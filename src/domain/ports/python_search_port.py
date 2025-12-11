"""Puerto para búsqueda especializada en fuentes Python confiables."""
from abc import ABC, abstractmethod

from ..models.python_search_models import PythonSource


class PythonSearchPort(ABC):
    """Puerto para búsqueda inteligente en fuentes Python confiables."""

    @abstractmethod
    async def search_python_bug(self, error_message: str) -> list[PythonSource]:
        """Busca soluciones a errores específicos en fuentes Python confiables."""
        pass

    @abstractmethod
    async def search_python_api(self, module: str, attribute: str) -> list[PythonSource]:
        """Busca ejemplos de uso de APIs específicas."""
        pass

    @abstractmethod
    async def search_python_best_practice(self, topic: str) -> list[PythonSource]:
        """Busca best-practices / PEPs / guías oficiales."""
        pass
