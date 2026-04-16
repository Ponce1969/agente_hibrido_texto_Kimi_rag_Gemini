"""
Retry con exponential backoff para llamadas a APIs externas.

Proporciona reintentos automáticos con espera exponencial para errores
transitorios (429 rate limit, 500 server error, timeouts).
No reintenta en errores de autenticación (401/403).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Errores que merecen reintento (transitorios)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def is_retryable_error(error: Exception) -> bool:
    """Determina si un error merece reintento."""
    if isinstance(error, httpx.TimeoutException):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in RETRYABLE_STATUS_CODES
    if isinstance(error, ConnectionRefusedError):
        return False  # Auth errors nunca se reintan
    if isinstance(error, OSError | ConnectionError):
        return True
    return False


async def retry_with_backoff(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    **kwargs: Any,
) -> Any:
    """
    Ejecuta una función async con reintentos y exponential backoff.

    Args:
        fn: Función async a ejecutar
        max_retries: Máximo de reintentos (default 3)
        base_delay: Delay base en segundos (default 1.0)
        max_delay: Delay máximo en segundos (default 10.0)

    Returns:
        El resultado de la función

    Raises:
        La última excepción si todos los reintentos fallan
    """
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            if not is_retryable_error(e):
                logger.error(f"Non-retryable error: {e}")
                raise

            last_error = e

            if attempt < max_retries:
                delay = min(base_delay * (2**attempt), max_delay)
                provider = getattr(fn, "__qualname__", str(fn))
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} for {provider} "
                    f"after {delay:.1f}s. Error: {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries} retries exhausted. Last error: {e}")
                raise

    # Should not reach here, but just in case
    if last_error:
        raise last_error
