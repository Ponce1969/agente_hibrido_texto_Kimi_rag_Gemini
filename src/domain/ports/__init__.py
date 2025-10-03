"""
Puertos (Interfaces) del dominio.

Este módulo define las interfaces que deben ser implementadas por los adaptadores.
Siguiendo el principio de Inversión de Dependencias (SOLID).
"""

from __future__ import annotations

from .llm_port import LLMPort
from .repository_port import ChatRepositoryPort
from .embeddings_port import EmbeddingsPort

__all__ = [
    "LLMPort",
    "ChatRepositoryPort",
    "EmbeddingsPort",
]
