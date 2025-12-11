"""Modelos de dominio para métricas."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentMetricData:
    """Datos de una métrica de agente (modelo de dominio)."""
    session_id: str
    agent_mode: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    response_time: float
    model_name: str
    has_rag_context: bool = False
    rag_chunks_used: int = 0
    file_id: str | None = None
    used_bear_search: bool = False
    bear_sources_count: int = 0
    user_rating: int | None = None
    id: int | None = None
    created_at: datetime | None = None


@dataclass
class ErrorLogData:
    """Datos de un log de error (modelo de dominio)."""
    error_type: str
    error_message: str
    stack_trace: str | None = None
    session_id: str | None = None
    endpoint: str | None = None
    id: int | None = None
    created_at: datetime | None = None
