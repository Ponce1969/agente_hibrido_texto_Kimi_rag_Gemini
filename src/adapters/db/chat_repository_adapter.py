"""
Adaptador de repositorio SQLite/PostgreSQL que implementa ChatRepositoryPort.

Este adaptador conecta la lógica de negocio con la base de datos
siguiendo el patrón de arquitectura hexagonal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, func, select

from src.adapters.db.chat import ChatSession as ChatSessionDB
from src.adapters.db.message import ChatMessage as ChatMessageDB
from src.domain.ports.repository_port import ChatRepositoryPort

if TYPE_CHECKING:
    from src.domain.models import (
        ChatMessage,
        ChatMessageCreate,
        ChatSession,
        ChatSessionCreate,
    )


class SQLChatRepositoryAdapter(ChatRepositoryPort):
    """
    Adaptador de repositorio SQL que implementa ChatRepositoryPort.

    Características:
    - Usa SQLModel para ORM
    - Compatible con SQLite y PostgreSQL
    - Convierte entre modelos de dominio y modelos de DB
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa el adaptador de repositorio.

        Args:
            session: Sesión de SQLModel/SQLAlchemy
        """
        self.session = session

    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """
        Crea una nueva sesión de chat.

        Args:
            session_data: Datos para crear la sesión

        Returns:
            Sesión creada (modelo de dominio)
        """
        # Convertir de DTO de dominio a modelo de DB
        db_session = ChatSessionDB(
            session_name=session_data.title,  # El dominio usa 'title', DB usa 'session_name'
            user_id=session_data.user_id,
        )

        self.session.add(db_session)
        self.session.commit()
        self.session.refresh(db_session)

        # Convertir de modelo de DB a modelo de dominio
        return self._db_session_to_domain(db_session)

    def get_session(self, session_id: str) -> ChatSession | None:
        """
        Obtiene una sesión por su ID.

        Args:
            session_id: ID de la sesión

        Returns:
            Sesión encontrada o None
        """
        statement = (
            select(ChatSessionDB)
            .where(ChatSessionDB.id == int(session_id))
        )
        db_session = self.session.exec(statement).first()

        if not db_session:
            return None

        return self._db_session_to_domain(db_session)

    def list_sessions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatSession]:
        """
        Lista solo las sesiones que tienen mensajes.

        Filtra automáticamente las sesiones sin mensajes para
        mantener la interfaz limpia y ordenada.

        Args:
            limit: Número máximo de sesiones
            offset: Número de sesiones a saltar

        Returns:
            Lista de sesiones con al menos 1 mensaje
        """
        # Subquery para contar mensajes por sesión
        message_count = (
            select(func.count(ChatMessageDB.id))
            .where(ChatMessageDB.session_id == ChatSessionDB.id)
            .scalar_subquery()
        )

        statement = (
            select(ChatSessionDB)
            .where(message_count > 0)  # Solo sesiones con mensajes
            .order_by(ChatSessionDB.updated_at.desc())  # type: ignore[arg-defined]
            .limit(limit)
            .offset(offset)
        )

        db_sessions = self.session.exec(statement).all()
        return [self._db_session_to_domain(s) for s in db_sessions]

    def count_session_messages(self, session_id: str) -> int:
        """
        Cuenta los mensajes de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Número de mensajes
        """
        statement = (
            select(func.count())
            .select_from(ChatMessageDB)
            .where(ChatMessageDB.session_id == int(session_id))
        )
        count = self.session.exec(statement).first()
        return count or 0


    def update_session(
        self,
        session_id: str,
        title: str | None = None,
    ) -> ChatSession:
        """
        Actualiza una sesión existente.

        Args:
            session_id: ID de la sesión
            title: Nuevo título

        Returns:
            Sesión actualizada
        """
        db_session = self.session.get(ChatSessionDB, int(session_id))

        if not db_session:
            raise ValueError(f"Sesión {session_id} no encontrada")

        if title is not None:
            db_session.title = title

        self.session.commit()
        self.session.refresh(db_session)

        return self._db_session_to_domain(db_session)

    def delete_session(self, session_id: str) -> bool:
        """
        Elimina una sesión y todos sus mensajes.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se eliminó, False si no existía
        """
        db_session = self.session.get(ChatSessionDB, int(session_id))

        if not db_session:
            return False

        self.session.delete(db_session)
        self.session.commit()

        return True

    def add_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """
        Agrega un mensaje a una sesión.

        Args:
            message_data: Datos del mensaje

        Returns:
            Mensaje creado (modelo de dominio)
        """
        # Crear mensaje en DB
        db_message = ChatMessageDB(
            session_id=int(message_data.session_id),
            role=message_data.role.value,
            content=message_data.content,
            message_index=message_data.message_index, # El índice ahora lo calcula el dominio
        )

        self.session.add(db_message)
        self.session.commit()
        self.session.refresh(db_message)

        return self._db_message_to_domain(db_message)

    def get_session_messages(
        self,
        session_id: str,
        *,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        """
        Obtiene los mensajes de una sesión.

        Args:
            session_id: ID de la sesión
            limit: Número máximo de mensajes

        Returns:
            Lista de mensajes ordenados por índice
        """
        statement = (
            select(ChatMessageDB)
            .where(ChatMessageDB.session_id == int(session_id))
            .order_by(ChatMessageDB.message_index)  # type: ignore[arg-type]
        )

        if limit is not None:
            statement = statement.limit(limit)

        db_messages = self.session.exec(statement).all()

        return [self._db_message_to_domain(m) for m in db_messages]

    def get_message(self, message_id: int) -> ChatMessage | None:
        """
        Obtiene un mensaje por su ID.

        Args:
            message_id: ID del mensaje

        Returns:
            Mensaje encontrado o None
        """
        db_message = self.session.get(ChatMessageDB, message_id)

        if not db_message:
            return None

        return self._db_message_to_domain(db_message)

    # Métodos privados de conversión

    def _db_session_to_domain(self, db_session) -> ChatSession:
        """Convierte modelo de DB a modelo de dominio."""

        # Retornar directamente el modelo de DB (ChatSession ya es el modelo correcto)
        return db_session

    def _db_message_to_domain(self, db_message: ChatMessageDB) -> ChatMessage:
        """Convierte modelo de DB a modelo de dominio."""
        from datetime import UTC, datetime

        from src.domain.models import ChatMessage, MessageRole

        return ChatMessage(
            session_id=db_message.session_id,
            role=MessageRole(db_message.role),
            content=db_message.content,
            timestamp=getattr(db_message, 'created_at', datetime.now(UTC)),
            message_index=db_message.message_index,
            metadata={},
            token_count=None,
        )
