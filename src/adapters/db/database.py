from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from src.adapters.config.settings import settings
from src.adapters.db.file_models import FileUpload, FileSection  # noqa: F401
import os

# Configuración para SQLite con threading
engine = create_engine(
    settings.database_url,
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
    SQLModel.metadata.create_all(engine)
    # Ajuste de esquema para entorno de desarrollo (SQLite):
    # Garantiza columnas nuevas tras refactors sin usar migraciones.
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

    # Crear tablas nuevas para manejo de archivos si no existen
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """
                CREATE TABLE IF NOT EXISTS file_uploads (
                    id INTEGER PRIMARY KEY,
                    uuid_str TEXT NOT NULL,
                    filename_original TEXT NOT NULL,
                    filename_saved TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    total_pages INTEGER DEFAULT 0,
                    pages_processed INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
            conn.exec_driver_sql(
                """
                CREATE TABLE IF NOT EXISTS file_sections (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER NOT NULL REFERENCES file_uploads(id),
                    title TEXT,
                    start_page INTEGER NOT NULL,
                    end_page INTEGER NOT NULL,
                    char_count INTEGER DEFAULT 0
                )
                """
            )
    except Exception:
        pass

def get_session() -> Generator[Session, None, None]:
    """Dependency para obtener sesión de base de datos"""
    with Session(engine) as session:
        yield session