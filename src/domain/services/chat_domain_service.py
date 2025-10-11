"""
Servicios de dominio que contienen la lógica de negocio pura.

Estos servicios operan sobre las entidades de dominio y usan las interfaces
de repositorio, independientes de cualquier framework o tecnología específica.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
import uuid

from ..models.chat_models import ChatSession, ChatMessage, MessageRole, FileDocument, FileSection
from ..repositories.chat_repository import ChatRepositoryInterface
from ..exceptions.domain_exceptions import (
    ChatSessionNotFoundError,
    ChatSessionAlreadyExistsError,
    InvalidMessageError,
    MessageNotFoundError,
    FileNotFoundError,
    FileSectionNotFoundError,
    AgentModeNotSupportedError,
    InsufficientContextError,
    RateLimitExceededError,
    ValidationError
)


class ChatDomainService:
    """Servicio de dominio para lógica de chat."""

    def __init__(self, chat_repository: ChatRepositoryInterface) -> None:
        self.chat_repository = chat_repository

    async def create_new_session(self, user_id: str, session_name: Optional[str] = None) -> ChatSession:
        """Crea una nueva sesión de chat."""
        # Validar que el usuario no exceda el límite de sesiones activas
        active_sessions = await self.chat_repository.get_user_sessions(user_id, active_only=True)
        if len(active_sessions) >= 50:  # Límite razonable
            raise RateLimitExceededError("Límite de sesiones activas excedido")

        # Crear la nueva sesión
        session = ChatSession(
            user_id=user_id,
            session_name=session_name or f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
        )

        return await self.chat_repository.create_session(user_id, session_name)

    async def add_message_to_session(
        self,
        session_id: int,
        user_id: str,
        content: str,
        role: MessageRole = MessageRole.USER
    ) -> ChatMessage:
        """Agrega un mensaje a una sesión existente."""
        # Validar la sesión
        session = await self.chat_repository.get_session_by_user(user_id, session_id)
        if not session:
            raise ChatSessionNotFoundError(session_id)

        if not session.is_active:
            raise ValidationError("session", session_id, "La sesión no está activa")

        # Validar el mensaje
        if not content.strip():
            raise InvalidMessageError("El mensaje no puede estar vacío")

        if len(content) > 50000:  # Límite de caracteres
            raise InvalidMessageError("El mensaje es demasiado largo", "máximo 50,000 caracteres")

        # Lógica de dominio: calcular el siguiente índice
        messages = await self.chat_repository.get_session_messages(session_id)
        next_index = len(messages)

        # Crear el mensaje
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            timestamp=datetime.now(UTC),
            message_index=next_index
        )

        # Calcular tokens aproximados (1 token ≈ 4 caracteres)
        message.token_count = len(content) // 4

        return await self.chat_repository.save_message(message)

    async def get_conversation_context(
        self,
        session_id: int,
        user_id: str,
        max_messages: int = 20,
        include_system: bool = True
    ) -> List[ChatMessage]:
        """Obtiene el contexto de la conversación."""
        session = await self.chat_repository.get_session_by_user(user_id, session_id)
        if not session:
            raise ChatSessionNotFoundError(session_id)

        messages = await self.chat_repository.get_session_messages(session_id)

        # Filtrar y limitar mensajes
        if not include_system:
            messages = [msg for msg in messages if msg.role != MessageRole.SYSTEM]

        # Tomar los últimos N mensajes
        context_messages = messages[-max_messages:] if max_messages > 0 else messages

        return context_messages

    async def validate_session_access(self, session_id: int, user_id: str) -> bool:
        """Valida que un usuario tenga acceso a una sesión."""
        session = await self.chat_repository.get_session_by_user(user_id, session_id)
        return session is not None

    async def get_user_session_summary(self, user_id: str) -> Dict[str, Any]:
        """Obtiene un resumen de las sesiones del usuario."""
        sessions = await self.chat_repository.get_user_sessions(user_id)
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.is_active])
        total_messages = sum(s.get_message_count() for s in sessions)

        return {
            "user_id": user_id,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0
        }


class FileDomainService:
    """Servicio de dominio para lógica de archivos."""

    def __init__(self, file_repository: 'FileRepositoryInterface') -> None:
        self.file_repository = file_repository

    async def process_uploaded_file(
        self,
        filename_original: str,
        filename_saved: str,
        file_path: str,
        file_size: int,
        content_type: str
    ) -> FileDocument:
        """Procesa un archivo subido."""
        # Validar el archivo
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise ValidationError("file_size", str(file_size), "Archivo demasiado grande")

        if not self._is_supported_content_type(content_type):
            raise ValidationError("content_type", content_type, "Tipo de archivo no soportado")

        # Crear registro del archivo
        file_doc = await self.file_repository.create_file(
            filename_original=filename_original,
            filename_saved=filename_saved,
            file_path=file_path,
            file_size=file_size,
            content_type=content_type
        )

        return file_doc

    async def add_file_section(
        self,
        file_id: int,
        title: Optional[str],
        start_page: int,
        end_page: int,
        text_content: str
    ) -> FileSection:
        """Agrega una sección a un archivo."""
        # Verificar que el archivo existe
        file_doc = await self.file_repository.get_file(file_id)
        if not file_doc:
            raise FileNotFoundError(file_id)

        if file_doc.has_error():
            raise ValidationError("file", file_id, "El archivo tiene errores de procesamiento")

        # Crear la sección
        section = FileSection(
            file_id=file_id,
            title=title,
            start_page=start_page,
            end_page=end_page,
            char_count=len(text_content),
            text_content=text_content
        )

        return await self.file_repository.save_section(section)

    async def get_file_with_sections(self, file_id: int) -> Optional[FileDocument]:
        """Obtiene un archivo con todas sus secciones."""
        file_doc = await self.file_repository.get_file(file_id)
        if not file_doc:
            return None

        sections = await self.file_repository.get_file_sections(file_id)
        file_doc.sections = sections

        return file_doc

    async def search_file_content(
        self,
        file_id: int,
        query: str,
        max_results: int = 10
    ) -> List[FileSection]:
        """Busca contenido específico en un archivo."""
        if not query.strip():
            raise ValidationError("query", query, "La consulta no puede estar vacía")

        file_doc = await self.file_repository.get_file(file_id)
        if not file_doc:
            raise FileNotFoundError(file_id)

        return await self.file_repository.search_sections_by_content(file_id, query, max_results)

    def _is_supported_content_type(self, content_type: str) -> bool:
        """Verifica si el tipo de contenido es soportado."""
        supported_types = [
            'application/pdf',
            'text/plain',
            'text/markdown',
            'application/json'
        ]
        return content_type.lower() in supported_types

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento de archivos."""
        return await self.file_repository.get_processing_stats()


