"""Puerto para el repositorio de métricas."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


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
        file_id: str | None = None,
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
        stack_trace: str | None = None,
        session_id: str | None = None,
        endpoint: str | None = None
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
        end_date: datetime | None = None
    ) -> list[Any]:
        """Obtener métricas por rango de fechas."""
        pass

    @abstractmethod
    def get_daily_summaries(
        self,
        start_date: str,
        end_date: str | None = None
    ) -> list[Any]:
        """Obtener resúmenes diarios."""
        pass

    @abstractmethod
    def get_top_agents(
        self,
        start_date: datetime,
        limit: int = 5
    ) -> list[Any]:
        """Obtener agentes más usados."""
        pass

    @abstractmethod
    def get_recent_errors(self, limit: int = 10) -> list[Any]:
        """Obtener errores recientes."""
        pass

    @abstractmethod
    def update_daily_summary(self, date: str) -> None:
        """Actualizar resumen diario."""
        pass
