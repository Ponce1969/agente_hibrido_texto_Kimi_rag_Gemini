"""
Circuit breaker para proveedores LLM.

Si un proveedor falla N veces consecutivas, se desactiva temporalmente.
Después de un tiempo de recuperación, permite un intento de prueba (half-open).
Si el intento tiene éxito, se reactiva. Si falla, sigue desactivado.

Uso:
    cb = CircuitBreaker(name="deepseek", failure_threshold=3, recovery_seconds=60)
    if cb.is_open:
        raise ProviderUnavailable("deepseek")
    try:
        result = await call_llm(...)
        cb.record_success()
    except Exception:
        cb.record_failure()
        raise
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker simple para un proveedor LLM."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_seconds: float = 60.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._state: str = "closed"  # closed, open, half-open

    @property
    def is_open(self) -> bool:
        """True si el circuit breaker está abierto (proveedor deshabilitado)."""
        if self._state == "closed":
            return False
        if self._state == "open":
            # Verificar si pasó el tiempo de recuperación
            if time.monotonic() - self._last_failure_time >= self.recovery_seconds:
                self._state = "half-open"
                logger.info(
                    f"Circuit breaker [{self.name}]: half-open, permitiendo intento de prueba"
                )
                return False
            return True
        # half-open: permitir un intento
        return False

    @property
    def state(self) -> str:
        return self._state

    def record_success(self) -> None:
        """Registra un éxito — cierra el circuit breaker."""
        if self._state == "half-open":
            logger.info(f"Circuit breaker [{self.name}]: closed (éxito en half-open)")
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        """Registra un fallo — incrementa el contador y abre si supera el umbral."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._state == "half-open":
            logger.warning(f"Circuit breaker [{self.name}]: open (fallo en half-open)")
            self._state = "open"
        elif self._failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker [{self.name}]: open "
                f"({self._failure_count} fallos consecutivos)"
            )
            self._state = "open"

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, state={self._state}, "
            f"failures={self._failure_count})"
        )
