import logging
import os
from collections.abc import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.adapters.config.settings import settings

logger = logging.getLogger(__name__)


def sanitize_db_url(url: str) -> str:
    """Oculta credenciales en URLs de base de datos para logs seguros."""
    if "postgresql" in url.lower():
        return "PostgreSQL (pgvector)"
    elif "sqlite" in url.lower():
        return "SQLite (desarrollo)"
    else:
        return "Base de datos configurada"


# Importar modelos para que SQLModel.metadata los conozca
from src.adapters.db.file_models import FileSection, FileUpload  # noqa: F401
from src.domain.models.user import User  # noqa: F401

try:
    from src.adapters.db.embeddings_models import (  # noqa: F401
        EmbeddingChunk,
        SimilarChunk,
    )
except ImportError:
    pass

try:
    from src.adapters.db.chat import ChatSession  # noqa: F401
    from src.adapters.db.message import ChatMessage  # noqa: F401
except ImportError:
    pass

# Configuración de base de datos
if settings.db_backend == "postgresql" and settings.database_url_pg:
    engine = create_engine(
        settings.effective_database_url,
        echo=False,
    )
else:
    engine = create_engine(
        settings.effective_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )


def run_alembic_migrations() -> None:
    """Ejecuta las migraciones de Alembic pendientes.

    Se usa en vez de create_all() para manejar schema evolution de forma segura.
    En desarrollo sin DB, crea las tablas con create_all() como fallback.
    """
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", "alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.effective_database_url)
        command.upgrade(alembic_cfg, "head")
        logger.info("Migraciones de Alembic ejecutadas correctamente")
    except Exception as e:
        logger.warning(f"No se pudieron ejecutar migraciones Alembic: {e}")
        logger.info("Fallback: creando tablas con SQLModel.metadata.create_all()")
        _create_tables_fallback()


def _create_tables_fallback() -> None:
    """Crea tablas usando create_all() como fallback cuando Alembic no está disponible."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/files", exist_ok=True)
    SQLModel.metadata.create_all(engine)
    safe_url = sanitize_db_url(settings.effective_database_url)
    logger.info(f"Tablas creadas/verificadas en: {safe_url}")


def create_db_and_tables():
    """Inicializa la base de datos. Usa Alembic si está disponible, fallback a create_all."""
    run_alembic_migrations()


def get_session() -> Generator[Session, None, None]:
    """Dependency para obtener sesión de base de datos."""
    with Session(engine) as session:
        yield session
