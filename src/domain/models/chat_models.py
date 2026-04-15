"""
Modelos de dominio puros para el asistente de aprendizaje de Python.

Estos modelos representan entidades de negocio independientes de cualquier
tecnología de persistencia o presentación.

Tipado estricto para mypy --strict con Python 3.12+
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    """Roles posibles para los mensajes en el dominio."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Representa un mensaje en una conversación."""

    session_id: int
    role: MessageRole
    content: str
    timestamp: datetime
    message_index: int
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int | None = None

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.content.strip():
            raise ValueError("El contenido del mensaje no puede estar vacío")

        if len(self.content) > 100000:  # Límite razonable
            raise ValueError("El contenido del mensaje es demasiado largo")

        if self.message_index < 0:
            raise ValueError("El índice del mensaje debe ser no negativo")

    def is_from_user(self) -> bool:
        """Verifica si el mensaje es del usuario."""
        return self.role == MessageRole.USER

    def is_from_assistant(self) -> bool:
        """Verifica si el mensaje es del asistente."""
        return self.role == MessageRole.ASSISTANT

    def is_system_message(self) -> bool:
        """Verifica si el mensaje es del sistema."""
        return self.role == MessageRole.SYSTEM

    def to_dict(self) -> dict[str, Any]:
        """Convierte el mensaje a diccionario."""
        return {
            "session_id": self.session_id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_index": self.message_index,
            "metadata": self.metadata,
            "token_count": self.token_count,
        }


@dataclass
class ChatSession:
    """Representa una sesión de conversación."""

    user_id: str
    session_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    # Relación con mensajes (no se incluye en __init__)
    messages: list[ChatMessage] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.user_id.strip():
            raise ValueError("El ID de usuario no puede estar vacío")

        if self.session_name and len(self.session_name) > 200:
            raise ValueError("El nombre de la sesión es demasiado largo")

    def add_message(self, message: ChatMessage) -> None:
        """Agrega un mensaje a la sesión."""
        if message.session_id != self.id:
            raise ValueError("El mensaje no pertenece a esta sesión")

        # Actualizar timestamp
        self.updated_at = datetime.now(UTC)

        # Agregar mensaje
        self.messages.append(message)

        # Actualizar índice del mensaje
        message.message_index = len(self.messages) - 1

    def get_message_count(self) -> int:
        """Retorna el número de mensajes en la sesión."""
        return len(self.messages)

    def get_user_messages(self) -> list[ChatMessage]:
        """Retorna solo los mensajes del usuario."""
        return [msg for msg in self.messages if msg.is_from_user()]

    def get_assistant_messages(self) -> list[ChatMessage]:
        """Retorna solo los mensajes del asistente."""
        return [msg for msg in self.messages if msg.is_from_assistant()]

    def get_last_message(self) -> ChatMessage | None:
        """Retorna el último mensaje de la sesión."""
        return self.messages[-1] if self.messages else None

    def is_empty(self) -> bool:
        """Verifica si la sesión está vacía."""
        return len(self.messages) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convierte la sesión a diccionario."""
        return {
            "user_id": self.user_id,
            "session_name": self.session_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "metadata": self.metadata,
            "message_count": len(self.messages),
        }

    @property
    def id(self) -> int:
        """ID de la sesión (se asignará externamente)."""
        return getattr(self, "_id", 0)

    @id.setter
    def id(self, value: int) -> None:
        """Establece el ID de la sesión."""
        self._id = value


# ============================================================================
# DTOs para Creación (Data Transfer Objects)
# ============================================================================


@dataclass
class ChatSessionCreate:
    """DTO para crear una nueva sesión de chat."""

    title: str
    user_id: str = "default_user"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.title.strip():
            raise ValueError("El título no puede estar vacío")

        if len(self.title) > 200:
            raise ValueError("El título es demasiado largo")


@dataclass
class ChatMessageCreate:
    """DTO para crear un nuevo mensaje."""

    session_id: str
    role: MessageRole
    content: str
    message_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validación después de inicialización."""
        if not self.content.strip():
            raise ValueError("El contenido no puede estar vacío")

        if len(self.content) > 100000:
            raise ValueError("El contenido es demasiado largo")

        if self.message_index < 0:
            raise ValueError("El índice debe ser no negativo")
