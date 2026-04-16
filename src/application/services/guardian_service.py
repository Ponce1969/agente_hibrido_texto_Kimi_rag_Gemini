"""
Servicio de aplicación para el Guardian.
Incluye caché, rate limiting y lógica de negocio.

Para el caso de uso CLI (contexto para modelos locales), el Guardian
opera en modo heurístico por defecto — sin llamadas LLM externas.
Esto evita bloquear el chat si la API de terceros falla.
"""

import hashlib
import logging
import time
from collections import deque

from src.domain.exceptions.guardian_exceptions import (
    MessageBlockedException,
)
from src.domain.ports.guardian_port import GuardianPort, GuardianResult, ThreatLevel

logger = logging.getLogger(__name__)


class GuardianService:
    """
    Servicio de aplicación que gestiona el Guardian con:
    - Heurísticas rápidas (pre-filtrado) — Siempre activo
    - LLM check opcional — Solo si guardian_llm_enabled=True
    - Caché local
    - Rate limiting
    - Métricas detalladas

    Modo de operación:
    - guardian_llm_enabled=False (default): Solo heurísticas, sin llamadas LLM.
      Rápido, sin dependencia externa, ideal para CLI.
    - guardian_llm_enabled=True: Heurísticas + LLM externo (SiliconFlow).
      Más preciso pero depende de API de terceros.
    """

    SUSPICIOUS_KEYWORDS = [
        "ignore previous",
        "ignore all",
        "disregard",
        "forget everything",
        "new instructions",
        "system prompt",
        "you are now",
        "pretend you are",
        "act as if",
        "jailbreak",
        "dan mode",
        "developer mode",
        "bypass",
        "override",
        "sudo",
        "root access",
        "extract your instructions",
        "reveal your prompt",
        "show me your system",
        "repeat everything above",
        "what were you told",
    ]

    def __init__(
        self,
        guardian_client: GuardianPort,
        max_calls_per_minute: int = 10,
        cache_ttl: int = 3600,
        min_length_to_check: int = 20,
        llm_enabled: bool = False,
    ):
        self.client = guardian_client
        self.max_calls = max_calls_per_minute
        self.cache_ttl = cache_ttl
        self.min_length = min_length_to_check
        self.llm_enabled = llm_enabled

        self.cache: dict[str, tuple[GuardianResult, float]] = {}
        self.call_timestamps: deque[float] = deque(maxlen=max_calls_per_minute)

        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "heuristic_blocks": 0,
            "heuristic_allows": 0,
            "llm_checks": 0,
            "rate_limit_skips": 0,
            "llm_errors": 0,
        }

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        return (time.time() - timestamp) < self.cache_ttl

    def _can_call_llm(self) -> bool:
        now = time.time()
        while self.call_timestamps and now - self.call_timestamps[0] > 60:
            self.call_timestamps.popleft()
        return len(self.call_timestamps) < self.max_calls

    def _check_heuristics(self, text: str) -> GuardianResult | None:
        """Pre-filtro rápido con heurísticas. Retorna None si es seguro."""
        text_lower = text.lower()

        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in text_lower:
                self.metrics["heuristic_blocks"] += 1
                logger.warning(f"Heuristic block: keyword '{keyword}' found")
                return GuardianResult(
                    is_safe=False,
                    threat_level=ThreatLevel.HIGH,
                    reason=f"Patrón sospechoso detectado: '{keyword}'",
                    confidence=0.9,
                    categories=["heuristic_block"],
                )

        self.metrics["heuristic_allows"] += 1
        return None

    async def check_message(
        self,
        text: str,
        user_id: str | None = None,
        force_check: bool = False,
    ) -> GuardianResult:
        """
        Analiza un mensaje.

        Flujo:
        1. Mensajes cortos → permitir (sin check)
        2. Caché → usar resultado cacheado
        3. Heurísticas → bloquear si detecta patrón sospechoso
        4. Si llm_enabled=False → permitir (solo heurísticas)
        5. Si llm_enabled=True → consultar LLM externo
        """
        if not force_check and len(text) < self.min_length:
            return GuardianResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                reason="Mensaje muy corto",
                confidence=1.0,
            )

        cache_key = self._get_cache_key(text)
        if not force_check and cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                self.metrics["cache_hits"] += 1
                return result

        self.metrics["cache_misses"] += 1

        # Heurísticas siempre activas
        heuristic_result = self._check_heuristics(text)
        if heuristic_result and not heuristic_result.is_safe:
            self.cache[cache_key] = (heuristic_result, time.time())
            return heuristic_result

        # Si LLM está deshabilitado, heurísticas bastan → permitir
        if not self.llm_enabled:
            return GuardianResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                reason="Aprobado por heurísticas (modo sin LLM)",
                confidence=0.7,
            )

        # LLM check (solo si está habilitado)
        if not self._can_call_llm():
            self.metrics["rate_limit_skips"] += 1
            logger.warning("Guardian rate limit exceeded, allowing message")
            return GuardianResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                reason="Rate limit excedido",
                confidence=0.0,
            )

        self.call_timestamps.append(time.time())
        self.metrics["llm_checks"] += 1

        try:
            logger.info(f"Guardian LLM check (user: {user_id})")
            result = await self.client.check_message(text, user_id)
            self.cache[cache_key] = (result, time.time())
            return result
        except Exception as e:
            self.metrics["llm_errors"] += 1
            logger.error(f"Guardian LLM error (allowing message): {e}")
            # Fail-open: si el LLM falla, permettre el mensaje
            # Las heurísticas ya pasaron, es seguro continuar
            return GuardianResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                reason=f"LLM error, aprobado por heurísticas: {e}",
                confidence=0.5,
            )

    async def validate_or_raise(
        self,
        text: str,
        user_id: str | None = None,
    ) -> None:
        result = await self.check_message(text, user_id)
        if not result.is_safe:
            raise MessageBlockedException(
                reason=result.reason or "Contenido no permitido",
                threat_level=result.threat_level.value,
            )

    def get_metrics(self) -> dict:
        total_checks = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        return {
            **self.metrics,
            "llm_enabled": self.llm_enabled,
            "cache_hit_rate": (
                self.metrics["cache_hits"] / total_checks if total_checks > 0 else 0.0
            ),
            "cache_size": len(self.cache),
        }

    def clear_cache(self) -> None:
        self.cache.clear()
        logger.info("Guardian cache cleared")
