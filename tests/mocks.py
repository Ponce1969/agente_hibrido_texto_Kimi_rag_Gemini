"""Mocks para testing de servicios."""
from typing import Any, Dict, List, Tuple
from src.domain.ports import LLMPort, ChatRepositoryPort
from src.domain.models import ChatSession, ChatMessage


class MockLLMPort(LLMPort):
    """Mock del adaptador LLM para testing."""
    
    def __init__(self):
        self.response = "Mock response"
        self.tokens_used = 100
    
    async def get_chat_completion(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any
    ) -> Tuple[str, int]:
        return self.response, self.tokens_used

    async def get_chat_completion_stream(self, *args, **kwargs):
        yield self.response

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4


class MockRepositoryPort(ChatRepositoryPort):
    """Mock del repositorio para testing."""
    
    def __init__(self):
        self.sessions = {}
        self.messages = {}
    
    def create_session(self, session_data) -> ChatSession:
        session = ChatSession(
            id="test-session-1",
            user_id=session_data.user_id,
            title=session_data.title,
            created_at="2024-01-01T00:00:00Z"
        )
        self.sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> ChatSession | None:
        return self.sessions.get(session_id)
    
    def list_sessions(self, limit: int = 50) -> List[ChatSession]:
        return list(self.sessions.values())[:limit]
    
    def add_message(self, message_data) -> ChatMessage:
        message = ChatMessage(
            id=f"msg-{len(self.messages) + 1}",
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content,
            created_at="2024-01-01T00:00:00Z"
        )
        if message_data.session_id not in self.messages:
            self.messages[message_data.session_id] = []
        self.messages[message_data.session_id].append(message)
        return message
    
    def get_session_messages(self, session_id: str, *, limit: int | None = None) -> list[ChatMessage]:
        messages = self.messages.get(session_id, [])
        if limit:
            return messages[-limit:]
        return messages

    def update_session(self, session_id: str, *, title: str | None = None) -> ChatSession:
        session = self.sessions[session_id]
        if title:
            session.title = title
        return session

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_message(self, message_id: int) -> ChatMessage | None:
        for msg_list in self.messages.values():
            for msg in msg_list:
                if msg.id == str(message_id):
                    return msg
        return None

    def count_session_messages(self, session_id: str) -> int:
        return len(self.messages.get(session_id, []))
