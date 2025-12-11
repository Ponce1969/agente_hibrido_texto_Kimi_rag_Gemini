import os
import re
from collections.abc import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.adapters.config.settings import settings
from src.adapters.db.file_models import FileSection, FileUpload  # noqa: F401
from src.domain.models.user import User  # noqa: F401


def sanitize_db_url(url: str) -> str:
    """
    Oculta credenciales en URLs de base de datos para logs seguros.

    Ejemplo:
        postgresql://user:password@host:5432/db
        -> postgresql://user:***@host:5432/db
    """
    # Patrón para capturar: scheme://user:password@host:port/db
    pattern = r"(://[^:]+:)([^@]+)(@)"
    return re.sub(pattern, r"\1***\3", url)

# Importar modelos de embeddings solo si usamos PostgreSQL para RAG
# (Los embeddings van en PostgreSQL, no en SQLite)
try:
    from src.adapters.db.embeddings_models import (  # noqa: F401
        EmbeddingChunk,
        SimilarChunk,
    )
except ImportError:
    # Los modelos de embeddings pueden no estar disponibles
    pass

# Importar modelos de chat si existen
try:
    from src.adapters.db.chat_models import ChatMessage, ChatSession  # noqa: F401
except ImportError:
    # Si no existen modelos de chat específicos para DB, usar los de dominio
    pass

# Configuración de base de datos (SQLite o PostgreSQL)
if settings.db_backend == "postgresql" and settings.database_url_pg:
    # Configuración para PostgreSQL
    engine = create_engine(
        settings.effective_database_url,
        echo=False  # Cambiar a True para debugging
    )
else:
    # Configuración para SQLite con threading
    engine = create_engine(
        settings.effective_database_url,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False  # Cambiar a True para debugging
    )

def create_db_and_tables():
    """Crea las tablas de la base de datos si no existen"""
    # Asegurar directorios de datos
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/files", exist_ok=True)

    # Crear todas las tablas usando SQLModel
    SQLModel.metadata.create_all(engine)

    # Log seguro sin exponer credenciales
    safe_url = sanitize_db_url(settings.effective_database_url)
    print(f"✅ Tablas creadas/verificadas en: {safe_url}")

    # Ajustes específicos según el backend
    if settings.db_backend == "postgresql":
        # Ajustes para PostgreSQL
        try:
            with engine.begin() as conn:
                # Verificar que la extensión pgvector esté disponible
                conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✅ Extensión pgvector verificada")
        except Exception as e:
            print(f"⚠️ No se pudo verificar pgvector: {e}")
    else:
        # Ajustes para SQLite (desarrollo)
        try:
            with engine.begin() as conn:
                # Añadir columna extra_data a chat_sessions si no existe
                conn.exec_driver_sql(
                    """
                    ALTER TABLE chat_sessions ADD COLUMN extra_data TEXT
                    """
                )
        except Exception:
            # Es probable que la columna ya exista; ignorar en dev
            pass

        try:
            with engine.begin() as conn:
                # Añadir columna extra_data a chat_messages si no existe
                conn.exec_driver_sql(
                    """
                    ALTER TABLE chat_messages ADD COLUMN extra_data TEXT
                    """
                )
        except Exception:
            # Es probable que la columna ya exista; ignorar en dev
            pass

def get_session() -> Generator[Session, None, None]:
    """Dependency para obtener sesión de base de datos"""
    with Session(engine) as session:
        yield session
