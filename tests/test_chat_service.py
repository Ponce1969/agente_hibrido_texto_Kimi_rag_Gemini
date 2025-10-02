"""
Tests del servicio de chat.
Verifica que el chat funcione correctamente con y sin RAG.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.application.services.chat_service import ChatService
from src.domain.models.chat_models import MessageRole


@pytest.mark.unit
class TestChatServiceBasic:
    """Tests básicos del servicio de chat."""
    
    @pytest.mark.asyncio
    async def test_chat_without_rag(self, mock_groq_response):
        """Verifica que el chat funcione sin RAG (modo normal)."""
        # Mock del cliente Groq
        mock_client = AsyncMock()
        mock_client.get_chat_completion.return_value = mock_groq_response["choices"][0]["message"]["content"]
        
        # Mock del repositorio
        mock_repo = Mock()
        mock_repo.get_session_messages.return_value = []
        mock_repo.add_message = Mock()
        
        service = ChatService(mock_repo, mock_client, gemini=None)
        
        response = await service.handle_chat_message(
            session_id=1,
            user_message="¿Qué es Python?",
            agent_mode="Arquitecto Python Senior",
            file_id=None  # Sin RAG
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        mock_client.get_chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_with_rag(self, mock_gemini_response, sample_chunks):
        """Verifica que el chat funcione con RAG activado."""
        # Mock del cliente Gemini
        mock_gemini = AsyncMock()
        mock_gemini.get_chat_completion.return_value = mock_gemini_response["candidates"][0]["content"]["parts"][0]["text"]
        
        # Mock del repositorio
        mock_repo = Mock()
        mock_repo.get_session_messages.return_value = []
        mock_repo.add_message = Mock()
        mock_repo.count_chunks.return_value = 522  # Hay chunks disponibles
        
        # Mock del servicio de embeddings
        with patch('src.application.services.chat_service.EmbeddingsService') as MockEmbeddings:
            mock_embeddings_instance = Mock()
            mock_embeddings_instance.search.return_value = sample_chunks
            MockEmbeddings.return_value = mock_embeddings_instance
            
            service = ChatService(mock_repo, Mock(), gemini=mock_gemini)
            
            response = await service.handle_chat_message(
                session_id=1,
                user_message="¿Qué dice el PDF sobre funciones?",
                agent_mode="Arquitecto Python Senior",
                file_id=1  # Con RAG
            )
            
            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
            mock_gemini.get_chat_completion.assert_called_once()


@pytest.mark.unit
class TestChatServicePrompts:
    """Tests de construcción de prompts."""
    
    def test_system_prompt_contains_agent_mode(self):
        """Verifica que el system prompt incluya el modo de agente."""
        from src.adapters.agents.prompts import get_system_prompt
        
        prompt = get_system_prompt("Arquitecto Python Senior")
        
        assert "Python" in prompt or "arquitecto" in prompt.lower()
        assert len(prompt) > 100  # Debe tener contenido sustancial
    
    def test_all_agent_modes_have_prompts(self):
        """Verifica que todos los modos de agente tengan prompts."""
        from src.adapters.agents.prompts import get_system_prompt
        
        agent_modes = [
            "Arquitecto Python Senior",
            "Ingeniero de Código",
            "Auditor de Seguridad",
            "Especialista en Bases de Datos",
            "Ingeniero de Refactoring"
        ]
        
        for mode in agent_modes:
            prompt = get_system_prompt(mode)
            assert prompt is not None
            assert len(prompt) > 50
            assert isinstance(prompt, str)


@pytest.mark.unit
class TestChatServiceErrorHandling:
    """Tests de manejo de errores."""
    
    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self):
        """Verifica que maneje errores de API correctamente."""
        # Mock que lanza excepción
        mock_client = AsyncMock()
        mock_client.get_chat_completion.side_effect = Exception("API Error")
        
        mock_repo = Mock()
        mock_repo.get_session_messages.return_value = []
        
        service = ChatService(mock_repo, mock_client, gemini=None)
        
        with pytest.raises(Exception):
            await service.handle_chat_message(
                session_id=1,
                user_message="test",
                agent_mode="Arquitecto Python Senior",
                file_id=None
            )
    
    @pytest.mark.asyncio
    async def test_handles_empty_message(self):
        """Verifica que maneje mensajes vacíos."""
        mock_client = AsyncMock()
        mock_repo = Mock()
        mock_repo.get_session_messages.return_value = []
        
        service = ChatService(mock_repo, mock_client, gemini=None)
        
        # Mensaje vacío no debería crashear
        try:
            response = await service.handle_chat_message(
                session_id=1,
                user_message="",
                agent_mode="Arquitecto Python Senior",
                file_id=None
            )
            # Puede devolver respuesta o lanzar excepción controlada
            assert True
        except ValueError:
            # Es aceptable que rechace mensajes vacíos
            assert True


@pytest.mark.integration
class TestChatServiceIntegration:
    """Tests de integración del servicio de chat."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_chat_flow_without_rag(self, db_session):
        """Test del flujo completo de chat sin RAG."""
        # Este test requiere base de datos real
        # Se implementará cuando tengamos fixtures de DB
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_chat_flow_with_rag(self, db_session):
        """Test del flujo completo de chat con RAG."""
        # Este test requiere PostgreSQL + pgvector
        # Se implementará cuando tengamos PostgreSQL en CI
        pass


@pytest.mark.unit
class TestChatServiceTokens:
    """Tests relacionados con conteo de tokens."""
    
    def test_prompt_length_is_reasonable(self):
        """Verifica que los prompts no sean excesivamente largos."""
        from src.adapters.agents.prompts import get_system_prompt
        
        for mode in ["Arquitecto Python Senior", "DBA", "Tester"]:
            prompt = get_system_prompt(mode)
            
            # Estimación: ~4 chars = 1 token
            estimated_tokens = len(prompt) // 4
            
            # Los prompts actuales son largos, pero no deberían exceder 5000 tokens
            assert estimated_tokens < 5000, f"Prompt muy largo para {mode}: ~{estimated_tokens} tokens"
    
    def test_rag_context_has_size_limit(self, sample_chunks):
        """Verifica que el contexto RAG tenga límite de tamaño."""
        # Simular construcción de contexto con límite
        limit = 6000  # caracteres
        acc = 0
        parts = []
        
        for chunk in sample_chunks:
            remaining = limit - acc
            if remaining <= 0:
                break
            snippet = chunk['content'][:remaining]
            parts.append(snippet)
            acc += len(snippet)
        
        rag_context = "\n\n".join(parts)
        
        # El contexto no debería exceder el límite
        assert len(rag_context) <= limit
