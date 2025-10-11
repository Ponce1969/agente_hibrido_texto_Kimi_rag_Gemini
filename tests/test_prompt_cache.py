"""
Tests para el sistema de caché de prompts y reducción de tokens.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.domain.models.chat_models import ChatSession
from src.application.services.chat_service import ChatServiceV2
from src.domain.ports import LLMPort

@pytest.mark.unit
class TestChatServiceCache:
    """Tests para la lógica de caché dentro de ChatServiceV2."""

    @pytest.mark.asyncio
    async def test_cache_is_used_on_second_call(self):
        """Verifica que el caché se use en la segunda llamada con la misma query."""
        mock_llm = AsyncMock(spec=LLMPort)
        mock_llm.get_chat_completion.return_value = ("Respuesta cacheable", 100)

        mock_repo = AsyncMock()
        mock_repo.get_session.return_value = ChatSession(user_id="test_user")
        mock_repo.get_session_messages.return_value = []

        service = ChatServiceV2(llm_client=mock_llm, repository=mock_repo)

        # Primera llamada (debería llamar al LLM)
        await service.handle_message(session_id="1", user_message="Pregunta para cachear")

        # Segunda llamada (debería usar el caché)
        await service.handle_message(session_id="1", user_message="Pregunta para cachear")

        # El mock del LLM no implementa caché, pero el servicio debe solicitarlo.
        # Verificamos que se llamó dos veces, y en ambas se pidió usar el caché.
        assert mock_llm.get_chat_completion.call_count == 2
        for call in mock_llm.get_chat_completion.call_args_list:
            assert call.kwargs.get('use_cache') is True
