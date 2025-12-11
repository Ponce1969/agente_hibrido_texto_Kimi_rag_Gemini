"""
Puerto (Interface) para repositorios de chat.

Este puerto define el contrato para persistencia de sesiones y mensajes de chat.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.chat_models import (
        ChatMessage,
        ChatMessageCreate,
        ChatSession,
        ChatSessionCreate,
    )


class ChatRepositoryPort(ABC):
    """
    Puerto para repositorio de chat.

    Esta interfaz abstrae la persistencia de datos de chat,
    permitiendo cambiar entre SQLite, PostgreSQL, MongoDB, etc.
    sin afectar la lógica de negocio.
    """

    @abstractmethod
    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """Crea una nueva sesión de chat."""
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> ChatSession | None:
        """Obtiene una sesión por su ID."""
        ...

    @abstractmethod
    def list_sessions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatSession]:
        """
        Lista las sesiones de chat.

        Args:
            limit: Número máximo de sesiones a retornar
            offset: Número de sesiones a saltar (paginación)

        Returns:
            Lista de sesiones ordenadas por fecha de actualización
        """
        ...

    @abstractmethod
    def update_session(
        self,
        session_id: str,
        *,
        title: str | None = None,
    ) -> ChatSession:
        """Actualiza una sesión existente."""
        ...

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión de chat."""
        ...

    @abstractmethod
    def add_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """Agrega un mensaje a una sesión."""
        ...

    @abstractmethod
    def get_session_messages(
        self,
        session_id: str,
        *,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        """Obtiene los mensajes de una sesión."""
        ...

    @abstractmethod
    def get_message(self, message_id: int) -> ChatMessage | None:
        """Obtiene un mensaje por su ID."""
        ...

    @abstractmethod
    def count_session_messages(self, session_id: str) -> int:
        """Cuenta los mensajes de una sesión."""
        ...
