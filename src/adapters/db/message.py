from datetime import datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Index, Text
from enum import Enum


class MessageRole(str, Enum):
    """Roles posibles para los mensajes"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessageBase(SQLModel):
    """Modelo base para mensajes de chat"""
    role: MessageRole = Field(description="Rol del emisor del mensaje")
    content: str = Field(sa_type=Text, description="Contenido del mensaje")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_index: int = Field(description="Índice secuencial dentro de la sesión")
    
    # Metadatos opcionales
    extra_data: Optional[str] = Field(default=None, description="JSON string para datos adicionales")
    token_count: Optional[int] = Field(default=None, description="Número de tokens del mensaje")


class ChatMessage(ChatMessageBase, table=True):
    """Modelo de tabla para mensajes de chat"""
    __tablename__ = "chat_messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_sessions.id", index=True)
    
    # Relación con sesión
    session: "ChatSession" = Relationship(back_populates="messages")
    
    # Índices para optimización
    __table_args__ = (
        Index("idx_session_messages", "session_id", "message_index"),
        Index("idx_timestamp", "timestamp"),
    )


class ChatMessageCreate(ChatMessageBase):
    """Schema para crear nuevos mensajes"""
    session_id: int


class ChatMessageUpdate(SQLModel):
    """Schema para actualizar mensajes (ej: editar contenido)"""
    content: Optional[str] = None
    extra_data: Optional[str] = None


class ChatMessagePublic(ChatMessageBase):
    """Schema público para respuestas de API"""
    id: int
    session_id: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Importar después para evitar circular imports
from src.adapters.db.chat import ChatSession