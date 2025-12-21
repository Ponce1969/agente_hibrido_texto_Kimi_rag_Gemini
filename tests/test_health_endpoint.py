"""
Tests para el endpoint /health.

Valida:
- Respuesta pública sin API Key
- Respuesta completa con API Key
- Estados de proveedores basados en circuit breakers
- Estado general de la API
"""
import pytest
from fastapi.testclient import TestClient

from src.adapters.api.endpoints.health import health_monitor
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_health_monitor():
    """Reset del monitor de salud antes de cada test."""
    # Resetear a estado inicial (todos ok)
    for provider in ["gemini", "kimi", "brave"]:
        health_monitor.update_provider_state(
            provider,
            error=None,
            latency_ms=None,
            circuit_breaker="closed"
        )
    yield


def test_health_public_without_api_key():
    """Test: /health sin API Key devuelve versión pública."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Debe tener solo api y timestamp
    assert "api" in data
    assert "timestamp" in data
    assert data["api"] in ["ok", "degraded", "down"]

    # NO debe tener información detallada
    assert "providers" not in data
    assert "circuit_breakers" not in data


def test_health_complete_with_api_key():
    """Test: /health con API Key devuelve versión completa."""
    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "test-api-key"}  # Usar la key de settings
    )

    assert response.status_code == 200
    data = response.json()

    # Debe tener toda la información
    assert "api" in data
    assert "providers" in data
    assert "circuit_breakers" in data
    assert "timestamp" in data

    # Validar estructura de providers
    assert "gemini" in data["providers"]
    assert "kimi" in data["providers"]
    assert "brave" in data["providers"]

    # Validar estructura de circuit_breakers
    assert "gemini" in data["circuit_breakers"]
    assert "kimi" in data["circuit_breakers"]
    assert "brave" in data["circuit_breakers"]


def test_health_all_providers_ok():
    """Test: Todos los proveedores OK → API OK."""
    # Estado inicial: todos ok
    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["api"] == "ok"
    assert data["providers"]["gemini"]["status"] == "ok"
    assert data["providers"]["kimi"]["status"] == "ok"
    assert data["providers"]["brave"]["status"] == "ok"
    assert data["circuit_breakers"]["gemini"] == "closed"


def test_health_one_provider_down():
    """Test: Un proveedor DOWN → API degraded."""
    # Simular que Gemini está down (circuit breaker open)
    health_monitor.update_provider_state(
        "gemini",
        error="connection_timeout",
        circuit_breaker="open"
    )

    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["api"] == "degraded"
    assert data["providers"]["gemini"]["status"] == "down"
    assert data["providers"]["gemini"]["reason"] == "circuit_breaker_open"
    assert data["circuit_breakers"]["gemini"] == "open"


def test_health_one_provider_degraded():
    """Test: Un proveedor degraded (half-open) → API degraded."""
    # Simular que Kimi está en half-open
    health_monitor.update_provider_state(
        "kimi",
        circuit_breaker="half_open"
    )

    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["api"] == "degraded"
    assert data["providers"]["kimi"]["status"] == "degraded"
    assert data["providers"]["kimi"]["reason"] == "circuit_breaker_half_open"
    assert data["circuit_breakers"]["kimi"] == "half_open"


def test_health_rate_limited_provider():
    """Test: Proveedor con rate limit → degraded."""
    # Simular rate limit en Brave
    health_monitor.update_provider_state(
        "brave",
        error="rate_limit_exceeded",
        circuit_breaker="closed"
    )

    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["providers"]["brave"]["status"] == "degraded"
    assert data["providers"]["brave"]["reason"] == "rate_limited"


def test_health_provider_specific_endpoint():
    """Test: Endpoint específico de proveedor."""
    response = client.get(
        "/api/v1/health/providers/gemini",
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["provider"] == "gemini"
    assert "health" in data
    assert "circuit_breaker" in data
    assert "timestamp" in data


def test_health_provider_specific_requires_api_key():
    """Test: Endpoint específico requiere API Key."""
    response = client.get("/api/v1/health/providers/gemini")

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"] == "API Key requerida"


def test_health_invalid_provider():
    """Test: Proveedor inválido devuelve error."""
    response = client.get(
        "/api/v1/health/providers/invalid",
        headers={"X-API-Key": "test-api-key"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "no reconocido" in data["error"]
