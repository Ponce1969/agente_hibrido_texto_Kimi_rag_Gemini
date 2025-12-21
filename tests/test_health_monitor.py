"""
Tests unitarios para el HealthMonitor.

Valida la lógica de determinación de estados sin depender de la app completa.
"""
import pytest

from src.adapters.api.endpoints.health import HealthMonitor


@pytest.fixture
def monitor():
    """Instancia fresca del monitor para cada test."""
    return HealthMonitor()


def test_all_providers_ok(monitor):
    """Test: Todos los proveedores OK → API OK."""
    assert monitor.get_api_status() == "ok"
    assert monitor.get_provider_health("gemini").status == "ok"
    assert monitor.get_provider_health("kimi").status == "ok"
    assert monitor.get_provider_health("brave").status == "ok"


def test_one_provider_down(monitor):
    """Test: Un proveedor DOWN (circuit breaker open) → API degraded."""
    monitor.update_provider_state(
        "gemini",
        error="connection_timeout",
        circuit_breaker="open"
    )

    assert monitor.get_api_status() == "degraded"
    assert monitor.get_provider_health("gemini").status == "down"
    assert monitor.get_provider_health("gemini").reason == "circuit_breaker_open"
    assert monitor.get_circuit_breaker_state("gemini") == "open"


def test_one_provider_degraded(monitor):
    """Test: Un proveedor degraded (half-open) → API degraded."""
    monitor.update_provider_state(
        "kimi",
        circuit_breaker="half_open"
    )

    assert monitor.get_api_status() == "degraded"
    assert monitor.get_provider_health("kimi").status == "degraded"
    assert monitor.get_provider_health("kimi").reason == "circuit_breaker_half_open"
    assert monitor.get_circuit_breaker_state("kimi") == "half_open"


def test_rate_limited_provider(monitor):
    """Test: Proveedor con rate limit → degraded."""
    monitor.update_provider_state(
        "brave",
        error="rate_limit_exceeded",
        circuit_breaker="closed"
    )

    health = monitor.get_provider_health("brave")
    assert health.status == "degraded"
    assert health.reason == "rate_limited"


def test_timeout_provider(monitor):
    """Test: Proveedor con timeout → degraded."""
    monitor.update_provider_state(
        "gemini",
        error="timeout_error",
        circuit_breaker="closed"
    )

    health = monitor.get_provider_health("gemini")
    assert health.status == "degraded"
    assert health.reason == "timeout"


def test_all_providers_down(monitor):
    """Test: Todos los proveedores down → API down."""
    for provider in ["gemini", "kimi", "brave"]:
        monitor.update_provider_state(
            provider,
            error="connection_error",
            circuit_breaker="open"
        )

    assert monitor.get_api_status() == "down"


def test_latency_tracking(monitor):
    """Test: Tracking de latencia."""
    monitor.update_provider_state(
        "gemini",
        latency_ms=150
    )

    health = monitor.get_provider_health("gemini")
    assert health.latency_ms == 150
    assert health.status == "ok"


def test_error_cleared_after_success(monitor):
    """Test: Error se limpia después de éxito."""
    # Primero un error
    monitor.update_provider_state(
        "kimi",
        error="rate_limit",
        circuit_breaker="closed"
    )
    assert monitor.get_provider_health("kimi").status == "degraded"

    # Luego éxito (error=None)
    monitor.update_provider_state(
        "kimi",
        error=None,
        circuit_breaker="closed"
    )
    assert monitor.get_provider_health("kimi").status == "ok"
