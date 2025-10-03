"""
Endpoints para extracción de texto de archivos (PDF y texto plano).
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Query
from src.adapters.config.settings import settings
from src.adapters.db.database import get_session
from sqlmodel import Session, select
from pathvalidate import sanitize_filename
from uuid import uuid4
import os
from datetime import datetime, UTC
from src.adapters.db.file_models import FileUpload, FileSection, FileStatus
from src.adapters.db.database import engine
from sqlmodel import Session as SQLSession
from src.application.services.embeddings_service import EmbeddingsService
from src.adapters.db.embeddings_repository import EmbeddingsRepository
from src.adapters.db.pg_engine import get_pg_engine

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


@router.get("/files")
def list_files(limit: int = Query(20, ge=1, le=200), session: Session = Depends(get_session)):
    """Lista los últimos archivos subidos, más recientes primero."""
    stmt = select(FileUpload).order_by(FileUpload.created_at.desc()).limit(limit)
    items = session.exec(stmt).all()
    out = []
    for f in items:
        out.append(
            {
                "id": f.id,
                "filename": f.filename_original,
                "status": f.status,
                "pages_processed": f.pages_processed,
                "total_pages": f.total_pages,
                "size_bytes": f.size_bytes,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
        )
    return out


# ============ Pipeline para PDFs grandes (upload + process + status + sections) ============

@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    background: BackgroundTasks = None,
    auto_index: bool = Query(False, description="Si es true, procesa e indexa automáticamente en background"),
):
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
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(fu)
    session.commit()
    session.refresh(fu)
    # Disparar pipeline completo si se solicita
    if auto_index and background is not None:
        background.add_task(_process_and_index, fu.id)
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
                fu.updated_at = datetime.now(UTC)
                session.add(fu)
                session.commit()

            fu.status = FileStatus.READY
            fu.updated_at = datetime.now(UTC)
            session.add(fu)
            session.commit()
        except Exception as e:
            fu.status = FileStatus.ERROR
            fu.error_message = str(e)
            fu.updated_at = datetime.now(UTC)
            session.add(fu)
            session.commit()


def _process_and_index(file_id: int):
    """Orquestador: procesa el PDF en secciones y luego indexa embeddings en pgvector.
    Idempotente: si ya existen embeddings para el file_id, no reindexa.
    """
    # Primero, crear secciones (actualiza FileUpload.status y páginas procesadas)
    _process_pdf_into_sections(file_id)

    # Luego, indexar si el archivo quedó READY
    with SQLSession(engine) as session:
        fu = session.get(FileUpload, file_id)
        if not fu or fu.status != FileStatus.READY:
            return
    try:
        repo = EmbeddingsRepository()
        repo.ensure_schema()
        # Evitar reindexación si ya existe
        if repo.count_chunks(file_id) > 0:
            return
        svc = EmbeddingsService(repo)
        svc.index_file(file_id)
    except Exception as e:
        # Registrar el error en FileUpload.error_message para visibilidad
        with SQLSession(engine) as session:
            fu2 = session.get(FileUpload, file_id)
            if fu2:
                fu2.error_message = f"index_error: {e}"
                fu2.updated_at = datetime.now(UTC)
                session.add(fu2)
                session.commit()


def _index_embeddings_bg(file_id: int):
    """Solo ejecuta indexación de embeddings en background para un file_id ya READY.
    Idempotente: si ya existen chunks, no hace nada.
    """
    try:
        repo = EmbeddingsRepository()
        repo.ensure_schema()
        if repo.count_chunks(file_id) > 0:
            return
        svc = EmbeddingsService(repo)
        svc.index_file(file_id)
    except Exception as e:
        # Registrar el error para visibilidad
        with SQLSession(engine) as session:
            fu2 = session.get(FileUpload, file_id)
            if fu2:
                fu2.error_message = f"bg_index_error: {e}"
                fu2.updated_at = datetime.now(UTC)
                session.add(fu2)
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
    fu.updated_at = datetime.now(UTC)
    session.add(fu)
    session.commit()
    background.add_task(_process_pdf_into_sections, file_id)
    return {"status": FileStatus.PROCESSING}


@router.post("/files/index/{file_id}")
def trigger_index(file_id: int, background: BackgroundTasks, session: Session = Depends(get_session)):
    """Dispara la indexación de embeddings en background para un PDF ya procesado.
    Responde inmediatamente para no bloquear la UI.
    """
    fu = session.get(FileUpload, file_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    if fu.status != FileStatus.READY:
        # Si aún no está listo, primero hay que procesar secciones
        raise HTTPException(status_code=409, detail="El archivo aún no está listo para indexación")
    # Validar PG antes de aceptar el trigger para evitar falso 'OK'
    if get_pg_engine() is None:
        raise HTTPException(status_code=400, detail="DATABASE_URL_PG no configurado para embeddings")
    try:
        repo = EmbeddingsRepository()
        if repo.count_chunks(file_id) > 0:
            return {"status": "ok", "message": "Ya indexado"}
    except Exception:
        pass
    background.add_task(_index_embeddings_bg, file_id)
    return {"status": "accepted", "message": "Indexación iniciada"}


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


@router.get("/files/progress/{file_id}")
def file_progress(file_id: int, session: Session = Depends(get_session)):
    """Devuelve un estado unificado del pipeline (secciones + índice)."""
    fu = session.get(FileUpload, file_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    phase = "uploaded"
    detail = None
    try:
        repo = EmbeddingsRepository()
        chunks = repo.count_chunks(file_id)
    except Exception:
        chunks = 0
    if fu.status in (FileStatus.PENDING, FileStatus.PROCESSING):
        phase = "processing_sections"
    elif fu.status == FileStatus.READY:
        # Si hay mensaje de error reciente y no hay chunks, reportar error
        if fu.error_message and (chunks == 0):
            phase = "error"
            detail = {"error": fu.error_message}
        else:
            # Si no hay embeddings aún, asumimos que está indexando o pendiente de indexar
            phase = "ready" if chunks > 0 else "indexing_embeddings"
            detail = {"chunks_indexed": chunks}
    elif fu.status == FileStatus.ERROR:
        phase = "error"
        detail = {"error": fu.error_message}
    return {
        "phase": phase,
        "status": fu.status,
        "pages_processed": fu.pages_processed,
        "total_pages": fu.total_pages,
        "detail": detail,
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
