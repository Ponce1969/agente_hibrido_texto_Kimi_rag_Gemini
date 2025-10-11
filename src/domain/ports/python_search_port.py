"""Puerto para búsqueda especializada en fuentes Python confiables."""
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class PythonSource:
    """Fuente de información Python con metadatos de confiabilidad."""
    
    url: str
    title: str
    snippet: str
    source_type: str  # github | official_docs | peps | blog_tecnico | qa
    reliability: int  # 1-10 (filtrado por el tool)


class PythonSearchPort(ABC):
    """Puerto para búsqueda inteligente en fuentes Python confiables."""

    @abstractmethod
    async def search_python_bug(self, error_message: str) -> List[PythonSource]:
        """Busca soluciones a errores específicos en fuentes Python confiables."""
        pass

    @abstractmethod
    async def search_python_api(self, module: str, attribute: str) -> List[PythonSource]:
        """Busca ejemplos de uso de APIs específicas."""
        pass

    @abstractmethod
    async def search_python_best_practice(self, topic: str) -> List[PythonSource]:
        """Busca best-practices / PEPs / guías oficiales."""
        pass
