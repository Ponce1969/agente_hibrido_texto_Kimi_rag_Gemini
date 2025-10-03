"""
Tests para el sistema de caché de prompts y reducción de tokens.
"""

import pytest
from src.adapters.agents.prompt_manager import PromptManager, TokenMetrics
from src.adapters.agents.prompts import AgentMode
from src.adapters.db.message import ChatMessage, MessageRole


class TestPromptManager:
    """Tests para el gestor de prompts con caché."""
    
    def test_first_call_returns_full_prompt(self):
        """Primera llamada debe retornar el prompt completo."""
        manager = PromptManager()
        session_id = "test_session_1"
        
        prompt, is_cached = manager.get_prompt(
            session_id=session_id,
            agent_mode=AgentMode.PYTHON_ARCHITECT
        )
        
        assert is_cached is False
        assert len(prompt) > 500  # Prompt completo es largo
        assert "Arquitecto Python Senior" in prompt
    
    def test_subsequent_calls_return_cached_reference(self):
        """Llamadas subsecuentes deben retornar referencia corta."""
        manager = PromptManager()
        session_id = "test_session_2"
        
        # Primera llamada
        prompt1, is_cached1 = manager.get_prompt(
            session_id=session_id,
            agent_mode=AgentMode.PYTHON_ARCHITECT
        )
        
        # Segunda llamada
        prompt2, is_cached2 = manager.get_prompt(
            session_id=session_id,
            agent_mode=AgentMode.PYTHON_ARCHITECT
        )
        
        assert is_cached1 is False
        assert is_cached2 is True
        assert len(prompt2) < len(prompt1)  # Referencia es más corta
        assert len(prompt2) < 500  # Referencia corta
    
    def test_different_sessions_have_independent_cache(self):
        """Sesiones diferentes deben tener caché independiente."""
        manager = PromptManager()
        
        # Sesión 1
        prompt1, cached1 = manager.get_prompt("session_1", AgentMode.CODE_GENERATOR)
        
        # Sesión 2 (primera llamada)
        prompt2, cached2 = manager.get_prompt("session_2", AgentMode.CODE_GENERATOR)
        
        assert cached1 is False
        assert cached2 is False  # Nueva sesión, no está cacheada
    
    def test_history_limiting(self):
        """El historial debe limitarse a MAX_HISTORY_MESSAGES."""
        manager = PromptManager()
        
        # Crear 10 mensajes
        messages = [
            ChatMessage(
                id=i,
                session_id="test",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}",
                message_index=i
            )
            for i in range(10)
        ]
        
        limited = manager.limit_history(messages)
        
        assert len(limited) == manager.MAX_HISTORY_MESSAGES
        assert limited[-1].content == "Message 9"  # Último mensaje
    
    def test_token_estimation(self):
        """Estimación de tokens debe ser aproximadamente correcta."""
        manager = PromptManager()
        
        # ~400 caracteres = ~100 tokens
        text = "a" * 400
        tokens = manager.estimate_tokens(text)
        
        assert 90 <= tokens <= 110  # Aproximadamente 100 tokens
    
    def test_metrics_recording(self):
        """Las métricas deben registrarse correctamente."""
        manager = PromptManager()
        session_id = "metrics_test"
        
        messages = [
            ChatMessage(
                id=1,
                session_id=session_id,
                role=MessageRole.USER,
                content="Test message",
                message_index=0
            )
        ]
        
        metrics = manager.record_metrics(
            session_id=session_id,
            system_prompt="Test prompt",
            history=messages,
            user_message="User input",
            is_cached=False
        )
        
        assert isinstance(metrics, TokenMetrics)
        assert metrics.session_id == session_id
        assert metrics.total_tokens > 0
        assert metrics.is_cached is False
    
    def test_session_stats_calculation(self):
        """Estadísticas de sesión deben calcularse correctamente."""
        manager = PromptManager()
        session_id = "stats_test"
        
        # Simular 3 llamadas
        for i in range(3):
            prompt, is_cached = manager.get_prompt(session_id, AgentMode.PYTHON_ARCHITECT)
            manager.record_metrics(
                session_id=session_id,
                system_prompt=prompt,
                history=[],
                user_message="test",
                is_cached=is_cached
            )
        
        stats = manager.get_session_stats(session_id)
        
        assert stats["total_calls"] == 3
        assert stats["total_tokens"] > 0
        assert stats["tokens_saved"] > 0  # Debe haber ahorro
    
    def test_cache_clearing(self):
        """Limpiar caché debe funcionar correctamente."""
        manager = PromptManager()
        session_id = "clear_test"
        
        # Primera llamada
        manager.get_prompt(session_id, AgentMode.REFACTOR_ENGINEER)
        
        # Limpiar caché
        manager.clear_session_cache(session_id)
        
        # Siguiente llamada debe ser como primera vez
        prompt, is_cached = manager.get_prompt(session_id, AgentMode.REFACTOR_ENGINEER)
        
        assert is_cached is False  # No está cacheado después de limpiar
    
    def test_global_stats(self):
        """Estadísticas globales deben incluir todas las sesiones."""
        manager = PromptManager()
        
        # Crear múltiples sesiones
        for i in range(3):
            session_id = f"global_test_{i}"
            prompt, is_cached = manager.get_prompt(session_id, AgentMode.DATABASE_SPECIALIST)
            manager.record_metrics(
                session_id=session_id,
                system_prompt=prompt,
                history=[],
                user_message="test",
                is_cached=is_cached
            )
        
        stats = manager.get_global_stats()
        
        assert stats["total_sessions"] == 3
        assert stats["total_calls"] == 3
        assert stats["total_tokens"] > 0


