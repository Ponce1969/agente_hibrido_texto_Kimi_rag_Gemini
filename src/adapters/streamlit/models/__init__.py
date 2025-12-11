"""
Modelos y DTOs para la interfaz Streamlit.
Siguiendo principios de arquitectura hexagonal.
"""

from .chat_models import AgentMode, ChatMessage, ChatRequest, ChatResponse, ChatSession
from .file_models import (
    EmbeddingSearchResult,
    FileProgress,
    FileSection,
    FileStatus,
    FileUploadInfo,
    ProcessingPhase,
)

__all__ = [
    # Chat models
    "AgentMode", "ChatMessage", "ChatSession", "ChatRequest", "ChatResponse",
    # File models
    "FileStatus", "ProcessingPhase", "FileUploadInfo",
    "FileProgress", "FileSection", "EmbeddingSearchResult"
]
