"""
Factory de inyección de dependencias para arquitectura hexagonal.

Este módulo crea las instancias de servicios con sus dependencias
inyectadas, siguiendo el patrón de Dependency Injection.
"""

from __future__ import annotations

from functools import lru_cache

import httpx
from sqlmodel import Session

from src.domain.ports import LLMPort, ChatRepositoryPort
from src.adapters.agents.groq_adapter import GroqAdapter
from src.adapters.agents.gemini_adapter import GeminiAdapter
from src.adapters.db.chat_repository_adapter import SQLChatRepositoryAdapter
from src.application.services.chat_service_v2 import ChatServiceV2
from src.adapters.db.database import get_session


# ============================================================================
# HTTP Client (compartido)
# ============================================================================

@lru_cache()
def get_http_client() -> httpx.AsyncClient:
    """
    Obtiene un cliente HTTP compartido.
    
    Returns:
        Cliente HTTP asíncrono
    """
    return httpx.AsyncClient()


# ============================================================================
# Adaptadores de LLM
# ============================================================================

def get_groq_adapter() -> LLMPort:
    """
    Crea un adaptador de Groq (Kimi-K2).
    
    Returns:
        Adaptador de Groq que implementa LLMPort
    """
    client = get_http_client()
    return GroqAdapter(client)


def get_gemini_adapter() -> LLMPort:
    """
    Crea un adaptador de Gemini.
    
    Returns:
        Adaptador de Gemini que implementa LLMPort
    """
    client = get_http_client()
    return GeminiAdapter(client)


# ============================================================================
# Adaptadores de Repositorio
# ============================================================================

def get_chat_repository(session: Session) -> ChatRepositoryPort:
    """
    Crea un adaptador de repositorio de chat.
    
    Args:
        session: Sesión de SQLModel
        
    Returns:
        Adaptador de repositorio que implementa ChatRepositoryPort
    """
    return SQLChatRepositoryAdapter(session)


# ============================================================================
# Servicios de Aplicación
# ============================================================================

def get_chat_service(session: Session) -> ChatServiceV2:
    """
    Crea el servicio de chat con todas sus dependencias inyectadas.
    
    Args:
        session: Sesión de SQLModel
        
    Returns:
        Servicio de chat configurado
    """
    # Crear adaptadores
    llm_client = get_groq_adapter()
    fallback_llm = get_gemini_adapter()
    repository = get_chat_repository(session)
    
    # Crear servicio con dependencias inyectadas
    return ChatServiceV2(
        llm_client=llm_client,
        repository=repository,
        fallback_llm=fallback_llm,
    )


# ============================================================================
# Dependencias para FastAPI
# ============================================================================

def get_chat_service_dependency(
    session: Session = get_session(),  # type: ignore[misc]
) -> ChatServiceV2:
    """
    Dependencia de FastAPI para obtener el servicio de chat.
    
    Uso en endpoints:
    ```python
    @router.post("/chat")
    async def chat_endpoint(
        service: ChatServiceV2 = Depends(get_chat_service_dependency)
    ):
        ...
    ```
    
    Args:
        session: Sesión de base de datos (inyectada por FastAPI)
        
    Returns:
        Servicio de chat configurado
    """
    return get_chat_service(session)