class TestPromptReferences:
    """Tests para las referencias cortas de prompts."""
    
    def test_all_agent_modes_have_references(self):
        """Todos los modos de agente deben tener referencia corta."""
        manager = PromptManager()
        
        for mode in AgentMode:
            ref = manager._create_short_reference(mode)
            assert len(ref) > 0
            assert len(ref) < 500  # Referencia corta
    
    def test_reference_contains_key_info(self):
        """Referencia debe contener información clave del rol."""
        manager = PromptManager()
        
        ref = manager._create_short_reference(AgentMode.PYTHON_ARCHITECT)
        
        assert "SoftwareArchitect" in ref or "Architect" in ref
        assert "Python" in ref
    
    def test_token_savings_calculation(self):
        """Cálculo de ahorro de tokens debe ser correcto."""
        manager = PromptManager()
        session_id = "savings_test"
        
        # Primera llamada (prompt completo)
        prompt1, _ = manager.get_prompt(session_id, AgentMode.SECURITY_ANALYST)
        tokens1 = manager.estimate_tokens(prompt1)
        
        # Segunda llamada (referencia)
        prompt2, _ = manager.get_prompt(session_id, AgentMode.SECURITY_ANALYST)
        tokens2 = manager.estimate_tokens(prompt2)
        
        # Debe haber ahorro significativo
        savings = tokens1 - tokens2
        savings_pct = (savings / tokens1) * 100
        
        assert savings > 0
        assert savings_pct > 50  # Al menos 50% de ahorro


@pytest.mark.asyncio
class TestIntegrationWithGroqClient:
    """Tests de integración con GroqClient."""
    
    async def test_cache_integration(self):
        """Test de integración del caché con GroqClient."""
        from src.adapters.agents.groq_client import GroqClient
        from unittest.mock import AsyncMock, Mock
        import httpx
        
        # Mock del cliente HTTP
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_client.post.return_value = mock_response
        
        groq_client = GroqClient(mock_client)
        
        messages = [
            ChatMessage(
                id=1,
                session_id="integration_test",
                role=MessageRole.USER,
                content="Test",
                message_index=0
            )
        ]
        
        # Primera llamada
        response1, metrics1 = await groq_client.get_chat_completion(
            system_prompt="test",
            messages=messages,
            session_id="integration_test",
            agent_mode=AgentMode.CODE_GENERATOR,
            use_cache=True
        )
        
        assert metrics1 is not None
        assert metrics1.is_cached is False
        
        # Segunda llamada
        response2, metrics2 = await groq_client.get_chat_completion(
            system_prompt="test",
            messages=messages,
            session_id="integration_test",
            agent_mode=AgentMode.CODE_GENERATOR,
            use_cache=True
        )
        
        assert metrics2 is not None
        assert metrics2.is_cached is True
        assert metrics2.total_tokens < metrics1.total_tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
