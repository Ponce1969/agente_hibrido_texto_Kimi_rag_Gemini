"""
Tests del servicio de chat.
Verifica que el chat funcione correctamente con y sin RAG.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.application.services.chat_service import ChatServiceV2
from src.domain.models.chat_models import MessageRole, ChatSession, ChatMessage, ChatSessionCreate, ChatMessageCreate


@pytest.mark.unit
class TestChatServiceBasic:
    """Tests básicos del servicio de chat."""

    @pytest.mark.asyncio
    async def test_chat_without_rag(self):
        """Verifica que el chat funcione sin RAG (modo normal)."""
        mock_llm = AsyncMock()
        mock_llm.get_chat_completion.return_value = ("Respuesta de prueba", 50)

        mock_repo = AsyncMock()
        mock_session = ChatSession(user_id="test")
        mock_session.id = 1
        mock_repo.get_session.return_value = mock_session
        mock_repo.get_session_messages.return_value = []

        service = ChatServiceV2(llm_client=mock_llm, repository=mock_repo)

        response = await service.handle_message(session_id="1", user_message="Hola")
        
        assert response == "Respuesta de prueba"
        mock_llm.get_chat_completion.assert_called_once()
        mock_repo.add_message.assert_called()

    @pytest.mark.asyncio
    async def test_chat_with_rag(self, sample_chunks):
        """Verifica que el chat funcione con RAG activado."""
        mock_fallback_llm = AsyncMock()
        mock_fallback_llm.get_chat_completion.return_value = ("Respuesta con RAG", 150)

        mock_repo = AsyncMock()
        mock_session = ChatSession(user_id="test")
        mock_session.id = 1
        mock_repo.get_session.return_value = mock_session
        mock_repo.get_session_messages.return_value = []

        mock_embeddings_service = AsyncMock()
        mock_embeddings_service.search_similar.return_value = sample_chunks

        service = ChatServiceV2(
            llm_client=AsyncMock(),
            repository=mock_repo,
            fallback_llm=mock_fallback_llm,
            embeddings_service=mock_embeddings_service
        )

        response = await service.handle_message(session_id="1", user_message="Test", file_id=1)
        
        assert response == "Respuesta con RAG"
        mock_fallback_llm.get_chat_completion.assert_called_once()
        mock_embeddings_service.search_similar.assert_called_once()


@pytest.mark.unit
class TestChatServiceErrorHandling:
    """Tests de manejo de errores."""

    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self):
        """Verifica que maneje errores de API correctamente."""
        mock_llm = AsyncMock()
        mock_llm.get_chat_completion.side_effect = Exception("API Error")

        mock_repo = AsyncMock()
        mock_session = ChatSession(user_id="test")
        mock_session.id = 1
        mock_repo.get_session.return_value = mock_session
        mock_repo.get_session_messages.return_value = []

        service = ChatServiceV2(llm_client=mock_llm, repository=mock_repo)

        with pytest.raises(Exception, match="API Error"):
            await service.handle_message(session_id="1", user_message="test")
