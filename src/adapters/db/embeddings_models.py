"""
Data models for embeddings storage in PostgreSQL (pgvector).
These are lightweight container types used by the repository and services.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence


@dataclass(frozen=True)
class EmbeddingChunk:
    """A single chunk of document text with its vector embedding.

    Note: Foreign keys to SQLite entities (file_id, section_id) are logical only.
    
    Metadatos agregados para mejor filtrado:
    - page_number: Número de página del chunk
    - section_type: Tipo de sección (chapter, introduction, etc.)
    - file_name: Nombre original del archivo
    """
    file_id: int
    section_id: Optional[int]
    chunk_index: int
    content: str
    embedding: Sequence[float]  # Length must match the chosen model (e.g., 768)
    created_at: datetime | None = None
    # Metadatos para mejor filtrado
    page_number: Optional[int] = None
    section_type: Optional[str] = None
    file_name: Optional[str] = None


@dataclass(frozen=True)
class SimilarChunk:
    """Resultado de búsqueda de similitud con metadatos."""
    id: int
    file_id: int
    section_id: Optional[int]
    chunk_index: int
    content: str
    distance: float
    # Metadatos para contexto adicional
    page_number: Optional[int] = None
    section_type: Optional[str] = None
    file_name: Optional[str] = None
