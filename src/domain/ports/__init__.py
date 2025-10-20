"""
Puertos (Interfaces) del dominio.

Este módulo define las interfaces que deben ser implementadas por los adaptadores.
Siguiendo el principio de Inversión de Dependencias (SOLID).
"""

from __future__ import annotations

from .llm_port import LLMPort
from .repository_port import ChatRepositoryPort
from .file_repository_port import FileRepositoryPort
from .embeddings_port import EmbeddingsPort
from .python_search_port import PythonSearchPort, PythonSource
from .guardian_port import GuardianPort, GuardianResult, ThreatLevel

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
