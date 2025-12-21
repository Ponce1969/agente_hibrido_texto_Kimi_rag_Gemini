"""
Endpoint de Health Check para observabilidad del sistema.

Este endpoint expone el estado interno de la API y sus proveedores
sin realizar llamadas externas costosas. Implementa el contrato de
observabilidad definido para el sistema distribuido CLI-API.

Estados permitidos: ok, degraded, down
"""
import logging
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from src.adapters.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Seguridad: API Key para acceso interno
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verifica la API Key para acceso al health endpoint."""
    if not api_key or api_key != settings.rag_api_key:
        # Para health, devolvemos versión pública limitada
        return ""
    return api_key


# --- Schemas ---

ProviderStatus = Literal["ok", "degraded", "down"]
CircuitBreakerState = Literal["closed", "half_open", "open"]


class ProviderHealth(BaseModel):
    """Estado de salud de un proveedor."""
    status: ProviderStatus
    reason: str | None = None
    latency_ms: int | None = None


class HealthResponse(BaseModel):
    """Respuesta completa del health check."""
    api: ProviderStatus
    providers: dict[str, ProviderHealth]
    circuit_breakers: dict[str, CircuitBreakerState]
    timestamp: str


class PublicHealthResponse(BaseModel):
    """Respuesta pública simplificada."""
    api: ProviderStatus
    timestamp: str


# --- Estado Interno (simulado por ahora) ---

class HealthMonitor:
    """
    Monitor de salud del sistema.

    En una implementación completa, esto leería:
    - Estado de circuit breakers reales
    - Métricas de latencia cacheadas
    - Últimos errores registrados por proveedor
    """

    def __init__(self):
        # Estado interno que se actualiza con cada request/error
        self._provider_states: dict[str, dict] = {
            "gemini": {
                "status": "ok",
                "last_error": None,
                "last_latency_ms": None,
                "circuit_breaker": "closed"
            },
            "kimi": {
                "status": "ok",
                "last_error": None,
                "last_latency_ms": None,
                "circuit_breaker": "closed"
            },
            "brave": {
                "status": "ok",
                "last_error": None,
                "last_latency_ms": None,
                "circuit_breaker": "closed"
            }
        }

    def get_provider_health(self, provider: str) -> ProviderHealth:
        """
        Obtiene el estado de salud de un proveedor basado en estado interno.

        NO hace llamadas externas. Lee:
        - Estado del circuit breaker
        - Último error conocido
        - Última latencia cacheada
        """
        state = self._provider_states.get(provider, {})
        circuit_state = state.get("circuit_breaker", "closed")

        # Determinar status basado en circuit breaker
        if circuit_state == "open":
            status = "down"
            reason = "circuit_breaker_open"
        elif circuit_state == "half_open":
            status = "degraded"
            reason = "circuit_breaker_half_open"
        else:
            # Circuit breaker cerrado, verificar último error
            last_error = state.get("last_error")
            if last_error:
                if "rate_limit" in last_error.lower():
                    status = "degraded"
                    reason = "rate_limited"
                elif "timeout" in last_error.lower():
                    status = "degraded"
                    reason = "timeout"
                else:
                    status = "degraded"
                    reason = last_error
            else:
                status = "ok"
                reason = None

        return ProviderHealth(
            status=status,
            reason=reason,
            latency_ms=state.get("last_latency_ms")
        )

    def get_circuit_breaker_state(self, provider: str) -> CircuitBreakerState:
        """Obtiene el estado del circuit breaker de un proveedor."""
        state = self._provider_states.get(provider, {})
        return state.get("circuit_breaker", "closed")

    def get_api_status(self) -> ProviderStatus:
        """
        Determina el estado general de la API basado en proveedores.

        Reglas:
        - Si todos ok → ok
        - Si alguno degraded → degraded
        - Si todos down → down
        """
        provider_statuses = [
            self.get_provider_health(p).status
            for p in self._provider_states.keys()
        ]

        if all(s == "ok" for s in provider_statuses):
            return "ok"
        elif all(s == "down" for s in provider_statuses):
            return "down"
        else:
            return "degraded"

    def update_provider_state(
        self,
        provider: str,
        error: str | None = None,
        latency_ms: int | None = None,
        circuit_breaker: CircuitBreakerState | None = None
    ):
        """
        Actualiza el estado interno de un proveedor.

        Este método sería llamado por los servicios cuando:
        - Ocurre un error (error="mensaje")
        - Se completa una request exitosa (error=None limpia el error)
        - Cambia el estado del circuit breaker
        """
        if provider not in self._provider_states:
            self._provider_states[provider] = {}

        # Actualizar error (None limpia el error)
        self._provider_states[provider]["last_error"] = error
        
        if latency_ms is not None:
            self._provider_states[provider]["last_latency_ms"] = latency_ms
        if circuit_breaker is not None:
            self._provider_states[provider]["circuit_breaker"] = circuit_breaker


# Instancia global del monitor
health_monitor = HealthMonitor()


# --- Endpoints ---

@router.get("/health", response_model=HealthResponse | PublicHealthResponse)
async def health_check(api_key: str = Depends(verify_api_key)):
    """
    Health check del sistema.

    - Con API Key: Devuelve estado completo de proveedores
    - Sin API Key: Devuelve solo estado general de la API

    NO realiza llamadas externas. Lee estado interno cacheado.
    """
    timestamp = datetime.now(UTC).isoformat()

    # Sin API Key: versión pública limitada
    if not api_key:
        return PublicHealthResponse(
            api=health_monitor.get_api_status(),
            timestamp=timestamp
        )

    # Con API Key: versión completa
    providers = {
        "gemini": health_monitor.get_provider_health("gemini"),
        "kimi": health_monitor.get_provider_health("kimi"),
        "brave": health_monitor.get_provider_health("brave")
    }

    circuit_breakers = {
        "gemini": health_monitor.get_circuit_breaker_state("gemini"),
        "kimi": health_monitor.get_circuit_breaker_state("kimi"),
        "brave": health_monitor.get_circuit_breaker_state("brave")
    }

    return HealthResponse(
        api=health_monitor.get_api_status(),
        providers=providers,
        circuit_breakers=circuit_breakers,
        timestamp=timestamp
    )


@router.get("/health/providers/{provider_name}")
async def provider_health(
    provider_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Estado de salud de un proveedor específico.

    Requiere API Key.
    """
    if not api_key:
        return {"error": "API Key requerida"}

    if provider_name not in ["gemini", "kimi", "brave"]:
        return {"error": f"Proveedor '{provider_name}' no reconocido"}

    return {
        "provider": provider_name,
        "health": health_monitor.get_provider_health(provider_name),
        "circuit_breaker": health_monitor.get_circuit_breaker_state(provider_name),
        "timestamp": datetime.now(UTC).isoformat()
    }
