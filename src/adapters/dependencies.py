"""
Factory de inyección de dependencias para arquitectura hexagonal.

Este módulo crea las instancias de servicios con sus dependencias
inyectadas, siguiendo el patrón de Dependency Injection.
"""

from __future__ import annotations

from functools import lru_cache

import httpx
from fastapi import Depends
from sqlmodel import Session

from src.domain.ports import LLMPort, ChatRepositoryPort, EmbeddingsPort
from src.adapters.agents.groq_adapter import GroqAdapter
from src.adapters.agents.gemini_adapter import GeminiAdapter
from src.adapters.agents.gemini_embeddings_adapter import GeminiEmbeddingsAdapter
from src.adapters.db.chat_repository_adapter import SQLChatRepositoryAdapter
from src.application.services.chat_service import ChatServiceV2
from src.application.services.embeddings_service import EmbeddingsServiceV2
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
    embeddings_svc = get_embeddings_service()
    
    # Crear servicio con dependencias inyectadas
    return ChatServiceV2(
        llm_client=llm_client,
        repository=repository,
        fallback_llm=fallback_llm,
        embeddings_service=embeddings_svc,
    )


# ============================================================================
# Dependencias para FastAPI
# ============================================================================

def get_chat_service_dependency(
    session: Session = Depends(get_session),
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


# ============================================================================
# Adaptadores de Embeddings
# ============================================================================

def get_gemini_embeddings_adapter() -> EmbeddingsPort:
    """
    Crea un adaptador de Gemini Embeddings.
    
    Returns:
        Adaptador de Gemini Embeddings que implementa EmbeddingsPort
    """
    client = get_http_client()
    return GeminiEmbeddingsAdapter(client)


# ============================================================================
# Servicio de Embeddings
# ============================================================================

def get_embeddings_service() -> EmbeddingsServiceV2:
    """
    Crea el servicio de embeddings con todas sus dependencias inyectadas.
    
    Returns:
        Servicio de embeddings configurado
    """
    # Crear adaptador de embeddings
    embeddings_client = get_gemini_embeddings_adapter()
    
    # Crear servicio con dependencias inyectadas
    return EmbeddingsServiceV2(
        embeddings_client=embeddings_client,
    )


def get_embeddings_service_dependency() -> EmbeddingsServiceV2:
    """
    Dependencia de FastAPI para obtener el servicio de embeddings.
    
    Uso en endpoints:
    ```python
    @router.post("/index")
    async def index_endpoint(
        service: EmbeddingsServiceV2 = Depends(get_embeddings_service_dependency)
    ):
        ...
    ```
    
    Returns:
        Servicio de embeddings configurado
    """
    return get_embeddings_service()
