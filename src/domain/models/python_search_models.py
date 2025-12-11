"""Modelos de dominio para búsqueda Python."""
from dataclasses import dataclass


@dataclass
class PythonSource:
    """Fuente de información Python con metadatos de confiabilidad."""

    url: str
    title: str
    snippet: str
    source_type: str  # github | official_docs | peps | blog_tecnico | qa
    reliability: int  # 1-10 (filtrado por el tool)
