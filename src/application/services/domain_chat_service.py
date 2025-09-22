"""
Servicio de aplicación refactorizado para usar el Domain Layer.

Este servicio ahora usa las entidades y servicios del dominio en lugar
de trabajar directamente con los modelos de base de datos.
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime

from ..db.database import get_session
from ..db.domain_repository import SQLChatRepository, SQLFileRepository
from ..agents.groq_client import GroqClient
from ..agents.gemini_client import GeminiClient
from ..agents.prompts import AgentMode, get_system_prompt
from ..config.settings import settings
from ..domain import (
    ChatDomainService,
    FileDomainService,
    AgentDomainService,
    ValidationService,
    ChatSession,
    ChatMessage,
    MessageRole,
    FileDocument,
    FileSection,
    ChatSessionNotFoundError,
    InvalidMessageError,
    FileNotFoundError,
    AgentModeNotSupportedError,
    AIProviderError,
    InsufficientContextError
)


class ChatApplicationService:
    """Servicio de aplicación que orquesta el domain layer."""

    def __init__(self) -> None:
        # Repositorios de infraestructura
        self.chat_repo = SQLChatRepository(get_session())
        self.file_repo = SQLFileRepository(get_session())

        # Servicios de dominio
        self.chat_domain_service = ChatDomainService(self.chat_repo)
        self.file_domain_service = FileDomainService(self.file_repo)
        self.agent_domain_service = AgentDomainService(None)  # TODO: Implementar

        # Clientes de IA
        self.groq_client = GroqClient(None)  # TODO: Inyectar cliente HTTP
        self.gemini_client = GeminiClient(None)  # TODO: Inyectar cliente HTTP

    async def create_new_session(self, user_id: str, session_name: Optional[str] = None) -> ChatSession:
        """Crea una nueva sesión de chat."""
        ValidationService.validate_user_id(user_id)

        return await self.chat_domain_service.create_new_session(user_id, session_name)

    async def handle_chat_message(
        self,
        session_id: int,
        user_id: str,
        user_message: str,
        agent_mode: AgentMode,
        file_id: Optional[int] = None,
        selected_section_ids: Optional[List[int]] = None,
        use_gemini_fallback: Optional[bool] = None,
    ) -> str:
        """Maneja un nuevo mensaje de usuario y retorna la respuesta de la IA."""
        # 1. Validar acceso a la sesión
        session = await self.chat_domain_service.validate_session_access(session_id, user_id)
        if not session:
            raise ChatSessionNotFoundError(session_id)

        # 2. Validar el mensaje del usuario
        ValidationService.validate_message_content(user_message)

        # 3. Agregar mensaje del usuario usando domain service
        user_msg = await self.chat_domain_service.add_message_to_session(
            session_id=session_id,
            user_id=user_id,
            content=user_message,
            role=MessageRole.USER
        )

        # 4. Obtener contexto de la conversación
        context_messages = await self.chat_domain_service.get_conversation_context(
            session_id=session_id,
            user_id=user_id,
            max_messages=settings.conversation_window_messages,
            include_system=True
        )

        # 5. Obtener contexto de archivos si es necesario
        file_context = ""
        if file_id and selected_section_ids:
            file_context = await self._get_file_context(file_id, selected_section_ids)

        # 6. Obtener prompt del sistema para el agente
        try:
            system_prompt = await self.agent_domain_service.get_agent_system_prompt(agent_mode.value)
        except AgentModeNotSupportedError:
            # Fallback al prompt básico
            system_prompt = get_system_prompt(agent_mode)

        # 7. Construir mensajes para la IA
        messages = self._build_ai_messages(system_prompt, context_messages, file_context, user_message)

        # 8. Obtener respuesta de la IA
        ai_response = await self._get_ai_response(messages, agent_mode)

        # 9. Guardar respuesta del asistente
        assistant_msg = await self.chat_domain_service.add_message_to_session(
            session_id=session_id,
            user_id=user_id,
            content=ai_response,
            role=MessageRole.ASSISTANT
        )

        return ai_response

    async def upload_file(
        self,
        filename: str,
        file_path: str,
        file_size: int,
        content_type: str
    ) -> FileDocument:
        """Procesa un archivo subido."""
        return await self.file_domain_service.process_uploaded_file(
            filename_original=filename,
            filename_saved=filename,  # TODO: Generar nombre único
            file_path=file_path,
            file_size=file_size,
            content_type=content_type
        )

    async def add_file_section(
        self,
        file_id: int,
        title: Optional[str],
        start_page: int,
        end_page: int,
        text_content: str
    ) -> FileSection:
        """Agrega una sección a un archivo."""
        return await self.file_domain_service.add_file_section(
            file_id=file_id,
            title=title,
            start_page=start_page,
            end_page=end_page,
            text_content=text_content
        )

    async def get_file_with_sections(self, file_id: int) -> Optional[FileDocument]:
        """Obtiene un archivo con todas sus secciones."""
        return await self.file_domain_service.get_file_with_sections(file_id)

    async def search_file_content(self, file_id: int, query: str) -> List[FileSection]:
        """Busca contenido en un archivo."""
        return await self.file_domain_service.search_file_content(file_id, query)

    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """Obtiene todas las sesiones de un usuario."""
        ValidationService.validate_user_id(user_id)
        return await self.chat_domain_service.get_user_sessions(user_id)

    async def get_session_messages(self, session_id: int, user_id: str) -> List[ChatMessage]:
        """Obtiene los mensajes de una sesión."""
        # Validar acceso
        session = await self.chat_domain_service.validate_session_access(session_id, user_id)
        if not session:
            raise ChatSessionNotFoundError(session_id)

        return await self.chat_domain_service.get_conversation_context(
            session_id=session_id,
            user_id=user_id,
            max_messages=0,  # Sin límite
            include_system=True
        )

    async def _get_file_context(self, file_id: int, selected_section_ids: List[int]) -> str:
        """Obtiene el contexto de un archivo basado en secciones seleccionadas."""
        try:
            file_doc = await self.file_domain_service.get_file_with_sections(file_id)
            if not file_doc:
                raise FileNotFoundError(file_id)

            # Obtener secciones específicas
            context_parts = []
            for section_id in selected_section_ids:
                section = file_doc.get_section(section_id)
                if section and section.has_content():
                    context_parts.append(section.text_content)

            return "\n\n".join(context_parts)

        except Exception as e:
            # Log error pero no fallar completamente
            print(f"Error obteniendo contexto de archivo: {e}")
            return ""

    def _build_ai_messages(
        self,
        system_prompt: str,
        context_messages: List[ChatMessage],
        file_context: str,
        user_message: str
    ) -> List[Dict[str, str]]:
        """Construye los mensajes para enviar a la IA."""
        messages = [{"role": "system", "content": system_prompt}]

        # Agregar contexto de archivo si existe
        if file_context:
            messages.append({
                "role": "system",
                "content": f"Contexto adicional del documento:\n\n{file_context}"
            })

        # Agregar historial de conversación
        for msg in context_messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        # Agregar mensaje actual del usuario
        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    async def _get_ai_response(self, messages: List[Dict[str, str]], agent_mode: AgentMode) -> str:
        """Obtiene la respuesta de la IA."""
        try:
            # TODO: Implementar lógica de selección de proveedor
            # Por ahora usar Groq como principal
            response = await self.groq_client.get_chat_completion(
                system_prompt="",  # Ya incluido en messages
                messages=messages  # TODO: Convertir a ChatMessage objects
            )

            return response

        except Exception as e:
            # TODO: Implementar fallback a Gemini
            raise AIProviderError("groq", str(e))
