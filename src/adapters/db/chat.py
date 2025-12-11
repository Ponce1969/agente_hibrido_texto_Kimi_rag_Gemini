from datetime import datetime

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel


class ChatSessionBase(SQLModel):
    """Modelo base para sesiones de chat"""
    user_id: str = Field(index=True, description="ID único del usuario")
    session_name: str | None = Field(default=None, description="Nombre descriptivo de la sesión")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    extra_data: str | None = Field(default=None, description="JSON string para datos adicionales")


class ChatSession(ChatSessionBase, table=True):
    """Modelo de tabla para sesiones de chat"""
    __tablename__ = "chat_sessions"

    id: int | None = Field(default=None, primary_key=True)

    # Relación con mensajes
    messages: list["ChatMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Índices para optimización
    __table_args__ = (
        Index("idx_user_sessions", "user_id", "is_active"),
        Index("idx_created_at", "created_at"),
    )


class ChatSessionCreate(ChatSessionBase):
    """Schema para crear nuevas sesiones"""
    pass


class ChatSessionUpdate(SQLModel):
    """Schema para actualizar sesiones"""
    session_name: str | None = None
    is_active: bool | None = None
    extra_data: str | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSessionPublic(ChatSessionBase):
    """Schema público para respuestas de API"""
    id: int
    message_count: int = 0

    @classmethod
    def from_orm(cls, session: ChatSession) -> "ChatSessionPublic":
        """Método auxiliar para serialización"""
        public = cls.model_validate(session)
        public.message_count = len(session.messages)
        return public


# Importar después para evitar circular imports
from src.adapters.db.message import ChatMessage
