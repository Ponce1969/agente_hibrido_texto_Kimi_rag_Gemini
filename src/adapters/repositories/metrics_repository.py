"""Implementación del repositorio de métricas con SQLModel."""
from datetime import datetime, UTC
from typing import List, Optional, Any
from sqlmodel import Session, select, func
import json

from src.domain.ports.metrics_port import MetricsRepositoryPort
from src.adapters.db.metrics_models import AgentMetrics, DailyMetricsSummary, ErrorLog
from src.adapters.db.database import engine


class SQLModelMetricsRepository(MetricsRepositoryPort):
    """Implementación de MetricsRepositoryPort con SQLModel."""
    
    def __init__(self):
        """Inicializar repositorio."""
        self._ensure_data_directory()
        self._ensure_tables()
    
    def _ensure_data_directory(self):
        """Asegurar que el directorio data/ exists."""
        import os
        os.makedirs("data", exist_ok=True)
    
    def _ensure_tables(self):
        """Crear tablas si no existen."""
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
    
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
    ) -> AgentMetrics:
        """Crear y guardar una métrica."""
        metric = AgentMetrics(
            session_id=session_id,
            agent_mode=agent_mode,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            response_time=response_time,
            has_rag_context=has_rag_context,
            rag_chunks_used=rag_chunks_used,
            file_id=file_id,
            used_bear_search=used_bear_search,
            bear_sources_count=bear_sources_count,
            model_name=model_name
        )
        return self.save_metric(metric)
    
    def save_metric(self, metric: AgentMetrics) -> AgentMetrics:
        """Guardar una métrica."""
        with Session(engine) as session:
            session.add(metric)
            session.commit()
            session.refresh(metric)
        return metric
    
    def create_and_save_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        session_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> ErrorLog:
        """Crear y guardar un error."""
        error_log = ErrorLog(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            session_id=session_id,
            endpoint=endpoint
        )
        return self.save_error(error_log)
    
    def save_error(self, error: ErrorLog) -> ErrorLog:
        """Guardar un error."""
        with Session(engine) as session:
            session.add(error)
            session.commit()
            session.refresh(error)
        return error
    
    def get_metrics_by_date_range(
        self, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[AgentMetrics]:
        """Obtener métricas por rango de fechas."""
        with Session(engine) as session:
            statement = select(AgentMetrics).where(
                AgentMetrics.created_at >= start_date
            )
            if end_date:
                statement = statement.where(AgentMetrics.created_at <= end_date)
            
            return list(session.exec(statement).all())
    
    def get_daily_summaries(
        self, 
        start_date: str, 
        end_date: Optional[str] = None
    ) -> List[DailyMetricsSummary]:
        """Obtener resúmenes diarios."""
        with Session(engine) as session:
            statement = select(DailyMetricsSummary).where(
                DailyMetricsSummary.date >= start_date
            )
            if end_date:
                statement = statement.where(DailyMetricsSummary.date <= end_date)
            
            statement = statement.order_by(DailyMetricsSummary.date)
            return list(session.exec(statement).all())
    
    def get_top_agents(
        self, 
        start_date: datetime, 
        limit: int = 5
    ) -> List[Any]:
        """Obtener agentes más usados."""
        with Session(engine) as session:
            statement = (
                select(
                    AgentMetrics.agent_mode,
                    func.count(AgentMetrics.id).label("usage_count"),
                    func.sum(AgentMetrics.total_tokens).label("total_tokens"),
                    func.avg(AgentMetrics.response_time).label("avg_response_time")
                )
                .where(AgentMetrics.created_at >= start_date)
                .group_by(AgentMetrics.agent_mode)
                .order_by(func.count(AgentMetrics.id).desc())
                .limit(limit)
            )
            
            return list(session.exec(statement).all())
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorLog]:
        """Obtener errores recientes."""
        with Session(engine) as session:
            statement = (
                select(ErrorLog)
                .order_by(ErrorLog.created_at.desc())
                .limit(limit)
            )
            
            return list(session.exec(statement).all())
    
    def update_daily_summary(self, date: str) -> None:
        """Actualizar resumen diario."""
        with Session(engine) as session:
            # Obtener métricas del día
            statement = select(AgentMetrics).where(
                func.date(AgentMetrics.created_at) == date
            )
            metrics = session.exec(statement).all()
            
            if not metrics:
                return
            
            # Calcular agregados
            total_requests = len(metrics)
            unique_sessions = len(set(m.session_id for m in metrics))
            total_prompt_tokens = sum(m.prompt_tokens for m in metrics)
            total_completion_tokens = sum(m.completion_tokens for m in metrics)
            total_tokens = sum(m.total_tokens for m in metrics)
            total_cost = sum(m.estimated_cost for m in metrics)
            avg_response_time = sum(m.response_time for m in metrics) / total_requests
            rag_requests = sum(1 for m in metrics if m.has_rag_context)
            bear_requests = sum(1 for m in metrics if m.used_bear_search)
            
            # Uso por agente
            agent_usage = {}
            for m in metrics:
                agent_usage[m.agent_mode] = agent_usage.get(m.agent_mode, 0) + 1
            
            # Buscar si ya existe resumen
            existing = session.exec(
                select(DailyMetricsSummary).where(DailyMetricsSummary.date == date)
            ).first()
            
            if existing:
                # Actualizar
                existing.total_requests = total_requests
                existing.total_sessions = unique_sessions
                existing.total_prompt_tokens = total_prompt_tokens
                existing.total_completion_tokens = total_completion_tokens
                existing.total_tokens = total_tokens
                existing.total_cost = total_cost
                existing.avg_response_time = avg_response_time
                existing.rag_requests = rag_requests
                existing.bear_requests = bear_requests
                existing.agent_usage = json.dumps(agent_usage)
                existing.updated_at = datetime.now(UTC)
            else:
                # Crear nuevo
                summary = DailyMetricsSummary(
                    date=date,
                    total_requests=total_requests,
                    total_sessions=unique_sessions,
                    total_prompt_tokens=total_prompt_tokens,
                    total_completion_tokens=total_completion_tokens,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    avg_response_time=avg_response_time,
                    rag_requests=rag_requests,
                    bear_requests=bear_requests,
                    agent_usage=json.dumps(agent_usage)
                )
                session.add(summary)
            
            session.commit()
