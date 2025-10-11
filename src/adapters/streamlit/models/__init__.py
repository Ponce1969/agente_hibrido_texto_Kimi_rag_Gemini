"""
Modelos y DTOs para la interfaz Streamlit.
Siguiendo principios de arquitectura hexagonal.
"""

from .chat_models import AgentMode, ChatMessage, ChatSession, ChatRequest, ChatResponse
from .file_models import (
    FileStatus, ProcessingPhase, FileUploadInfo, 
    FileProgress, FileSection, EmbeddingSearchResult
)

__all__ = [
    # Chat models
    "AgentMode", "ChatMessage", "ChatSession", "ChatRequest", "ChatResponse",
    # File models
    "FileStatus", "ProcessingPhase", "FileUploadInfo", 
    "FileProgress", "FileSection", "EmbeddingSearchResult"
]
