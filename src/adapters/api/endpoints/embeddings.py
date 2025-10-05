"""
Embeddings endpoints:
 - init: asegura tablas e índices (pgvector)
 - index: indexa un file_id previamente procesado en secciones (SQLite) y guarda embeddings en Postgres
 - search: búsqueda top-k por similitud (cosine) opcionalmente filtrada por file_id
"""
from fastapi import APIRouter, HTTPException, Query

from src.adapters.db.embeddings_repository import EmbeddingsRepository
from src.adapters.db.pg_engine import get_pg_engine
from src.adapters.dependencies import get_embeddings_service

router = APIRouter()


@router.get("/embeddings/health", tags=["Embeddings"], summary="Verifica el estado del sistema de embeddings")
def embeddings_health():
    """Verifica la conexión a PostgreSQL y el estado del sistema de embeddings."""
    engine = get_pg_engine()
    if engine is None:
        return {
            "configured": False,
            "message": "DATABASE_URL_PG no configurado",
            "embedding_model": "Gemini text-embedding-004",
            "embedding_dim": 768
        }
    
    try:
        repo = EmbeddingsRepository()
        # Verificar que podemos conectar y contar
        total_chunks = repo.count_chunks(None)  # Contar todos los chunks
        
        return {
            "configured": True,
            "connected": True,
            "embedding_model": "Gemini text-embedding-004",
            "embedding_dim": 768,
            "total_chunks_indexed": total_chunks,
            "message": "Sistema de embeddings funcionando correctamente"
        }
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "error": str(e),
            "message": f"Error en sistema de embeddings: {e}"
        }


@router.post("/embeddings/init", tags=["Embeddings"], summary="Crea tablas e índices de embeddings en PostgreSQL")
def embeddings_init():
    engine = get_pg_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="DATABASE_URL_PG no configurado")
    try:
        repo = EmbeddingsRepository()
        repo.ensure_schema()
        return {"status": "ok", "message": "Schema de embeddings asegurado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando esquema: {e}")


@router.post("/embeddings/index/{file_id}", tags=["Embeddings"], summary="Indexa (chunking + embeddings) un PDF ya procesado en secciones")
def embeddings_index(file_id: int):
    engine = get_pg_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="DATABASE_URL_PG no configurado")
    try:
        repo = EmbeddingsRepository()
        svc = EmbeddingsService(repo)
        inserted = svc.index_file(file_id)
        return {"status": "ok", "file_id": file_id, "inserted_chunks": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexando archivo: {e}")


@router.get("/embeddings/search", tags=["Embeddings"], summary="Búsqueda top-k por similitud en embeddings")
def embeddings_search(q: str = Query(..., description="Consulta de texto"), file_id: int | None = Query(None), top_k: int = Query(5, ge=1, le=50)):
    engine = get_pg_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="DATABASE_URL_PG no configurado")
    try:
        repo = EmbeddingsRepository()
        svc = EmbeddingsService(repo)
        results = svc.search(q, file_id=file_id, top_k=top_k)
        return {
            "query": q,
            "file_id": file_id,
            "top_k": top_k,
            "results": [
                {
                    "id": r.id,
                    "file_id": r.file_id,
                    "section_id": r.section_id,
                    "chunk_index": r.chunk_index,
                    "distance": r.distance,
                    "content": r.content,
                }
                for r in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {e}")
