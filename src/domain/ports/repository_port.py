"""
Puerto (Interface) para repositorios de chat.

Este puerto define el contrato para persistencia de sesiones y mensajes de chat.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.chat_models import ChatSession, ChatMessage, ChatMessageCreate, ChatSessionCreate


class ChatRepositoryPort(ABC):
    """
    Puerto para repositorio de chat.
    
    Esta interfaz abstrae la persistencia de datos de chat,
    permitiendo cambiar entre SQLite, PostgreSQL, MongoDB, etc.
    sin afectar la lógica de negocio.
    
    Ejemplos de implementaciones:
        - SQLiteChatRepository: Usa SQLite para persistencia local
        - PostgresChatRepository: Usa PostgreSQL para producción
        - InMemoryChatRepository: Usa memoria RAM para testing
    """
    
    @abstractmethod
    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """
        Crea una nueva sesión de chat.
        
        Args:
            session_data: Datos para crear la sesión
            
        Returns:
            Sesión creada con ID asignado
            
        Raises:
            RepositoryError: Si hay error en la creación
        """
        ...
    
    @abstractmethod
    def get_session(self, session_id: str) -> ChatSession | None:
        """
        Obtiene una sesión por su ID.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Sesión encontrada o None si no existe
        """
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
        """
        Actualiza una sesión existente.
        
        Args:
            session_id: ID de la sesión
            title: Nuevo título (opcional)
            
        Returns:
            Sesión actualizada
            
        Raises:
            SessionNotFoundError: Si la sesión no existe
        """
        ...
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """
        Elimina una sesión y todos sus mensajes.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            True si se eliminó, False si no existía
        """
        ...
    
    @abstractmethod
    def add_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        """
        Agrega un mensaje a una sesión.
        
        Args:
            message_data: Datos del mensaje a crear
            
        Returns:
            Mensaje creado con ID asignado
            
        Raises:
            SessionNotFoundError: Si la sesión no existe
        """
        ...
    
    @abstractmethod
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
            limit: Número máximo de mensajes (None = todos)
            
        Returns:
            Lista de mensajes ordenados por índice
        """
        ...
    
    @abstractmethod
    def get_message(self, message_id: int) -> ChatMessage | None:
        """
        Obtiene un mensaje por su ID.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            Mensaje encontrado o None si no existe
        """
        ...
    
    @abstractmethod
    def count_session_messages(self, session_id: str) -> int:
        """
        Cuenta los mensajes de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Número de mensajes en la sesión
        """
        ...
