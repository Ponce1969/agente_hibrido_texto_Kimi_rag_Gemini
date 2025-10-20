"""
Servicio de aplicación para el Guardian.
Incluye caché, rate limiting y lógica de negocio.
"""
import time
import hashlib
import logging
from collections import deque
from typing import Deque

from src.domain.ports.guardian_port import GuardianPort, GuardianResult, ThreatLevel
from src.domain.exceptions.guardian_exceptions import (
    MessageBlockedException,
    RateLimitExceededException
)

logger = logging.getLogger(__name__)


class GuardianService:
    """
    Servicio de aplicación que gestiona el Guardian con:
    - Caché local (evita consultas repetidas)
    - Rate limiting (máx. N llamadas por minuto)
    - Heurísticas rápidas (pre-filtrado)
    - Métricas detalladas
    """
    
    # Palabras clave sospechosas (pre-filtro rápido)
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
    ]
    
    def __init__(
        self,
        guardian_client: GuardianPort,
        max_calls_per_minute: int = 10,
        cache_ttl: int = 3600,  # 1 hora
        min_length_to_check: int = 50,  # Solo revisar mensajes largos
    ):
        self.client = guardian_client
        self.max_calls = max_calls_per_minute
        self.cache_ttl = cache_ttl
        self.min_length = min_length_to_check
        
        # Caché: {hash: (result, timestamp)}
        self.cache: dict[str, tuple[GuardianResult, float]] = {}
        
        # Rate limiting
        self.call_timestamps: Deque[float] = deque(maxlen=max_calls_per_minute)
        
        # Métricas
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "heuristic_blocks": 0,
            "llm_checks": 0,
            "rate_limit_skips": 0,
        }
    
    def _get_cache_key(self, text: str) -> str:
        """Genera clave de caché para un texto."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Verifica si una entrada de caché sigue siendo válida."""
        return (time.time() - timestamp) < self.cache_ttl
    
    def _can_call_llm(self) -> bool:
        """Verifica si se puede llamar al LLM (rate limiting)."""
        now = time.time()
        # Limpiar timestamps antiguos (> 60 segundos)
        while self.call_timestamps and now - self.call_timestamps[0] > 60:
            self.call_timestamps.popleft()
        
        return len(self.call_timestamps) < self.max_calls
    
    def _check_heuristics(self, text: str) -> GuardianResult | None:
        """
        Pre-filtro rápido con heurísticas.
        Retorna GuardianResult si detecta amenaza, None si debe consultar LLM.
        """
        text_lower = text.lower()
        
        # Buscar palabras clave sospechosas
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in text_lower:
                self.metrics["heuristic_blocks"] += 1
                logger.warning(f"Heuristic block: keyword '{keyword}' found")
                return GuardianResult(
                    is_safe=False,
                    threat_level=ThreatLevel.HIGH,
                    reason=f"Palabra clave sospechosa detectada: '{keyword}'",
                    confidence=0.9,
                    categories=["heuristic_block"],
                )
        
        return None  # No se detectó nada, consultar LLM
    
    async def check_message(
        self,
        text: str,
        user_id: str | None = None,
        force_check: bool = False
    ) -> GuardianResult:
        """
        Analiza un mensaje con caché, heurísticas y rate limiting.
        
        Args:
            text: Mensaje a analizar
            user_id: ID del usuario (opcional)
            force_check: Forzar consulta al LLM (ignorar caché)
            
        Returns:
            GuardianResult con el análisis
        """
        # 1. Mensajes muy cortos: permitir sin revisar
        if not force_check and len(text) < self.min_length:
            return GuardianResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                reason="Mensaje muy corto",
                confidence=1.0,
            )
        
        # 2. Verificar caché
        cache_key = self._get_cache_key(text)
        if not force_check and cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                self.metrics["cache_hits"] += 1
                logger.debug(f"Guardian cache hit for message hash {cache_key[:8]}")
                return result
        
        self.metrics["cache_misses"] += 1
        
        # 3. Heurísticas rápidas (pre-filtro)
        heuristic_result = self._check_heuristics(text)
        if heuristic_result and not heuristic_result.is_safe:
            # Guardar en caché
            self.cache[cache_key] = (heuristic_result, time.time())
            return heuristic_result
        
        # 4. Rate limiting
        if not self._can_call_llm():
            self.metrics["rate_limit_skips"] += 1
            logger.warning("Guardian rate limit exceeded, allowing message")
            # Si se excede el límite, permitir temporalmente
            return GuardianResult(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                reason="Rate limit excedido, permitido temporalmente",
                confidence=0.0,
            )
        
        # 5. Consultar al LLM Guardian
        self.call_timestamps.append(time.time())
        self.metrics["llm_checks"] += 1
        
        logger.info(f"Checking message with Guardian LLM (user: {user_id})")
        result = await self.client.check_message(text, user_id)
        
        # 6. Guardar en caché
        self.cache[cache_key] = (result, time.time())
        
        return result
    
    async def validate_or_raise(
        self,
        text: str,
        user_id: str | None = None
    ) -> None:
        """
        Valida un mensaje y lanza excepción si es bloqueado.
        
        Raises:
            MessageBlockedException: Si el mensaje es bloqueado
        """
        result = await self.check_message(text, user_id)
        
        if not result.is_safe:
            raise MessageBlockedException(
                reason=result.reason or "Contenido no permitido",
                threat_level=result.threat_level.value
            )
    
    def get_metrics(self) -> dict:
        """Obtiene métricas del servicio."""
        total_checks = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        
        return {
            **self.metrics,
            "cache_hit_rate": (
                self.metrics["cache_hits"] / total_checks
                if total_checks > 0
                else 0.0
            ),
            "cache_size": len(self.cache),
        }
    
    def clear_cache(self) -> None:
        """Limpia el caché."""
        self.cache.clear()
        logger.info("Guardian cache cleared")
