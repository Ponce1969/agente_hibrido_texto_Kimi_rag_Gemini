"""Modelos de dominio para métricas."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    file_id: Optional[str] = None
    used_bear_search: bool = False
    bear_sources_count: int = 0
    user_rating: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class ErrorLogData:
    """Datos de un log de error (modelo de dominio)."""
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
