"""
Tests para validar la arquitectura hexagonal del Día 2.

Valida:
- Adaptadores implementan puertos correctamente
- ChatServiceV2 usa solo puertos
- Inyección de dependencias funciona
- No hay violaciones de arquitectura
"""

import pytest
from unittest.mock import AsyncMock, Mock

from src.domain.ports import LLMPort, ChatRepositoryPort
from src.domain.models import (
    ChatSession,
    ChatMessage,
    MessageRole,
    ChatSessionCreate,
    ChatMessageCreate,
)
from src.application.services.chat_service_v2 import ChatServiceV2


class MockLLMPort(LLMPort):
    """Mock del puerto LLM para testing."""
    
    def __init__(self, response: str = "Mock response") -> None:
        self.response = response
        self.call_count = 0
    
    async def get_chat_completion(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        session_id: str | None = None,
        agent_mode: str | None = None,
        use_cache: bool = True,
    ) -> tuple[str, int | None]:
        self.call_count += 1
        return self.response, 100
    
    async def get_chat_completion_stream(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        return self.response
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4


class MockRepositoryPort(ChatRepositoryPort):
    """Mock del puerto de repositorio para testing."""
    
    def __init__(self) -> None:
        self.sessions: dict[str, ChatSession] = {}
        self.messages: dict[str, list[ChatMessage]] = {}
        self.message_counter = 0
    
    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        from datetime import datetime
        
        session = ChatSession(
            user_id=session_data.user_id,
            session_name=session_data.title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session_id = "test_session_1"
        self.sessions[session_id] = session
        self.messages[session_id] = []
        return session
    
    def get_session(self, session_id: str) -> ChatSession | None:
        return self.sessions.get(session_id)
    
    def list_sessions(self, *, limit: int = 50, offset: int = 0) -> list[ChatSession]:
        return list(self.sessions.values())
    
    def update_session(self, session_id: str, *, title: str | None = None) -> ChatSession:
        session = self.sessions[session_id]
        if title:
            session.session_name = title
        return session
    
    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            del self.messages[session_id]
            return True
        return False
    
    def add_message(self, message_data: ChatMessageCreate) -> ChatMessage:
        from datetime import datetime
        
        self.message_counter += 1
        # session_id puede ser string o int, manejamos ambos
        try:
            session_id_int = int(message_data.session_id)
        except ValueError:
            session_id_int = 1  # Default para tests
        
        message = ChatMessage(
            session_id=session_id_int,
            role=message_data.role,
            content=message_data.content,
            timestamp=datetime.utcnow(),
            message_index=self.message_counter,
        )
        
        if message_data.session_id not in self.messages:
            self.messages[message_data.session_id] = []
        
        self.messages[message_data.session_id].append(message)
        return message
    
    def get_session_messages(
        self,
        session_id: str,
        *,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        messages = self.messages.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages
    
    def get_message(self, message_id: int) -> ChatMessage | None:
        for messages in self.messages.values():
            for msg in messages:
                if msg.message_index == message_id:
                    return msg
        return None
    
    def count_session_messages(self, session_id: str) -> int:
        return len(self.messages.get(session_id, []))


class TestChatServiceV2:
    """Tests para ChatServiceV2 con arquitectura hexagonal."""
    
    def test_service_creation(self) -> None:
        """Test que el servicio se crea correctamente."""
        mock_llm = MockLLMPort()
        mock_repo = MockRepositoryPort()
        
        service = ChatServiceV2(
            llm_client=mock_llm,
            repository=mock_repo,
        )
        
        assert service.llm == mock_llm
        assert service.repo == mock_repo
    
    def test_create_session(self) -> None:
        """Test crear una sesión."""
        mock_llm = MockLLMPort()
        mock_repo = MockRepositoryPort()
        service = ChatServiceV2(mock_llm, mock_repo)
        
        session_data = ChatSessionCreate(
            title="Test Session",
            user_id="test_user",
        )
        
        session = service.create_session(session_data)
        
        assert session is not None
        assert session.user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_handle_message(self) -> None:
        """Test manejar un mensaje del usuario."""
        mock_llm = MockLLMPort(response="Test response from LLM")
        mock_repo = MockRepositoryPort()
        service = ChatServiceV2(mock_llm, mock_repo)
        
        # Crear sesión
        session_data = ChatSessionCreate(title="Test", user_id="user1")
        session = service.create_session(session_data)
        session_id = "test_session_1"
        
        # Manejar mensaje
        response = await service.handle_message(
            session_id=session_id,
            user_message="Hello, how are you?",
            agent_mode="architect",
        )
        
        assert response == "Test response from LLM"
        assert mock_llm.call_count == 1
        
        # Verificar que se guardaron los mensajes
        messages = mock_repo.get_session_messages(session_id)
        assert len(messages) == 2  # user + assistant
        assert messages[0].role == MessageRole.USER
        assert messages[1].role == MessageRole.ASSISTANT
    
    @pytest.mark.asyncio
    async def test_fallback_llm(self) -> None:
        """Test que el fallback LLM funciona."""
        # LLM principal que falla
        mock_llm = MockLLMPort()
        mock_llm.get_chat_completion = AsyncMock(side_effect=Exception("API Error"))
        
        # LLM de respaldo
        fallback_llm = MockLLMPort(response="Fallback response")
        
        mock_repo = MockRepositoryPort()
        service = ChatServiceV2(mock_llm, mock_repo, fallback_llm=fallback_llm)
        
        # Crear sesión
        session_data = ChatSessionCreate(title="Test", user_id="user1")
        service.create_session(session_data)
        
        # Manejar mensaje (debería usar fallback)
        response = await service.handle_message(
            session_id="test_session_1",
            user_message="Test message",
            use_fallback_on_error=True,
        )
        
        assert response == "Fallback response"


class TestAdapters:
    """Tests para verificar que los adaptadores funcionan."""
    
    def test_groq_adapter_import(self) -> None:
        """Test que GroqAdapter se puede importar."""
        from src.adapters.agents.groq_adapter import GroqAdapter
        assert GroqAdapter is not None
    
    def test_gemini_adapter_import(self) -> None:
        """Test que GeminiAdapter se puede importar."""
        from src.adapters.agents.gemini_adapter import GeminiAdapter
        assert GeminiAdapter is not None
    
    def test_repository_adapter_import(self) -> None:
        """Test que SQLChatRepositoryAdapter se puede importar."""
        from src.adapters.db.chat_repository_adapter import SQLChatRepositoryAdapter
        assert SQLChatRepositoryAdapter is not None


class TestDependencies:
    """Tests para el sistema de inyección de dependencias."""
    
    def test_dependencies_import(self) -> None:
        """Test que el módulo de dependencies se puede importar."""
        from src.adapters import dependencies
        assert dependencies is not None
    
    def test_get_groq_adapter(self) -> None:
        """Test que se puede crear un GroqAdapter."""
        from src.adapters.dependencies import get_groq_adapter
        
        adapter = get_groq_adapter()
        assert adapter is not None
        assert hasattr(adapter, 'get_chat_completion')
    
    def test_get_gemini_adapter(self) -> None:
        """Test que se puede crear un GeminiAdapter."""
        from src.adapters.dependencies import get_gemini_adapter
        
        adapter = get_gemini_adapter()
        assert adapter is not None
        assert hasattr(adapter, 'get_chat_completion')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
