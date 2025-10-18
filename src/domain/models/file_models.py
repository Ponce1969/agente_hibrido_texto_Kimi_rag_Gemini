"""
Modelos de dominio para archivos y documentos.

Tipado estricto para mypy --strict con Python 3.12+
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum


class FileStatus(str, Enum):
    """Estados posibles de un archivo."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    INDEXED = "indexed"
    ERROR = "error"


@dataclass
class FileDocument:
    """Representa un documento en el sistema."""
    
    id: str
    filename: str
    file_path: str
    status: FileStatus
    # Campos adicionales usados por endpoints/repositorios SQL
    total_pages: int | None = None
    pages_processed: int | None = None
    error_message: str | None = None
    size_bytes: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    
    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.filename.strip():
            raise ValueError("El nombre de archivo no puede estar vacío")
    
    def is_indexed(self) -> bool:
        """Verifica si el documento está indexado."""
        return self.status == FileStatus.INDEXED
    
    def is_processing(self) -> bool:
        """Verifica si el documento está en procesamiento."""
        return self.status == FileStatus.PROCESSING
    
    def has_error(self) -> bool:
        """Verifica si el documento tiene error."""
        return self.status == FileStatus.ERROR


@dataclass
class FileSection:
    """Representa una sección de un documento."""
    
    id: int
    file_id: str
    text: str
    page_number: int | None = None
    chunk_index: int = 0
    
    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        # Permitir texto vacío temporalmente (será filtrado en el procesamiento)
        # if not self.text.strip():
        #     raise ValueError("El texto no puede estar vacío")
        
        if self.chunk_index < 0:
            raise ValueError("El índice del chunk debe ser no negativo")
    
    def get_text_length(self) -> int:
        """Retorna la longitud del texto."""
        return len(self.text)
