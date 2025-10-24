"""
Puerto del dominio para el repositorio de archivos.
"""
from __future__ import annotations

from typing import Protocol, Optional

from src.domain.models.file_models import FileDocument, FileSection, FileStatus


class FileRepositoryPort(Protocol):
    """Interfaz para el repositorio de archivos."""

    def create_file_record(self, filename: str, file_path: str, size_bytes: int) -> FileDocument:
        """Crea un registro para un nuevo archivo subido."""
        ...

    def add_sections_to_file(self, file_id: int, sections: list[dict]) -> None:
        """Añade registros de sección a un archivo."""
        ...

    def get_file(self, file_id: int) -> Optional[FileDocument]:
        """Obtiene un documento de archivo por su ID."""
        ...
    
    def list_files(self, limit: int = 20) -> list[FileDocument]:
        """Lista los archivos subidos recientemente."""
        ...

    def get_file_sections(self, file_id: int) -> list[FileSection]:
        """Obtiene las secciones de un archivo."""
        ...

    def update_file_status(self, file_id: int, status: FileStatus, error_message: Optional[str] = None) -> None:
        """Actualiza el estado y otros metadatos de un archivo."""
        ...
    
    def update_file_pages(self, file_id: int, total_pages: int, pages_processed: int) -> None:
        """Actualiza el número de páginas de un archivo."""
        ...
    
    def delete_file(self, file_id: int) -> bool:
        """Elimina un archivo y sus secciones asociadas."""
        ...
