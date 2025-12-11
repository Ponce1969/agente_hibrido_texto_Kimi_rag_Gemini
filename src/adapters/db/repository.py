
from sqlalchemy.orm import selectinload
from sqlmodel import Session, delete, func, select

from src.adapters.db.chat import ChatSession, ChatSessionCreate, ChatSessionUpdate
from src.adapters.db.message import ChatMessage, ChatMessageCreate


class ChatRepository:
    """Repositorio para operaciones de base de datos"""

    def __init__(self, session: Session):
        self.session = session

    # Métodos para ChatSession
    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """Crea una nueva sesión de chat"""
        db_session = ChatSession.model_validate(session_data)
        self.session.add(db_session)
        self.session.commit()
        self.session.refresh(db_session)
        return db_session

    def get_session(self, session_id: int) -> ChatSession | None:
        """Obtiene una sesión por ID con sus mensajes"""
        statement = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return self.session.exec(statement).first()

    async def list_sessions(self, limit: int = 50, offset: int = 0) -> list[ChatSession]:
        """Obtiene todas las sesiones."""
        import asyncio
        def _list_sessions():
            statement = select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit).offset(offset)
            return list(self.session.exec(statement))
        return await asyncio.to_thread(_list_sessions)

    def update_session(self, session_id: int, updates: ChatSessionUpdate) -> ChatSession | None:
        """Actualiza una sesión existente"""
        db_session = self.get_session(session_id)
        if db_session:
            for field, value in updates.model_dump(exclude_unset=True).items():
                setattr(db_session, field, value)
            self.session.commit()
            self.session.refresh(db_session)
        return db_session

    def delete_session(self, session_id: int) -> bool:
        """Elimina una sesión y todos sus mensajes"""
        db_session = self.get_session(session_id)
        if db_session:
            self.session.delete(db_session)
            self.session.commit()
            return True
        return False

    # Métodos para ChatMessage
    def add_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """Agrega un mensaje a una sesión"""
        # Obtener el siguiente índice de mensaje
        statement = (
            select(func.max(ChatMessage.message_index))
            .where(ChatMessage.session_id == message_data.session_id)
        )
        max_index = self.session.exec(statement).first()
        next_index = (max_index or 0) + 1

        # Excluir cualquier 'message_index' entrante; este repositorio lo calcula
        payload = message_data.model_dump(exclude={"message_index"})
        db_message = ChatMessage(
            **payload,
            message_index=next_index
        )
        self.session.add(db_message)

        # Actualizar timestamp de la sesión
        session = self.get_session(message_data.session_id)
        if session:
            session.updated_at = func.now()

        self.session.commit()
        self.session.refresh(db_message)
        return db_message

    def get_session_messages(self, session_id: int) -> list[ChatMessage]:
        """Obtiene todos los mensajes de una sesión ordenados"""
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.message_index)
        )
        return list(self.session.exec(statement))

    async def count_session_messages(self, session_id: int) -> int:
        """Cuenta los mensajes de una sesión."""
        import asyncio

        def _count():
            statement = select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
            return self.session.exec(statement).one_or_none() or 0

        return await asyncio.to_thread(_count)


    def clear_session(self, session_id: int) -> int:
        """Limpia todos los mensajes de una sesión"""
        deleted_count = self.session.exec(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        ).count()

        delete_stmt = delete(ChatMessage).where(ChatMessage.session_id == session_id)
        self.session.exec(delete_stmt)

        session = self.get_session(session_id)
        if session:
            session.updated_at = func.now()

        self.session.commit()
        return deleted_count


