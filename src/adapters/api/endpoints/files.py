"""
Endpoints para extracción de texto de archivos (PDF y texto plano).
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from src.adapters.config.settings import settings
from src.adapters.db.database import get_session
from sqlmodel import Session, select
from pathvalidate import sanitize_filename
from uuid import uuid4
import os
from datetime import datetime
from src.adapters.db.file_models import FileUpload, FileSection, FileStatus
from src.adapters.db.database import engine
from sqlmodel import Session as SQLSession

router = APIRouter()


def _truncate_text(text: str) -> tuple[str, bool]:
    max_chars = settings.file_context_max_chars
    if len(text) > max_chars:
        return text[:max_chars], True
    return text, False


# ============ Flujo simple de extracción en una sola llamada ============
@router.post("/files/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """Extrae texto de un archivo subido. Soporta:
    - PDF (usa PyPDF si está disponible en el entorno)
    - Archivos de texto/markdown/código (mejor esfuerzo de decodificación)
    Devuelve JSON con el texto (truncado según configuración) y metadatos.
    """
    filename = file.filename or "uploaded"
    content = await file.read()

    # Decisión por extensión o content-type
    is_pdf = filename.lower().endswith(".pdf") or (file.content_type == "application/pdf")

    text = None
    processed_pages = None
    total_pages = None
    if is_pdf:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception as e:
            raise HTTPException(
                status_code=501,
                detail=(
                    "Soporte PDF no disponible en el entorno. Rebuild de la imagen requerido. "
                    f"Detalle: {e}"
                ),
            )
        try:
            import io

            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")  # mejor esfuerzo para PDFs sin password explícita
                except Exception:
                    raise HTTPException(status_code=400, detail="El PDF está cifrado y no pudo ser leído.")

            parts: list[str] = []
            max_pages = settings.file_max_pdf_pages
            total_pages = len(reader.pages)
            limit = total_pages if max_pages == 0 else min(total_pages, max_pages)
            for idx in range(limit):
                page = reader.pages[idx]
                extracted = None
                try:
                    extracted = page.extract_text()
                except Exception:
                    extracted = None
                parts.append(extracted or "")
            text = "\n".join(parts)
            processed_pages = limit
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo extraer texto del PDF: {e}")
    else:
        # Intentar varias codificaciones
        for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
            try:
                text = content.decode(enc)
                break
            except Exception:
                continue
        if text is None:
            # Último recurso
            text = content.decode("utf-8", errors="replace")

    text = text or ""
    truncated_text, truncated = _truncate_text(text)
    return {
        "filename": filename,
        "chars": len(truncated_text),
        "truncated": truncated,
        "processed_pages": processed_pages,
        "total_pages": total_pages,
        "text": truncated_text,
    }


# ============ Pipeline para PDFs grandes (upload + process + status + sections) ============

@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...), session: Session = Depends(get_session)):
    filename_original = sanitize_filename(file.filename or "uploaded.pdf")
    content_type = file.content_type or "application/octet-stream"
    is_pdf = filename_original.lower().endswith(".pdf") or (content_type == "application/pdf")
    if not is_pdf:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF en este endpoint.")

    # Validar tamaño (leer a memoria por simplicidad en Etapa 1)
    content = await file.read()
    size_bytes = len(content)
    max_bytes = settings.file_max_pdf_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(status_code=413, detail=f"Archivo demasiado grande. Máximo {settings.file_max_pdf_size_mb} MB")

    # Guardar archivo en disco con UUID
    uid = str(uuid4())
    filename_saved = f"{uid}.pdf"
    save_path = os.path.join("data", "files", filename_saved)
    with open(save_path, "wb") as f:
        f.write(content)

    # Registrar en BD
    fu = FileUpload(
        uuid_str=uid,
        filename_original=filename_original,
        filename_saved=filename_saved,
        path=save_path,
        size_bytes=size_bytes,
        total_pages=0,
        pages_processed=0,
        status=FileStatus.PENDING,
        error_message=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(fu)
    session.commit()
    session.refresh(fu)
    return {"file_id": fu.id, "filename": filename_original, "size_bytes": size_bytes}


def _process_pdf_into_sections(file_id: int):
    # Worker: abre sesión propia
    with SQLSession(engine) as session:
        fu = session.get(FileUpload, file_id)
        if not fu:
            return
        try:
            from pypdf import PdfReader  # type: ignore
            import io
            # Cargar PDF desde disco
            with open(fu.path, "rb") as f:
                raw = f.read()
            reader = PdfReader(io.BytesIO(raw))
            if getattr(reader, "is_encrypted", False):
                try:
                    reader.decrypt("")
                except Exception:
                    raise HTTPException(status_code=400, detail="El PDF está cifrado y no pudo ser leído.")

            total_pages = len(reader.pages)
            fu.total_pages = total_pages
            fu.status = FileStatus.PROCESSING
            fu.pages_processed = 0
            session.add(fu)
            session.commit()

            window = max(1, settings.file_chapter_max_pages)
            sections: list[FileSection] = []
            for start in range(0, total_pages, window):
                end = min(total_pages - 1, start + window - 1)
                # Medir char_count aproximado extrayendo texto de la ventana
                parts: list[str] = []
                for idx in range(start, end + 1):
                    try:
                        text = reader.pages[idx].extract_text() or ""
                    except Exception:
                        text = ""
                    parts.append(text)
                section_text = "\n".join(parts)
                char_count = len(section_text)
                sec = FileSection(
                    file_id=file_id,
                    title=None,
                    start_page=start,
                    end_page=end,
                    char_count=char_count,
                )
                session.add(sec)
                sections.append(sec)

                # Progreso (cada ventana)
                fu.pages_processed = min(total_pages, end + 1)
                fu.updated_at = datetime.utcnow()
                session.add(fu)
                session.commit()

            fu.status = FileStatus.READY
            fu.updated_at = datetime.utcnow()
            session.add(fu)
            session.commit()
        except Exception as e:
            fu.status = FileStatus.ERROR
            fu.error_message = str(e)
            fu.updated_at = datetime.utcnow()
            session.add(fu)
            session.commit()


@router.post("/files/process/{file_id}")
def start_processing(file_id: int, background: BackgroundTasks, session: Session = Depends(get_session)):
    fu = session.get(FileUpload, file_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    if fu.status == FileStatus.READY:
        return {"status": fu.status, "pages_processed": fu.pages_processed, "total_pages": fu.total_pages}
    if fu.status == FileStatus.PROCESSING:
        return {"status": fu.status, "pages_processed": fu.pages_processed, "total_pages": fu.total_pages}
    # pending o error → reintentar
    fu.status = FileStatus.PENDING
    fu.pages_processed = 0
    fu.updated_at = datetime.utcnow()
    session.add(fu)
    session.commit()
    background.add_task(_process_pdf_into_sections, file_id)
    return {"status": FileStatus.PROCESSING}


@router.get("/files/status/{file_id}")
def file_status(file_id: int, session: Session = Depends(get_session)):
    fu = session.get(FileUpload, file_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return {
        "status": fu.status,
        "pages_processed": fu.pages_processed,
        "total_pages": fu.total_pages,
        "error_message": fu.error_message,
    }


@router.get("/files/{file_id}/sections")
def list_sections(file_id: int, session: Session = Depends(get_session)):
    fu = session.get(FileUpload, file_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    if fu.status != FileStatus.READY:
        raise HTTPException(status_code=409, detail="El archivo aún no está listo")
    statement = select(FileSection).where(FileSection.file_id == file_id).order_by(FileSection.start_page)
    sections = session.exec(statement).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "start_page": s.start_page,
            "end_page": s.end_page,
            "char_count": s.char_count,
        }
        for s in sections
    ]


@router.get("/files/{file_id}/sections/{section_id}/text")
def get_section_text(file_id: int, section_id: int, session: Session = Depends(get_session)):
    fu = session.get(FileUpload, file_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    sec = session.get(FileSection, section_id)
    if not sec or sec.file_id != file_id:
        raise HTTPException(status_code=404, detail="Sección no encontrada")
    # Extraer texto on-demand para no ocupar DB con texto grande
    try:
        from pypdf import PdfReader  # type: ignore
        import io
        with open(fu.path, "rb") as f:
            raw = f.read()
        reader = PdfReader(io.BytesIO(raw))
        parts: list[str] = []
        for idx in range(sec.start_page, sec.end_page + 1):
            try:
                text = reader.pages[idx].extract_text() or ""
            except Exception:
                text = ""
            parts.append(text)
        text = "\n".join(parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo extraer texto de la sección: {e}")

    truncated_text, truncated = _truncate_text(text)
    return {
        "file_id": file_id,
        "section_id": section_id,
        "start_page": sec.start_page,
        "end_page": sec.end_page,
        "chars": len(truncated_text),
        "truncated": truncated,
        "text": truncated_text,
    }
