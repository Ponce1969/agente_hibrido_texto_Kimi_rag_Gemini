"""Servicio para registrar y consultar métricas de agentes."""
from datetime import UTC, datetime, timedelta
from typing import Any

from src.domain.ports.metrics_port import MetricsRepositoryPort


class MetricsService:
    """Servicio para gestión de métricas."""

    def __init__(self, repository: MetricsRepositoryPort):
        """
        Inicializar servicio de métricas.

        Args:
            repository: Implementación del repositorio de métricas
        """
        self.repository = repository

    def record_agent_usage(
        self,
        session_id: str,
        agent_mode: str,
        prompt_tokens: int,
        completion_tokens: int,
        response_time: float,
        model_name: str,
        has_rag_context: bool = False,
        rag_chunks_used: int = 0,
        file_id: str | None = None,
        used_bear_search: bool = False,
        bear_sources_count: int = 0
    ) -> Any:
        """
        Registrar uso de un agente.

        Args:
            session_id: ID de la sesión
            agent_mode: Modo del agente usado
            prompt_tokens: Tokens del prompt
            completion_tokens: Tokens de la respuesta
            response_time: Tiempo de respuesta en segundos
            model_name: Nombre del modelo usado
            has_rag_context: Si usó contexto RAG
            rag_chunks_used: Cantidad de chunks RAG usados
            file_id: ID del archivo usado (si aplica)
            used_bear_search: Si usó Bear API
            bear_sources_count: Cantidad de fuentes Bear consultadas

        Returns:
            Registro de métricas creado
        """
        total_tokens = prompt_tokens + completion_tokens

        # Calcular costo estimado (precios aproximados)
        # Kimi: $0.0003 / 1K tokens
        # Gemini: $0.00015 / 1K tokens (input), $0.0006 / 1K tokens (output)
        if "kimi" in model_name.lower():
            estimated_cost = (total_tokens / 1000) * 0.0003
        elif "gemini" in model_name.lower():
            estimated_cost = (
                (prompt_tokens / 1000) * 0.00015 +
                (completion_tokens / 1000) * 0.0006
            )
        else:
            estimated_cost = (total_tokens / 1000) * 0.0005  # Default

        saved_metric = self.repository.create_and_save_metric(
            session_id=session_id,
            agent_mode=agent_mode,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            response_time=response_time,
            model_name=model_name,
            has_rag_context=has_rag_context,
            rag_chunks_used=rag_chunks_used,
            file_id=file_id,
            used_bear_search=used_bear_search,
            bear_sources_count=bear_sources_count
        )

        # Actualizar resumen diario
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        self.repository.update_daily_summary(today)

        return saved_metric

    def record_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str | None = None,
        session_id: str | None = None,
        endpoint: str | None = None
    ) -> Any:
        """Registrar un error del sistema."""
        return self.repository.create_and_save_error(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            session_id=session_id,
            endpoint=endpoint
        )

    def get_metrics_summary(self, days: int = 7) -> dict:
        """
        Obtener resumen de métricas de los últimos N días.

        Args:
            days: Cantidad de días a consultar

        Returns:
            Dict con resumen de métricas
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        metrics = self.repository.get_metrics_by_date_range(cutoff_date)

        if not metrics:
            return self._empty_summary()

        # Calcular agregados
        total_requests = len(metrics)
        total_tokens = sum(m.total_tokens for m in metrics)
        total_cost = sum(m.estimated_cost for m in metrics)
        avg_response_time = sum(m.response_time for m in metrics) / total_requests

        # Por agente
        agent_usage = {}
        for m in metrics:
            agent_usage[m.agent_mode] = agent_usage.get(m.agent_mode, 0) + 1

        # Por modelo
        model_usage = {}
        for m in metrics:
            model_usage[m.model_name] = model_usage.get(m.model_name, 0) + 1

        # Features
        rag_usage = sum(1 for m in metrics if m.has_rag_context)
        bear_usage = sum(1 for m in metrics if m.used_bear_search)

        # Sesiones únicas
        unique_sessions = len({m.session_id for m in metrics})

        return {
            "period_days": days,
            "total_requests": total_requests,
            "unique_sessions": unique_sessions,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_response_time_seconds": round(avg_response_time, 2),
            "agent_usage": agent_usage,
            "model_usage": model_usage,
            "rag_requests": rag_usage,
            "rag_percentage": round((rag_usage / total_requests) * 100, 1),
            "bear_requests": bear_usage,
            "bear_percentage": round((bear_usage / total_requests) * 100, 1),
        }

    def get_daily_metrics(self, days: int = 30) -> list[dict]:
        """Obtener métricas diarias para gráficos."""
        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
        summaries = self.repository.get_daily_summaries(cutoff_date)

        return [
            {
                "date": s.date,
                "requests": s.total_requests,
                "tokens": s.total_tokens,
                "cost": s.total_cost,
                "avg_response_time": s.avg_response_time,
                "rag_requests": s.rag_requests,
                "bear_requests": s.bear_requests
            }
            for s in summaries
        ]

    def get_top_agents(self, days: int = 7, limit: int = 5) -> list[dict]:
        """Obtener agentes más usados."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        results = self.repository.get_top_agents(cutoff_date, limit)

        return [
            {
                "agent": r[0],
                "usage_count": r[1],
                "total_tokens": r[2],
                "avg_response_time": round(r[3], 2)
            }
            for r in results
        ]

    def get_recent_errors(self, limit: int = 10) -> list[dict]:
        """Obtener errores recientes."""
        errors = self.repository.get_recent_errors(limit)

        return [
            {
                "id": e.id,
                "type": e.error_type,
                "message": e.error_message,
                "endpoint": e.endpoint,
                "created_at": e.created_at.isoformat()
            }
            for e in errors
        ]

    def _empty_summary(self) -> dict:
        """Retornar resumen vacío."""
        return {
            "period_days": 0,
            "total_requests": 0,
            "unique_sessions": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_response_time_seconds": 0.0,
            "agent_usage": {},
            "model_usage": {},
            "rag_requests": 0,
            "rag_percentage": 0.0,
            "bear_requests": 0,
            "bear_percentage": 0.0,
        }
