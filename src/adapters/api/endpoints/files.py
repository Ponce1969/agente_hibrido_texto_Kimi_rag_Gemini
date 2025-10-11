"""
Endpoints para la gestión de archivos, refactorizados para seguir la arquitectura hexagonal.
"""
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel

from src.application.services.file_processing_service import FileProcessingService
from src.adapters.dependencies import get_file_processing_service_dependency

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Schemas ---
class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    size_bytes: int

class FileStatusResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: str  # Requerido por Streamlit
    total_pages: int | None = None
    pages_processed: int | None = None
    error_message: str | None = None
    size_bytes: int | None = None
    mime_type: str | None = None

# --- Endpoints ---
@router.post("/files/upload", response_model=FileUploadResponse, tags=["Files"])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_index: bool = Query(False, description="Iniciar procesamiento e indexación automáticamente"),
    service: FileProcessingService = Depends(get_file_processing_service_dependency),
):
    try:
        file_doc = await service.upload_and_save_file(file)
        if auto_index:
            background_tasks.add_task(service.process_pdf_sections, int(file_doc.id))
            background_tasks.add_task(service.index_file, int(file_doc.id))
        return FileUploadResponse(
            file_id=int(file_doc.id),
            filename=file_doc.filename,
            size_bytes=file.size, # Aproximación, el tamaño real está en el servicio
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al subir archivo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al subir el archivo.")

@router.get("/files", response_model=List[FileStatusResponse], tags=["Files"])
def list_files(
    limit: int = Query(20, ge=1, le=200),
    service: FileProcessingService = Depends(get_file_processing_service_dependency),
):
    try:
        files = service.list_files(limit)

        result: List[FileStatusResponse] = []
        for f in files:
            # Asegurar tipos correctos
            fid = (
                int(f.id) if isinstance(f.id, str) and f.id.isdigit()
                else (f.id if isinstance(f.id, int) else int(str(f.id)))
            )
            status_str = f.status.value if hasattr(f.status, "value") else str(f.status)

            # Convertir created_at a string ISO (requerido)
            from datetime import datetime, UTC
            if f.created_at:
                created_at_str = f.created_at.isoformat() if hasattr(f.created_at, 'isoformat') else str(f.created_at)
            else:
                # Fallback si no hay created_at
                created_at_str = datetime.now(UTC).isoformat()
            
            result.append(
                FileStatusResponse(
                    id=fid,
                    filename=f.filename,
                    status=status_str,
                    created_at=created_at_str,
                    total_pages=f.total_pages,
                    pages_processed=f.pages_processed,
                    error_message=f.error_message,
                    size_bytes=f.size_bytes,
                    mime_type=None,  # No disponible en el modelo actual
                )
            )
        return result
    except Exception as e:
        logger.error(f"Error al listar archivos: {e}", exc_info=True)
        # Devolver detalle para diagnosticar rápidamente
        raise HTTPException(status_code=500, detail=f"Error al listar archivos: {type(e).__name__}: {e}")

@router.get("/files/status/{file_id}", response_model=FileStatusResponse, tags=["Files"])
def get_file_status(
    file_id: int,
    service: FileProcessingService = Depends(get_file_processing_service_dependency),
):
    file_doc = service.get_file_status(file_id)
    if not file_doc:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Construir respuesta manualmente (file_doc es dataclass, no tiene .dict())
    from datetime import datetime, UTC
    
    if file_doc.created_at:
        created_at_str = file_doc.created_at.isoformat() if hasattr(file_doc.created_at, 'isoformat') else str(file_doc.created_at)
    else:
        created_at_str = datetime.now(UTC).isoformat()
    
    status_str = file_doc.status.value if hasattr(file_doc.status, 'value') else str(file_doc.status)
    
    return FileStatusResponse(
        id=int(file_doc.id),
        filename=file_doc.filename,
        status=status_str,
        created_at=created_at_str,
        total_pages=file_doc.total_pages,
        pages_processed=file_doc.pages_processed,
        error_message=file_doc.error_message,
        size_bytes=file_doc.size_bytes,
        mime_type=None,
    )

@router.post("/files/process/{file_id}", status_code=202, tags=["Files"])
def trigger_processing(
    file_id: int,
    background_tasks: BackgroundTasks,
    service: FileProcessingService = Depends(get_file_processing_service_dependency),
):
    """Inicia el procesamiento de secciones de un archivo en segundo plano."""
    file_doc = service.get_file_status(file_id)
    if not file_doc:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    background_tasks.add_task(service.process_pdf_sections, file_id)
    return {"message": "Procesamiento iniciado"}
