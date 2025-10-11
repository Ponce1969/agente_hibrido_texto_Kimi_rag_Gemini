"""Servicio para registrar y consultar métricas de agentes."""
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Optional
from sqlmodel import Session, select, func
from src.adapters.db.metrics_models import AgentMetrics, DailyMetricsSummary, ErrorLog
from src.adapters.db.database import engine
import json


class MetricsService:
    """Servicio para gestión de métricas."""
    
    def __init__(self):
        """Inicializar servicio de métricas."""
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Crear tablas si no existen."""
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
    
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
        file_id: Optional[str] = None,
        used_bear_search: bool = False,
        bear_sources_count: int = 0
    ) -> AgentMetrics:
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
            AgentMetrics: Registro de métricas creado
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
        
        with Session(engine) as session:
            session.add(metric)
            session.commit()
            session.refresh(metric)
        
        # Actualizar resumen diario
        self._update_daily_summary()
        
        return metric
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        session_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> ErrorLog:
        """Registrar un error del sistema."""
        error_log = ErrorLog(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            session_id=session_id,
            endpoint=endpoint
        )
        
        with Session(engine) as session:
            session.add(error_log)
            session.commit()
            session.refresh(error_log)
        
        return error_log
    
    def get_metrics_summary(self, days: int = 7) -> Dict:
        """
        Obtener resumen de métricas de los últimos N días.
        
        Args:
            days: Cantidad de días a consultar
        
        Returns:
            Dict con resumen de métricas
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        
        with Session(engine) as session:
            # Métricas totales
            statement = select(AgentMetrics).where(
                AgentMetrics.created_at >= cutoff_date
            )
            metrics = session.exec(statement).all()
            
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
            unique_sessions = len(set(m.session_id for m in metrics))
            
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
    
    def get_daily_metrics(self, days: int = 30) -> List[Dict]:
        """Obtener métricas diarias para gráficos."""
        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with Session(engine) as session:
            statement = select(DailyMetricsSummary).where(
                DailyMetricsSummary.date >= cutoff_date
            ).order_by(DailyMetricsSummary.date)
            
            summaries = session.exec(statement).all()
            
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
    
    def get_top_agents(self, days: int = 7, limit: int = 5) -> List[Dict]:
        """Obtener agentes más usados."""
        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        
        with Session(engine) as session:
            statement = (
                select(
                    AgentMetrics.agent_mode,
                    func.count(AgentMetrics.id).label("usage_count"),
                    func.sum(AgentMetrics.total_tokens).label("total_tokens"),
                    func.avg(AgentMetrics.response_time).label("avg_response_time")
                )
                .where(AgentMetrics.created_at >= cutoff_date)
                .group_by(AgentMetrics.agent_mode)
                .order_by(func.count(AgentMetrics.id).desc())
                .limit(limit)
            )
            
            results = session.exec(statement).all()
            
            return [
                {
                    "agent": r[0],
                    "usage_count": r[1],
                    "total_tokens": r[2],
                    "avg_response_time": round(r[3], 2)
                }
                for r in results
            ]
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Obtener errores recientes."""
        with Session(engine) as session:
            statement = (
                select(ErrorLog)
                .order_by(ErrorLog.created_at.desc())
                .limit(limit)
            )
            
            errors = session.exec(statement).all()
            
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
    
    def _update_daily_summary(self):
        """Actualizar resumen diario con datos de hoy."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        
        with Session(engine) as session:
            # Obtener métricas de hoy
            statement = select(AgentMetrics).where(
                func.date(AgentMetrics.created_at) == today
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
            
            # Buscar si ya existe resumen de hoy
            existing = session.exec(
                select(DailyMetricsSummary).where(DailyMetricsSummary.date == today)
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
                    date=today,
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
    
    def _empty_summary(self) -> Dict:
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
