from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from src.adapters.config.settings import settings
from src.adapters.db.file_models import FileUpload, FileSection  # noqa: F401
import os

# Importar modelos de embeddings solo si usamos PostgreSQL para RAG
# (Los embeddings van en PostgreSQL, no en SQLite)
try:
    from src.adapters.db.embeddings_models import EmbeddingChunk, SimilarChunk  # noqa: F401
except ImportError:
    # Los modelos de embeddings pueden no estar disponibles
    pass

# Importar modelos de chat si existen
try:
    from src.adapters.db.chat_models import ChatSession, ChatMessage  # noqa: F401
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
    
    print(f"✅ Tablas creadas/verificadas en: {settings.effective_database_url}")
    
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