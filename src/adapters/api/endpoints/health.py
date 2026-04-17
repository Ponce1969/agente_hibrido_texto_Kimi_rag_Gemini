"""
Endpoint de Health Check para observabilidad del sistema.

Conecta los circuit breakers reales de los LLM adapters
para dar visibilidad real del estado de los providers.
"""

import logging
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from src.adapters.agents.circuit_breaker import CircuitBreaker
from src.adapters.agents.deepseek_adapter import _deepseek_breaker
from src.adapters.agents.gemini_adapter import _gemini_breaker
from src.adapters.agents.groq_adapter import _groq_breaker
from src.adapters.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key != settings.rag_api_key:
        return ""
    return api_key


ProviderStatus = Literal["ok", "degraded", "down"]


class ProviderHealth(BaseModel):
    status: ProviderStatus
    reason: str | None = None
    circuit_breaker: str = "closed"


class HealthResponse(BaseModel):
    api: ProviderStatus
    providers: dict[str, ProviderHealth]
    llm_routing: dict[str, str]
    guardian: dict[str, str]
    timestamp: str


class PublicHealthResponse(BaseModel):
    api: ProviderStatus
    timestamp: str


def _breaker_to_status(
    breaker: CircuitBreaker,
) -> tuple[ProviderStatus, ProviderHealth]:
    """Convierte estado de circuit breaker a status de provider."""
    if breaker.state == "open":
        return "down", ProviderHealth(
            status="down",
            reason=f"circuit breaker open ({breaker.failure_count} failures)",
            circuit_breaker="open",
        )
    if breaker.state == "half-open":
        return "degraded", ProviderHealth(
            status="degraded",
            reason="circuit breaker half-open (probing)",
            circuit_breaker="half-open",
        )
    return "ok", ProviderHealth(status="ok", circuit_breaker="closed")


@router.get("/health", response_model=HealthResponse | PublicHealthResponse)
async def health_check(api_key: str = Depends(verify_api_key)):
    """Health check del sistema con estado real de circuit breakers."""
    timestamp = datetime.now(UTC).isoformat()

    if not api_key:
        return PublicHealthResponse(
            api=_compute_overall_status(),
            timestamp=timestamp,
        )

    providers = {}
    for name, breaker in [
        ("deepseek", _deepseek_breaker),
        ("groq", _groq_breaker),
        ("gemini", _gemini_breaker),
    ]:
        _, health = _breaker_to_status(breaker)
        providers[name] = health

    return HealthResponse(
        api=_compute_overall_status(),
        providers=providers,
        llm_routing={
            "chat": f"{settings.chat_provider}/{settings.chat_model}",
            "rag": f"{settings.rag_provider}/{settings.rag_model}",
            "fallback": f"{settings.fallback_provider}/{settings.fallback_model}",
        },
        guardian={
            "enabled": str(settings.guardian_enabled),
            "mode": "llm+heuristics"
            if settings.guardian_llm_enabled
            else "heuristics-only",
        },
        timestamp=timestamp,
    )


def _compute_overall_status() -> ProviderStatus:
    """Computa el estado general basado en los circuit breakers."""
    breakers = [_deepseek_breaker, _groq_breaker, _gemini_breaker]
    states = [b.state for b in breakers]

    if all(s == "open" for s in states):
        return "down"
    if any(s in ("open", "half-open") for s in states):
        return "degraded"
    return "ok"
