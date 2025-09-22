from typing import List, Optional
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from src.adapters.db.chat import ChatSession, ChatSessionCreate, ChatSessionUpdate
from src.adapters.db.message import ChatMessage, ChatMessageCreate, MessageRole


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
    
    def get_session(self, session_id: int) -> Optional[ChatSession]:
        """Obtiene una sesión por ID con sus mensajes"""
        statement = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return self.session.exec(statement).first()
    
    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[ChatSession]:
        """Obtiene las sesiones de un usuario"""
        statement = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))
    
    def update_session(self, session_id: int, updates: ChatSessionUpdate) -> Optional[ChatSession]:
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
    
    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        """Obtiene todos los mensajes de una sesión ordenados"""
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.message_index)
        )
        return list(self.session.exec(statement))
    
    def get_last_messages(self, session_id: int, limit: int = 10) -> List[ChatMessage]:
        """Obtiene los últimos N mensajes de una sesión"""
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.message_index.desc())
            .limit(limit)
        )
        return list(reversed(self.session.exec(statement).all()))
    
    def get_message_count(self, session_id: int) -> int:
        """Cuenta los mensajes en una sesión"""
        statement = select(func.count(ChatMessage.id)).where(
            ChatMessage.session_id == session_id
        )
        return self.session.exec(statement).first() or 0
    
    def clear_session(self, session_id: int) -> int:
        """Limpia todos los mensajes de una sesión"""
        deleted_count = self.session.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
        ).count()
        
        self.session.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()
        
        # Actualizar timestamp
        session = self.get_session(session_id)
        if session:
            session.updated_at = func.now()
        
        self.session.commit()
        return deleted_count