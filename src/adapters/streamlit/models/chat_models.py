"""
Modelos para el sistema de chat en Streamlit.
"""
from dataclasses import dataclass

from src.adapters.agents.prompts import AgentMode


@dataclass
class ChatMessage:
    """Modelo para un mensaje de chat."""
    role: str
    content: str
    message_index: int
    created_at: str | None = None


@dataclass
class ChatSession:
    """Modelo para una sesión de chat."""
    id: int
    user_id: str
    session_name: str | None
    created_at: str
    message_count: int = 0


@dataclass
class ChatRequest:
    """Modelo para una petición de chat."""
    session_id: int
    message: str
    mode: AgentMode
    file_id: int | None = None
    selected_section_ids: list[int] | None = None


@dataclass
class ChatResponse:
    """Modelo para una respuesta de chat."""
    content: str
    success: bool
    error: str | None = None
