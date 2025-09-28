"""
Endpoints de verificación para PostgreSQL + pgvector (opcional).
Solo operan si `DATABASE_URL_PG` está configurado en el .env.
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from src.adapters.db.pg_engine import get_pg_engine

router = APIRouter()


@router.get("/pg/health", tags=["PostgreSQL"], summary="Verifica conexión a PostgreSQL y la extensión pgvector")
def pg_health():
    engine = get_pg_engine()
    if engine is None:
        # No configurado
        return {
            "configured": False,
            "message": "DATABASE_URL_PG no configurado. El sistema sigue operando con SQLite para historial.",
        }
    try:
        with engine.connect() as conn:
            # Consulta simple
            conn.execute(text("SELECT 1"))
            # Verificar extensión vector
            res = conn.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'"))
            has_vector = res.first() is not None
        return {
            "configured": True,
            "connected": True,
            "pgvector_installed": has_vector,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a PostgreSQL: {e}")
