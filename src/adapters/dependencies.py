"""
Factory de inyección de dependencias para arquitectura hexagonal.

Este módulo crea las instancias de servicios con sus dependencias
inyectadas, siguiendo el patrón de Dependency Injection.
"""

from __future__ import annotations

from functools import lru_cache
from fastapi import Depends
import httpx

from sqlmodel import Session

from src.domain.ports import (ChatRepositoryPort, EmbeddingsPort, LLMPort, 
                              FileRepositoryPort, PythonSearchPort)
                              
from src.adapters.agents.gemini_adapter import GeminiAdapter
from src.adapters.agents.gemini_embeddings_adapter import GeminiEmbeddingsAdapter
from src.adapters.db.chat_repository_adapter import SQLChatRepositoryAdapter
from src.adapters.db.file_repository_adapter import SQLFileRepository
from src.adapters.db.database import get_session
from src.adapters.tools.bear_python_tool import BearPythonTool
from src.adapters.repositories.metrics_repository import SQLModelMetricsRepository

from src.application.services.chat_service import ChatServiceV2
from src.application.services.embeddings_service import EmbeddingsServiceV2
from src.application.services.file_processing_service import FileProcessingService
from src.application.services.metrics_service import MetricsService
from src.adapters.config.settings import settings

# --- Caché para singletons ---
@lru_cache(maxsize=None)
def get_http_client() -> httpx.Client:
    return httpx.Client()

@lru_cache(maxsize=None)
def get_async_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()

# --- Adaptadores ---
def get_chat_repository(session: Session = Depends(get_session)) -> ChatRepositoryPort:
    return SQLChatRepositoryAdapter(session)

def get_file_repository() -> FileRepositoryPort:
    # SQLFileRepository NO recibe Session en el constructor
    return SQLFileRepository()

def get_gemini_adapter() -> LLMPort:
    return GeminiAdapter(client=get_async_http_client())

def get_kimi_adapter() -> LLMPort:
    # Suponiendo que tienes un KimiAdapter
    # from src.adapters.agents.kimi_adapter import KimiAdapter
    # return KimiAdapter(client=get_async_http_client())
    return get_gemini_adapter() # Fallback por ahora

def get_gemini_embeddings_adapter() -> EmbeddingsPort:
    return GeminiEmbeddingsAdapter(client=get_async_http_client())

def get_python_search_tool() -> PythonSearchPort:
    # BearPythonTool(api_key, base_url) según su firma
    return BearPythonTool(
        api_key=settings.bear_api_key,
        base_url=settings.bear_base_url,
    )

@lru_cache(maxsize=None)
def get_metrics_service() -> MetricsService:
    """Factory para el servicio de métricas (singleton)."""
    metrics_repository = SQLModelMetricsRepository()
    return MetricsService(repository=metrics_repository)

# --- Servicios de Aplicación ---
def get_embeddings_service() -> EmbeddingsServiceV2:
    return EmbeddingsServiceV2(embeddings_client=get_gemini_embeddings_adapter())

def get_file_processing_service(
    file_repo: FileRepositoryPort = Depends(get_file_repository),
    embeddings_service: EmbeddingsServiceV2 = Depends(get_embeddings_service),
) -> FileProcessingService:
    return FileProcessingService(
        file_repo, 
        embeddings_service,
        max_pdf_size_mb=settings.file_max_pdf_size_mb
    )

def get_chat_service(
    llm_client: LLMPort = Depends(get_kimi_adapter),
    fallback_llm: LLMPort = Depends(get_gemini_adapter),
    repository: ChatRepositoryPort = Depends(get_chat_repository),
    embeddings_service: EmbeddingsServiceV2 = Depends(get_embeddings_service),
    python_search: PythonSearchPort = Depends(get_python_search_tool),
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> ChatServiceV2:
    return ChatServiceV2(
        llm_client=llm_client,
        repository=repository,
        fallback_llm=fallback_llm,
        embeddings_service=embeddings_service,
        python_search=python_search,
        metrics_service=metrics_service,
    )

# --- Dependencias para Endpoints de FastAPI ---

def get_chat_service_dependency(
    llm_client: LLMPort = Depends(get_kimi_adapter),
    fallback_llm: LLMPort = Depends(get_gemini_adapter),
    repository: ChatRepositoryPort = Depends(get_chat_repository),
    embeddings_service: EmbeddingsServiceV2 = Depends(get_embeddings_service),
    python_search: PythonSearchPort = Depends(get_python_search_tool),
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> ChatServiceV2:
    # Importante: NO llamar directamente a get_chat_service() aquí,
    # porque fuera del sistema de dependencias retornaría objetos Depends sin resolver.
    return ChatServiceV2(
        llm_client=llm_client,
        repository=repository,
        fallback_llm=fallback_llm,
        embeddings_service=embeddings_service,
        python_search=python_search,
        metrics_service=metrics_service,
    )

def get_embeddings_service_dependency() -> EmbeddingsServiceV2:
    return get_embeddings_service()

def get_file_processing_service_dependency(
    file_repo: FileRepositoryPort = Depends(get_file_repository),
    embeddings_service: EmbeddingsServiceV2 = Depends(get_embeddings_service),
) -> FileProcessingService:
    # Igual que con chat_service: no invocar directamente a una función con Depends.
    return FileProcessingService(
        file_repo, 
        embeddings_service,
        max_pdf_size_mb=settings.file_max_pdf_size_mb
    )
