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
    """
    file_id: int
    section_id: Optional[int]
    chunk_index: int
    content: str
    embedding: Sequence[float]  # Length must match the chosen model (e.g., 768)
    created_at: datetime | None = None


@dataclass(frozen=True)
class SimilarChunk:
    id: int
    file_id: int
    section_id: Optional[int]
    chunk_index: int
    content: str
    distance: float
