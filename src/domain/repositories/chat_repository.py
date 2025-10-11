"""
Interfaces de repositorio para el dominio.

Estas interfaces definen los contratos para acceder a los datos,
independientes de la implementación específica de persistencia.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.chat_models import ChatSession, ChatMessage, FileDocument, FileSection
from ..exceptions.domain_exceptions import (
    ChatSessionNotFoundError,
    ChatSessionAlreadyExistsError,
    MessageNotFoundError,
    FileNotFoundError,
    FileSectionNotFoundError
)


class ChatRepositoryInterface(ABC):
    """Interfaz para operaciones de repositorio de chat."""

    @abstractmethod
    async def get_session(self, session_id: int) -> Optional[ChatSession]:
        """Obtiene una sesión por ID."""
        pass

    @abstractmethod
    async def get_session_by_user(self, user_id: str, session_id: int) -> Optional[ChatSession]:
        """Obtiene una sesión específica de un usuario."""
        pass

    @abstractmethod
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[ChatSession]:
        """Obtiene todas las sesiones de un usuario."""
        pass

    @abstractmethod
    async def create_session(self, user_id: str, session_name: Optional[str] = None) -> ChatSession:
        """Crea una nueva sesión de chat."""
        pass

    @abstractmethod
    async def update_session(self, session: ChatSession) -> ChatSession:
        """Actualiza una sesión existente."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: int) -> bool:
        """Elimina una sesión y todos sus mensajes."""
        pass

    @abstractmethod
    async def save_message(self, message: ChatMessage) -> ChatMessage:
        """Guarda un mensaje en la sesión."""
        pass

    @abstractmethod
    async def get_session_messages(
        self,
        session_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ChatMessage]:
        """Obtiene los mensajes de una sesión."""
        pass

    @abstractmethod
    async def get_message(self, message_id: int) -> Optional[ChatMessage]:
        """Obtiene un mensaje específico."""
        pass

    @abstractmethod
    async def delete_message(self, message_id: int) -> bool:
        """Elimina un mensaje."""
        pass

    @abstractmethod
    async def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Obtiene las sesiones más recientes."""
        pass

    @abstractmethod
    async def get_session_count(self, user_id: str) -> int:
        """Obtiene el número de sesiones de un usuario."""
        pass


class FileRepositoryInterface(ABC):
    """Interfaz para operaciones de repositorio de archivos."""

    @abstractmethod
    async def get_file(self, file_id: int) -> Optional[FileDocument]:
        """Obtiene un archivo por ID."""
        pass

    @abstractmethod
    async def get_user_files(self, user_id: str) -> List[FileDocument]:
        """Obtiene todos los archivos de un usuario."""
        pass

    @abstractmethod
    async def create_file(
        self,
        filename_original: str,
        filename_saved: str,
        file_path: str,
        file_size: int,
        content_type: str
    ) -> FileDocument:
        """Crea un nuevo registro de archivo."""
        pass

    @abstractmethod
    async def update_file(self, file: FileDocument) -> FileDocument:
        """Actualiza un archivo existente."""
        pass

    @abstractmethod
    async def delete_file(self, file_id: int) -> bool:
        """Elimina un archivo y sus secciones."""
        pass

    @abstractmethod
    async def save_section(self, section: FileSection) -> FileSection:
        """Guarda una sección de archivo."""
        pass

    @abstractmethod
    async def get_file_sections(self, file_id: int) -> List[FileSection]:
        """Obtiene todas las secciones de un archivo."""
        pass

    @abstractmethod
    async def get_section(self, section_id: int) -> Optional[FileSection]:
        """Obtiene una sección específica."""
        pass

    @abstractmethod
    async def delete_section(self, section_id: int) -> bool:
        """Elimina una sección de archivo."""
        pass

    @abstractmethod
    async def get_sections_by_page_range(
        self,
        file_id: int,
        start_page: int,
        end_page: int
    ) -> List[FileSection]:
        """Obtiene secciones en un rango de páginas."""
        pass

    @abstractmethod
    async def search_sections_by_content(
        self,
        file_id: int,
        query: str,
        limit: int = 10
    ) -> List[FileSection]:
        """Busca secciones que contengan texto específico."""
        pass

    @abstractmethod
    async def get_files_by_status(self, status: str) -> List[FileDocument]:
        """Obtiene archivos por estado de procesamiento."""
        pass

    @abstractmethod
    async def get_processing_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de procesamiento de archivos."""
        pass


class AgentRepositoryInterface(ABC):
    """Interfaz para operaciones de repositorio de agentes."""

    @abstractmethod
    async def get_agent_config(self, agent_mode: str) -> Dict[str, Any]:
        """Obtiene la configuración de un agente."""
        pass

    @abstractmethod
    async def save_agent_config(self, agent_mode: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda la configuración de un agente."""
        pass

    @abstractmethod
    async def get_available_agents(self) -> List[str]:
        """Obtiene la lista de agentes disponibles."""
        pass

    @abstractmethod
    async def get_agent_usage_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de uso de agentes."""
        pass

    @abstractmethod
    async def log_agent_interaction(
        self,
        agent_mode: str,
        session_id: int,
        token_count: int,
        response_time: float
    ) -> None:
        """Registra una interacción con un agente."""
        pass


class AnalyticsRepositoryInterface(ABC):
    """Interfaz para operaciones de repositorio de analíticas."""

    @abstractmethod
    async def log_chat_interaction(
        self,
        session_id: int,
        message_count: int,
        agent_mode: str,
        has_file_context: bool,
        response_time: float,
        token_count: int
    ) -> None:
        """Registra una interacción de chat para analíticas."""
        pass

    @abstractmethod
    async def get_daily_stats(self, date: datetime) -> Dict[str, Any]:
        """Obtiene estadísticas del día especificado."""
        pass

    @abstractmethod
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de un usuario."""
        pass

    @abstractmethod
    async def get_popular_agents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene los agentes más populares."""
        pass

    @abstractmethod
    async def get_file_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento de archivos."""
        pass
