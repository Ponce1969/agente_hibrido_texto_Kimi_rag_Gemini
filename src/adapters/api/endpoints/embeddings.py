"""
Endpoints para la gestión de embeddings, refactorizados para seguir la arquitectura hexagonal.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.adapters.dependencies import (
    get_embeddings_service_dependency,
    get_file_processing_service_dependency,
)
from src.application.services.embeddings_service import EmbeddingsServiceV2
from src.application.services.file_processing_service import FileProcessingService

logger = logging.getLogger(__name__)

# Configurar limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post(
    "/embeddings/index/{file_id}",
    tags=["Embeddings"],
    summary="Indexa el contenido de un archivo procesado"
)
@limiter.limit("5/minute")  # Límite: 5 requests por minuto (operación muy costosa)
async def embeddings_index(
    request: Request,
    file_id: int,
    service: FileProcessingService = Depends(get_file_processing_service_dependency),
):
    """Inicia el proceso de chunking, extracción de texto e indexación de un archivo."""
    try:
        inserted_chunks = await service.index_file(file_id)
        return {"status": "ok", "file_id": file_id, "inserted_chunks": inserted_chunks}
    except FileNotFoundError as e:
        logger.warning(f"Intento de indexar archivo no encontrado {file_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"Error de validación al indexar {file_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error crítico al indexar archivo {file_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al indexar el archivo: {e}")


@router.get(
    "/embeddings/search",
    tags=["Embeddings"],
    summary="Búsqueda por similitud en embeddings"
)
async def embeddings_search(
    q: str = Query(..., description="Consulta de texto"),
    file_id: int | None = Query(None),
    top_k: int = Query(10, ge=1, le=50),
    service: EmbeddingsServiceV2 = Depends(get_embeddings_service_dependency),
):
    """Realiza una búsqueda semántica en los chunks de un archivo o en todos."""
    try:
        results = await service.search_similar(
            query=q,
            file_id=str(file_id) if file_id else None,
            top_k=top_k
        )
        return {
            "query": q,
            "file_id": file_id,
            "top_k": top_k,
            "results": results,
        }
    except ValueError as e:
        logger.warning(f"Búsqueda inválida: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en búsqueda de embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al realizar la búsqueda")
