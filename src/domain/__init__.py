"""
Domain Layer - Lógica de negocio pura.

Este módulo contiene todas las entidades, servicios y reglas de negocio
del dominio, independientes de cualquier framework o tecnología específica.
"""

# Excepciones de dominio
from .exceptions.domain_exceptions import (
    AgentModeNotSupportedError,
    AIProviderError,
    ChatSessionAlreadyExistsError,
    ChatSessionNotFoundError,
    DomainException,
    FileNotFoundError,
    FileProcessingError,
    FileSectionNotFoundError,
    InsufficientContextError,
    InvalidMessageError,
    MessageNotFoundError,
    RateLimitExceededError,
    ValidationError,
)

# Modelos de dominio
from .models.chat_models import (
    ChatMessage,
    ChatSession,
    FileDocument,
    FileSection,
    MessageRole,
)

# Interfaces de repositorio (ahora en ports/)
# Las interfaces están en domain/ports/ siguiendo arquitectura hexagonal
# Servicios de dominio
from .services.chat_domain_service import (
    AgentDomainService,
    ChatDomainService,
    FileDomainService,
    ValidationService,
)

# Exportar todo lo público
__all__ = [
    # Excepciones
    "DomainException",
    "ChatSessionNotFoundError",
    "ChatSessionAlreadyExistsError",
    "InvalidMessageError",
    "MessageNotFoundError",
    "FileNotFoundError",
    "FileProcessingError",
    "FileSectionNotFoundError",
    "AgentModeNotSupportedError",
    "AIProviderError",
    "InsufficientContextError",
    "RateLimitExceededError",
    "ValidationError",

    # Modelos
    "ChatMessage",
    "ChatSession",
    "FileDocument",
    "FileSection",
    "MessageRole",

    # Servicios
    "ChatDomainService",
    "FileDomainService",
    "AgentDomainService",
    "ValidationService",
]