class AgentDomainService:
    """Servicio de dominio para lógica de agentes."""

    def __init__(self, agent_repository: 'AgentRepositoryInterface') -> None:
        self.agent_repository = agent_repository

    async def validate_agent_mode(self, agent_mode: str) -> bool:
        """Valida que un modo de agente sea soportado."""
        available_agents = await self.agent_repository.get_available_agents()
        return agent_mode in available_agents

    async def get_agent_system_prompt(self, agent_mode: str) -> str:
        """Obtiene el prompt del sistema para un agente."""
        config = await self.agent_repository.get_agent_config(agent_mode)

        if 'system_prompt' not in config:
            raise AgentModeNotSupportedError(agent_mode)

        return config['system_prompt']

    async def log_agent_usage(
        self,
        agent_mode: str,
        session_id: int,
        token_count: int,
        response_time: float
    ) -> None:
        """Registra el uso de un agente."""
        await self.agent_repository.log_agent_interaction(
            agent_mode=agent_mode,
            session_id=session_id,
            token_count=token_count,
            response_time=response_time
        )

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de agentes."""
        return await self.agent_repository.get_agent_usage_stats()


class ValidationService:
    """Servicio de dominio para validaciones comunes."""

    @staticmethod
    def validate_user_id(user_id: str) -> None:
        """Valida un ID de usuario."""
        if not user_id or not user_id.strip():
            raise ValidationError("user_id", user_id, "ID de usuario requerido")

        if len(user_id) > 100:
            raise ValidationError("user_id", user_id, "ID de usuario demasiado largo")

    @staticmethod
    def validate_session_name(session_name: Optional[str]) -> None:
        """Valida un nombre de sesión."""
        if session_name and len(session_name) > 200:
            raise ValidationError("session_name", session_name, "Nombre demasiado largo")

    @staticmethod
    def validate_message_content(content: str) -> None:
        """Valida el contenido de un mensaje."""
        if not content or not content.strip():
            raise ValidationError("content", content, "Contenido requerido")

        if len(content) > 50000:
            raise ValidationError("content", content, "Contenido demasiado largo")

    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 100) -> None:
        """Valida el tamaño de un archivo."""
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size <= 0:
            raise ValidationError("file_size", str(file_size), "Tamaño debe ser positivo")

        if file_size > max_size_bytes:
            raise ValidationError("file_size", str(file_size), f"Tamaño excede {max_size_mb}MB")
