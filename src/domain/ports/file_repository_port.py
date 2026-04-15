"""
Puerto del dominio para el repositorio de archivos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models.file_models import FileDocument, FileSection, FileStatus


class FileRepositoryPort(ABC):
    """Interfaz para el repositorio de archivos."""

    @abstractmethod
    def create_file_record(
        self, filename: str, file_path: str, size_bytes: int
    ) -> FileDocument:
        """Crea un registro para un nuevo archivo subido."""
        ...

    @abstractmethod
    def add_sections_to_file(self, file_id: int, sections: list[dict]) -> None:
        """Añade registros de sección a un archivo."""
        ...

    @abstractmethod
    def get_file(self, file_id: int) -> FileDocument | None:
        """Obtiene un documento de archivo por su ID."""
        ...

    @abstractmethod
    def list_files(self, limit: int = 20) -> list[FileDocument]:
        """Lista los archivos subidos recientemente."""
        ...

    @abstractmethod
    def get_file_sections(self, file_id: int) -> list[FileSection]:
        """Obtiene las secciones de un archivo."""
        ...

    @abstractmethod
    def update_file_status(
        self, file_id: int, status: FileStatus, error_message: str | None = None
    ) -> None:
        """Actualiza el estado y otros metadatos de un archivo."""
        ...

    @abstractmethod
    def update_file_pages(
        self, file_id: int, total_pages: int, pages_processed: int
    ) -> None:
        """Actualiza el número de páginas de un archivo."""
        ...

    @abstractmethod
    def delete_file(self, file_id: int) -> bool:
        """Elimina un archivo y sus secciones asociadas."""
        ...
