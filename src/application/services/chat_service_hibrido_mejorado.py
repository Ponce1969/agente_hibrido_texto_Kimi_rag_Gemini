"""
ChatServiceHibrido REFACTORIZADO - Versión limpia.
"""

import logging
from typing import Any

from src.application.services.chat_service import ChatServiceV2
from src.application.services.rag.query_service import RagQueryService
from src.application.services.rag_context_service import RagContextService

logger = logging.getLogger(__name__)


class ChatServiceHibridoRefactorizado(ChatServiceV2):
    def __init__(
        self,
        *args: Any,
        embeddings_repo: Any | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.rag_context_service: RagContextService | None = None
        self.rag_query_service: RagQueryService | None = None

        if self.document_mapper and hasattr(self.document_mapper, "file_repository"):
            self.rag_context_service = RagContextService(
                file_repository=self.document_mapper.file_repository
            )

        if self.embeddings and self.fallback_llm and embeddings_repo:
            self.rag_query_service = RagQueryService(
                embeddings_repository=embeddings_repo, gemini_adapter=self.fallback_llm
            )

    async def handle_message(
        self,
        session_id: str,
        user_message: str,
        *,
        agent_mode: str = "architect",
        file_id: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Versión refactorizada con contexto RAG"""

        # 1. Resolver referencia a documento (ID:5, este PDF, etc.)
        resolved_file_id = await self._resolve_file_id_with_context(
            session_id, user_message, file_id
        )

        # 2. Si hay documento, usar RAG
        if resolved_file_id and self.rag_context_service and self.rag_query_service:
            logger.info(f"📚 Usando RAG con file_id={resolved_file_id}")

            # Actualizar contexto
            self.rag_context_service.set_current_file_id(session_id, resolved_file_id)

            # Ejecutar RAG
            return await self.rag_query_service.query_rag(
                query=user_message, file_id=resolved_file_id, session_id=session_id
            )

        # 3. Si no hay documento, routing normal
        return await super().handle_message(
            session_id=session_id,
            user_message=user_message,
            agent_mode=agent_mode,
            file_id=None,
            **kwargs,
        )

    async def _resolve_file_id_with_context(
        self, session_id: str, user_message: str, explicit_file_id: int | None
    ) -> int | None:
        """Resuelve file_id usando contexto y referencias"""

        # Prioridad 1: file_id explícito
        if explicit_file_id:
            return explicit_file_id

        if not self.rag_context_service:
            return None

        # Prioridad 2: Referencia en el mensaje (ID:5, este PDF)
        referenced_file_id = await self.rag_context_service.resolve_file_reference(
            session_id, user_message
        )

        if referenced_file_id:
            return referenced_file_id

        # Prioridad 3: file_id actual de la sesión
        current_file_id = self.rag_context_service.get_current_file_id(session_id)
        if current_file_id:
            if self._is_document_related_query(user_message):
                return current_file_id

        return None

    def _is_document_related_query(self, query: str) -> bool:
        """Determina si la query está relacionada con el documento actual"""
        doc_keywords = ["documento", "pdf", "libro", "capítulo", "sección", "página"]
        return any(keyword in query.lower() for keyword in doc_keywords)

    async def get_system_status(self) -> dict[str, Any]:
        """
        Retorna el estado de todos los modelos disponibles.

        Útil para dashboard y diagnóstico.
        """
        return {
            "kimi_k2": {"available": True, "type": "cloud"},
            "gemini": {"available": bool(self.fallback_llm), "type": "cloud"},
            "routing_enabled": True,
        }
