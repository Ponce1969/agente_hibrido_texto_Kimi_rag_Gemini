"""
Puertos (Interfaces) del dominio.

Este módulo define las interfaces que deben ser implementadas por los adaptadores.
Siguiendo el principio de Inversión de Dependencias (SOLID).
"""

from __future__ import annotations

from .embeddings_port import EmbeddingsPort
from .file_repository_port import FileRepositoryPort
from .guardian_port import GuardianPort, GuardianResult, ThreatLevel
from .llm_port import LLMPort
from .python_search_port import PythonSearchPort, PythonSource
from .repository_port import ChatRepositoryPort

__all__ = [
    "LLMPort",
    "ChatRepositoryPort",
    "EmbeddingsPort",
    "FileRepositoryPort",
    "PythonSearchPort",
    "PythonSource",
    "GuardianPort",
    "GuardianResult",
    "ThreatLevel",
]
