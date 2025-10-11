"""
Modelos para el sistema de archivos en Streamlit.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class FileStatus(Enum):
    """Estados de procesamiento de archivos."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class ProcessingPhase(Enum):
    """Fases del procesamiento de archivos."""
    UPLOADED = "uploaded"
    PROCESSING_SECTIONS = "processing_sections"
    INDEXING_EMBEDDINGS = "indexing_embeddings"
    READY = "ready"
    ERROR = "error"


@dataclass
class FileUploadInfo:
    """Información de un archivo subido."""
    id: int
    filename: str
    status: str
    created_at: str
    pages_processed: Optional[int] = None
    total_pages: Optional[int] = None
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class FileProgress:
    """Progreso del procesamiento de un archivo."""
    phase: ProcessingPhase
    status: FileStatus
    pages_processed: int
    total_pages: int
    detail: Optional[Dict[str, Any]] = None


@dataclass
class FileSection:
    """Sección de un archivo procesado."""
    id: int
    file_id: int
    title: str
    start_page: int
    end_page: int
    content_preview: Optional[str] = None


@dataclass
class EmbeddingSearchResult:
    """Resultado de búsqueda en embeddings."""
    id: int
    file_id: int
    section_id: int
    chunk_index: int
    distance: float
    content: str
