"""
Puerto de dominio para el Guardian de seguridad.
Define la interfaz que debe implementar cualquier servicio de moderación.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ThreatLevel(str, Enum):
    """Nivel de amenaza detectado."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardianResult:
    """Resultado del análisis de seguridad."""
    is_safe: bool
    threat_level: ThreatLevel
    reason: str | None = None
    confidence: float = 0.0  # 0.0 a 1.0
    categories: list[str] | None = None  # ["injection", "prompt_leak", etc.]
    checked_at: datetime | None = None


class GuardianPort(ABC):
    """
    Puerto de dominio para servicios de moderación/seguridad.
    Permite cambiar la implementación sin afectar la lógica de negocio.
    """
    
    @abstractmethod
    async def check_message(self, text: str, user_id: str | None = None) -> GuardianResult:
        """
        Analiza un mensaje para detectar amenazas.
        
        Args:
            text: Mensaje a analizar
            user_id: ID del usuario (opcional, para tracking)
            
        Returns:
            GuardianResult con el análisis
        """
        pass
    
    @abstractmethod
    async def is_enabled(self) -> bool:
        """Verifica si el Guardian está activo."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> dict:
        """Obtiene estadísticas de uso del Guardian."""
        pass
