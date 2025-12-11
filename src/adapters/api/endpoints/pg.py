"""
Endpoints de verificación para PostgreSQL + pgvector (opcional).
Solo operan si `DATABASE_URL_PG` está configurado en el .env.
"""
from fastapi import APIRouter
from sqlalchemy import text

from src.adapters.db.database import sanitize_db_url
from src.adapters.db.pg_engine import get_pg_engine

router = APIRouter()


@router.get("/pg/health", tags=["PostgreSQL"], summary="Verifica conexión a PostgreSQL y la extensión pgvector")
def pg_health():
    from src.adapters.config.settings import settings

    engine = get_pg_engine()
    if engine is None:
        # No configurado
        return {
            "configured": False,
            "database_url_pg": None,  # No exponer URL si no está configurado
            "message": "DATABASE_URL_PG no configurado. El sistema sigue operando con SQLite para historial.",
        }
    try:
        with engine.connect() as conn:
            # Consulta simple
            conn.execute(text("SELECT 1"))
            # Verificar extensión vector
            res = conn.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'"))
            has_vector = res.fetchone() is not None

            # Información adicional para debugging
            version_res = conn.execute(text("SELECT version()"))
            version_row = version_res.fetchone()
            pg_version = version_row[0] if version_row else "Unknown"

        # Sanitizar URL antes de exponerla
        safe_url = sanitize_db_url(settings.database_url_pg) if settings.database_url_pg else None

        return {
            "configured": True,
            "connected": True,
            "pgvector_installed": has_vector,
            "postgresql_version": pg_version,
            "database_url_pg": safe_url,  # URL sanitizada
            "embedding_dim": 384,  # Current setting
            "message": "PostgreSQL conectado correctamente" if has_vector else "PostgreSQL conectado pero pgvector no instalado"
        }
    except Exception as e:
        # Sanitizar URL antes de exponerla
        safe_url = sanitize_db_url(settings.database_url_pg) if settings.database_url_pg else None

        return {
            "configured": True,
            "connected": False,
            "error": str(e),
            "database_url_pg": safe_url,  # URL sanitizada
            "message": f"Error conectando a PostgreSQL: {e}. Verifica que el servicio esté ejecutándose."
        }
