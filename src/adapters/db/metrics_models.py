"""Modelos de base de datos para métricas de agentes."""
from datetime import datetime, UTC
from typing import Optional
from sqlmodel import Field, SQLModel


class AgentMetrics(SQLModel, table=True):
    """Métricas de uso de agentes IA."""
    
    __tablename__ = "agent_metrics"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Identificación
    session_id: str = Field(index=True)
    agent_mode: str = Field(index=True)  # "Arquitecto Python Senior", etc.
    
    # Tokens
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    
    # Costos estimados (en USD)
    estimated_cost: float = Field(default=0.0)
    
    # Tiempos (en segundos)
    response_time: float = Field(default=0.0)
    
    # Contexto
    has_rag_context: bool = Field(default=False)
    rag_chunks_used: int = Field(default=0)
    file_id: Optional[str] = Field(default=None)
    
    # Búsqueda externa
    used_bear_search: bool = Field(default=False)
    bear_sources_count: int = Field(default=0)
    
    # Modelo usado
    model_name: str = Field(default="")  # "kimi-k2", "gemini-2.5-flash", etc.
    
    # Calidad de respuesta (opcional, para feedback)
    user_rating: Optional[int] = Field(default=None)  # 1-5 estrellas
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123",
                "agent_mode": "Arquitecto Python Senior",
                "prompt_tokens": 150,
                "completion_tokens": 300,
                "total_tokens": 450,
                "estimated_cost": 0.0023,
                "response_time": 2.5,
                "has_rag_context": True,
                "rag_chunks_used": 5,
                "model_name": "gemini-2.5-flash"
            }
        }


class DailyMetricsSummary(SQLModel, table=True):
    """Resumen diario de métricas agregadas."""
    
    __tablename__ = "daily_metrics_summary"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Fecha
    date: str = Field(index=True)  # YYYY-MM-DD
    
    # Contadores
    total_requests: int = Field(default=0)
    total_sessions: int = Field(default=0)
    
    # Tokens totales
    total_prompt_tokens: int = Field(default=0)
    total_completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    
    # Costos
    total_cost: float = Field(default=0.0)
    
    # Tiempos promedio
    avg_response_time: float = Field(default=0.0)
    
    # Uso de features
    rag_requests: int = Field(default=0)
    bear_requests: int = Field(default=0)
    
    # Por agente (JSON string)
    agent_usage: str = Field(default="{}")  # {"Arquitecto": 10, "Ingeniero": 5}
    
    # Timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ErrorLog(SQLModel, table=True):
    """Log de errores del sistema."""
    
    __tablename__ = "error_logs"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Error info
    error_type: str = Field(index=True)
    error_message: str
    stack_trace: Optional[str] = Field(default=None)
    
    # Contexto
    session_id: Optional[str] = Field(default=None)
    endpoint: Optional[str] = Field(default=None)
    
    # Timestamp
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "APIError",
                "error_message": "Rate limit exceeded",
                "endpoint": "/api/chat"
            }
        }
