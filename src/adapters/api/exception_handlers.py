"""
Manejadores de excepciones para mapear excepciones de dominio a respuestas HTTP.

Este módulo implementa el contrato API-CLI definido en docs/api-cli-contract.md.
Mapea excepciones de dominio a códigos HTTP semánticos para que el CLI pueda
tomar decisiones inteligentes de fallback.
"""
import logging
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.domain_exceptions import (
    AIProviderError,
    ChatSessionNotFoundError,
    DomainException,
    InsufficientContextError,
    InvalidMessageError,
    RateLimitExceededError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class HTTPExceptionResponse:
    """Helper para crear respuestas HTTP consistentes."""

    @staticmethod
    def create(
        status_code: int,
        error: str,
        message: str,
        **extra: Any
    ) -> JSONResponse:
        """Crea una respuesta HTTP con formato estándar."""
        content = {
            "error": error,
            "message": message,
            **extra
        }
        return JSONResponse(
            status_code=status_code,
            content=content
        )


async def chat_session_not_found_handler(
    request: Request,
    exc: ChatSessionNotFoundError
) -> JSONResponse:
    """
    Maneja ChatSessionNotFoundError → 422 Unprocessable Entity.

    Según contrato: El CLI debe retry con session_id=0 para crear nueva sesión.
    """
    logger.warning(f"Sesión no encontrada: {exc.session_id}")
    return HTTPExceptionResponse.create(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="SessionNotFound",
        message=f"Sesión {exc.session_id} no encontrada",
        session_id=exc.session_id
    )


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceededError
) -> JSONResponse:
    """
    Maneja RateLimitExceededError → 429 Too Many Requests.

    Según contrato: El CLI debe hacer backoff exponencial con retry_after.
    """
    logger.warning(f"Rate limit excedido: {exc.limit_type}")

    # Calcular retry_after basado en el tipo de límite
    retry_after = 5  # Default 5 segundos
    if "minute" in exc.limit_type.lower():
        retry_after = 60
    elif "hour" in exc.limit_type.lower():
        retry_after = 300

    return HTTPExceptionResponse.create(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error="RateLimitExceeded",
        message=f"Límite de uso excedido: {exc.limit_type}",
        retry_after=retry_after
    )


async def ai_provider_error_handler(
    request: Request,
    exc: AIProviderError
) -> JSONResponse:
    """
    Maneja AIProviderError → 503 Service Unavailable.

    Según contrato: El CLI debe retry 1x → Cache → LLM local.
    """
    logger.error(f"Error de proveedor IA: {exc.provider} - {exc.reason}")
    return HTTPExceptionResponse.create(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error="AIProviderUnavailable",
        message=f"Proveedor de IA '{exc.provider}' no disponible temporalmente",
        provider=exc.provider,
        reason=exc.reason or None,
        retry_after=None
    )


async def validation_error_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    Maneja ValidationError → 400 Bad Request.

    Según contrato: El CLI debe mostrar error técnico y abortar.
    """
    logger.warning(f"Error de validación: {exc.field} = {exc.value}")
    return HTTPExceptionResponse.create(
        status_code=status.HTTP_400_BAD_REQUEST,
        error="ValidationError",
        message=f"Validación fallida para '{exc.field}': {exc.reason}",
        field=exc.field,
        value=exc.value
    )


async def invalid_message_error_handler(
    request: Request,
    exc: InvalidMessageError
) -> JSONResponse:
    """
    Maneja InvalidMessageError → 400 Bad Request.

    Según contrato: El CLI debe mostrar error técnico y abortar.
    """
    logger.warning(f"Mensaje inválido: {exc.reason}")
    return HTTPExceptionResponse.create(
        status_code=status.HTTP_400_BAD_REQUEST,
        error="InvalidMessage",
        message=f"Mensaje inválido: {exc.reason}",
        reason=exc.reason
    )


async def insufficient_context_error_handler(
    request: Request,
    exc: InsufficientContextError
) -> JSONResponse:
    """
    Maneja InsufficientContextError → 206 Partial Content.

    Según contrato: El CLI debe usar la respuesta parcial si existe.
    """
    logger.warning(f"Contexto insuficiente: {exc.reason}")
    return HTTPExceptionResponse.create(
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        error="PartialResponse",
        message="Respuesta generada con contexto limitado",
        reason=exc.reason,
        partial=True
    )


async def domain_exception_handler(
    request: Request,
    exc: DomainException
) -> JSONResponse:
    """
    Maneja excepciones de dominio genéricas → 500 Internal Server Error.

    Este es el fallback para excepciones de dominio no específicamente manejadas.
    """
    logger.error(f"Excepción de dominio no manejada: {type(exc).__name__} - {str(exc)}")
    return HTTPExceptionResponse.create(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="InternalError",
        message="Error interno del servidor"
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Maneja excepciones genéricas → 500 Internal Server Error.

    Este es el último recurso para errores inesperados.
    """
    logger.error(f"Excepción no manejada: {type(exc).__name__} - {str(exc)}", exc_info=True)
    return HTTPExceptionResponse.create(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="InternalError",
        message="Error interno del servidor"
    )


def register_exception_handlers(app):
    """
    Registra todos los manejadores de excepciones en la aplicación FastAPI.

    Args:
        app: Instancia de FastAPI
    """
    # Excepciones de dominio específicas
    app.add_exception_handler(ChatSessionNotFoundError, chat_session_not_found_handler)
    app.add_exception_handler(RateLimitExceededError, rate_limit_exceeded_handler)
    app.add_exception_handler(AIProviderError, ai_provider_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(InvalidMessageError, invalid_message_error_handler)
    app.add_exception_handler(InsufficientContextError, insufficient_context_error_handler)

    # Fallback para excepciones de dominio no específicas
    app.add_exception_handler(DomainException, domain_exception_handler)

    # Fallback para excepciones genéricas
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Manejadores de excepciones registrados según contrato API-CLI")
