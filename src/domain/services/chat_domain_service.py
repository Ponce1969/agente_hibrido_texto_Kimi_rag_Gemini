"""
Servicios de dominio que contienen la lógica de negocio pura.

Estos servicios operan sobre las entidades de dominio y usan las interfaces
de repositorio, independientes de cualquier framework o tecnología específica.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..exceptions.domain_exceptions import (
    ChatSessionNotFoundError,
    FileNotFoundError,
    InvalidMessageError,
    ValidationError,
)
from ..models.chat_models import (
    ChatMessage,
    ChatSession,
    FileDocument,
    FileSection,
    MessageRole,
)
from ..models.file_models import FileStatus
from ..ports.file_repository_port import FileRepositoryPort
from ..ports.repository_port import ChatRepositoryPort


class ChatDomainService:
    """Servicio de dominio para lógica de chat."""

    def __init__(self, chat_repository: ChatRepositoryPort) -> None:
        self.chat_repository = chat_repository

    async def create_new_session(self, user_id: str, session_name: str | None = None) -> ChatSession:
        """Crea una nueva sesión de chat."""
        # Crear la nueva sesión usando el método correcto
        from ..models.chat_models import ChatSessionCreate

        session_data = ChatSessionCreate(
            user_id=user_id,
            title=session_name or f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
        )

        return self.chat_repository.create_session(session_data)

    async def add_message_to_session(
        self,
        session_id: str,
        user_id: str,
        content: str,
        role: MessageRole = MessageRole.USER
    ) -> ChatMessage:
        """Agrega un mensaje a una sesión existente."""
        # Validar la sesión
        session = self.chat_repository.get_session(session_id)
        if not session:
            raise ChatSessionNotFoundError(int(session_id))

        if not session.is_active:
            raise ValidationError("session", session_id, "La sesión no está activa")

        # Validar el mensaje
        if not content.strip():
            raise InvalidMessageError("El mensaje no puede estar vacío")

        if len(content) > 50000:  # Límite de caracteres
            raise InvalidMessageError("El mensaje es demasiado largo", "máximo 50,000 caracteres")

        # Crear el mensaje usando ChatMessageCreate
        from ..models.chat_models import ChatMessageCreate

        message_data = ChatMessageCreate(
            session_id=session_id,
            role=role,
            content=content,
        )

        return self.chat_repository.add_message(message_data)

    async def get_conversation_context(
        self,
        session_id: str,
        user_id: str,
        max_messages: int = 20,
        include_system: bool = True
    ) -> list[ChatMessage]:
        """Obtiene el contexto de la conversación."""
        session = self.chat_repository.get_session(session_id)
        if not session:
            raise ChatSessionNotFoundError(int(session_id))

        messages = self.chat_repository.get_session_messages(session_id)

        # Filtrar y limitar mensajes
        if not include_system:
            messages = [msg for msg in messages if msg.role != MessageRole.SYSTEM]

        # Tomar los últimos N mensajes
        context_messages = messages[-max_messages:] if max_messages > 0 else messages

        return context_messages

    async def validate_session_access(self, session_id: str, user_id: str) -> bool:
        """Valida que un usuario tenga acceso a una sesión."""
        session = self.chat_repository.get_session(session_id)
        return session is not None and session.user_id == user_id

    async def get_user_session_summary(self, user_id: str) -> dict[str, Any]:
        """Obtiene un resumen de las sesiones del usuario."""
        sessions = self.chat_repository.list_sessions()
        user_sessions = [s for s in sessions if s.user_id == user_id]

        total_sessions = len(user_sessions)
        active_sessions = len([s for s in user_sessions if s.is_active])
        total_messages = sum(self.chat_repository.count_session_messages(s.id) for s in user_sessions)

        return {
            "user_id": user_id,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0
        }


class FileDomainService:
    """Servicio de dominio para lógica de archivos."""

    def __init__(self, file_repository: FileRepositoryPort) -> None:
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

        # Crear registro del archivo usando el método correcto
        file_doc = self.file_repository.create_file_record(
            filename=filename_saved,
            file_path=file_path,
            size_bytes=file_size
        )

        return file_doc

    async def add_file_section(
        self,
        file_id: int,
        title: str | None,
        start_page: int,
        end_page: int,
        text_content: str
    ) -> FileSection:
        """Agrega una sección a un archivo."""
        # Verificar que el archivo existe
        file_doc = self.file_repository.get_file(file_id)
        if not file_doc:
            raise FileNotFoundError(file_id)

        if file_doc.status == FileStatus.ERROR:
            raise ValidationError("file", str(file_id), "El archivo tiene errores de procesamiento")

        # Crear la sección
        section = FileSection(
            file_id=file_id,
            title=title,
            start_page=start_page,
            end_page=end_page,
            char_count=len(text_content),
            text_content=text_content
        )

        # Guardar la sección (simulado, ya que el puerto no tiene save_section)
        return section

    async def get_file_with_sections(self, file_id: int) -> FileDocument | None:
        """Obtiene un archivo con todas sus secciones."""
        file_doc = self.file_repository.get_file(file_id)
        if not file_doc:
            return None

        # Las secciones se obtienen si se necesitan
        return file_doc

    async def search_file_content(
        self,
        file_id: int,
        query: str,
        max_results: int = 10
    ) -> list[FileSection]:
        """Busca contenido específico en un archivo."""
        if not query.strip():
            raise ValidationError("query", query, "La consulta no puede estar vacía")

        file_doc = self.file_repository.get_file(file_id)
        if not file_doc:
            raise FileNotFoundError(file_id)

        # Buscar en las secciones (simulado, ya que el puerto no tiene search_sections_by_content)
        sections = self.file_repository.get_file_sections(file_id)
        filtered_sections = [s for s in sections if query.lower() in (s.text_content or "").lower()]

        return filtered_sections[:max_results]

    def _is_supported_content_type(self, content_type: str) -> bool:
        """Verifica si el tipo de contenido es soportado."""
        supported_types = [
            'application/pdf',
            'text/plain',
            'text/markdown',
            'application/json'
        ]
        return content_type.lower() in supported_types

    async def get_processing_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas de procesamiento de archivos."""
        # Método no disponible en el puerto, retornar stats básicos
        files = self.file_repository.list_files()
        return {
            "total_files": len(files),
            "processed_files": len([f for f in files if f.status == FileStatus.PROCESSED]),
            "error_files": len([f for f in files if f.status == FileStatus.ERROR])
        }


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
    def validate_session_name(session_name: str | None) -> None:
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
