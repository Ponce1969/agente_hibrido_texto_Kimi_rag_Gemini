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
                              FileRepositoryPort, PythonSearchPort, GuardianPort)
                              
from src.adapters.agents.gemini_adapter import GeminiAdapter
from src.adapters.agents.gemini_embeddings_adapter import GeminiEmbeddingsAdapter
from src.adapters.db.chat_repository_adapter import SQLChatRepositoryAdapter
from src.adapters.db.file_repository_adapter import SQLFileRepository
from src.adapters.db.database import get_session
from src.adapters.tools.bear_python_tool import BearPythonTool
from src.adapters.tools.qwen_guardian_client import QwenGuardianClient
from src.adapters.repositories.metrics_repository import SQLModelMetricsRepository

from src.application.services.chat_service import ChatServiceV2
from src.application.services.embeddings_service import EmbeddingsServiceV2
from src.application.services.file_processing_service import FileProcessingService
from src.application.services.metrics_service import MetricsService
from src.application.services.auth_service import AuthService
from src.application.services.guardian_service import GuardianService
from src.adapters.config.settings import settings
from src.adapters.security.argon2_hasher import Argon2PasswordHasher
from src.adapters.security.jwt_token_service import JWTTokenService
from src.adapters.db.user_repository import SQLModelUserRepository

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

# --- Servicios de Autenticación ---

@lru_cache(maxsize=None)
def get_password_hasher() -> Argon2PasswordHasher:
    """Factory para el hasher de contraseñas (singleton)."""
    return Argon2PasswordHasher()

@lru_cache(maxsize=None)
def get_token_service() -> JWTTokenService:
    """Factory para el servicio de tokens (singleton)."""
    return JWTTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm="HS256",
        expire_minutes=settings.jwt_expire_minutes
    )

def get_user_repository(session: Session = Depends(get_session)) -> SQLModelUserRepository:
    """Factory para el repositorio de usuarios."""
    return SQLModelUserRepository(session)

def get_auth_service(
    password_hasher: Argon2PasswordHasher = Depends(get_password_hasher),
    token_service: JWTTokenService = Depends(get_token_service),
    user_repository: SQLModelUserRepository = Depends(get_user_repository),
) -> AuthService:
    """Factory para el servicio de autenticación."""
    return AuthService(
        password_hasher=password_hasher,
        token_service=token_service,
        user_repository=user_repository
    )

# --- Guardian ---
@lru_cache(maxsize=1)
def get_guardian_client() -> GuardianPort:
    """Factory para el cliente Guardian (Qwen2.5-1.5B)."""
    return QwenGuardianClient(
        api_url=settings.guardian_api_url,
        api_key=settings.guardian_api_key,
        timeout=settings.guardian_timeout,
        enabled=settings.guardian_enabled
    )

@lru_cache(maxsize=1)
def get_guardian_service(
    guardian_client: GuardianPort = Depends(get_guardian_client)
) -> GuardianService:
    """Factory para el servicio Guardian con caché y rate limiting."""
    return GuardianService(
        guardian_client=guardian_client,
        max_calls_per_minute=settings.guardian_max_calls_per_minute,
        cache_ttl=settings.guardian_cache_ttl,
        min_length_to_check=settings.guardian_min_length
    )
