"""Puerto para el repositorio de métricas."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Any, Dict


class MetricsRepositoryPort(ABC):
    """Puerto para el repositorio de métricas."""
    
    @abstractmethod
    def create_and_save_metric(
        self,
        session_id: str,
        agent_mode: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost: float,
        response_time: float,
        model_name: str,
        has_rag_context: bool = False,
        rag_chunks_used: int = 0,
        file_id: Optional[str] = None,
        used_bear_search: bool = False,
        bear_sources_count: int = 0
    ) -> Any:
        """Crear y guardar una métrica."""
        pass
    
    @abstractmethod
    def save_metric(self, metric: Any) -> Any:
        """Guardar una métrica."""
        pass
    
    @abstractmethod
    def create_and_save_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        session_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Any:
        """Crear y guardar un error."""
        pass
    
    @abstractmethod
    def save_error(self, error: Any) -> Any:
        """Guardar un error."""
        pass
    
    @abstractmethod
    def get_metrics_by_date_range(
        self, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[Any]:
        """Obtener métricas por rango de fechas."""
        pass
    
    @abstractmethod
    def get_daily_summaries(
        self, 
        start_date: str, 
        end_date: Optional[str] = None
    ) -> List[Any]:
        """Obtener resúmenes diarios."""
        pass
    
    @abstractmethod
    def get_top_agents(
        self, 
        start_date: datetime, 
        limit: int = 5
    ) -> List[Any]:
        """Obtener agentes más usados."""
        pass
    
    @abstractmethod
    def get_recent_errors(self, limit: int = 10) -> List[Any]:
        """Obtener errores recientes."""
        pass
    
    @abstractmethod
    def update_daily_summary(self, date: str) -> None:
        """Actualizar resumen diario."""
        pass
