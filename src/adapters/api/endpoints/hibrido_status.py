"""
Endpoints para el estado del sistema híbrido mejorado.

Muestra información sobre:
- Disponibilidad de modelos (nube y local)
- Routing decisions
- Métricas del sistema híbrido
- Salud de Ollama y APIs
"""

import logging
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.adapters.dependencies import get_chat_service_hibrido_dependency
from src.application.services.chat_service_hibrido_mejorado import (
    ChatServiceHibridoMejorado,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ModelStatus(BaseModel):
    """Estado de un modelo."""
    available: bool
    type: str  # "cloud" o "local"
    name: str
    response_time_ms: int | None = None
    last_check: str


class HybridSystemStatus(BaseModel):
    """Estado completo del sistema híbrido."""
    models: dict[str, ModelStatus]
    routing_enabled: bool
    total_models_available: int
    cloud_models_available: int
    local_models_available: int
    recommended_strategy: str
    system_health: str  # "healthy", "degraded", "critical"


@router.get("/hibrido/status", response_model=HybridSystemStatus, tags=["Híbrido"])
async def get_hybrid_system_status(
    service: ChatServiceHibridoMejorado = Depends(get_chat_service_hibrido_dependency),
):
    """
    Retorna el estado completo del sistema híbrido.

    Útil para monitorear qué modelos están disponibles y
    cómo está funcionando el routing inteligente.
    """
    try:
        # Obtener estado básico del servicio
        basic_status = await service.get_system_status()

        # Construir modelo de respuesta detallado
        models = {}
        cloud_available = 0
        local_available = 0

        for model_name, model_info in basic_status.items():
            if model_name in ["routing_enabled"]:
                continue

            status = ModelStatus(
                available=model_info["available"],
                type=model_info["type"],
                name=model_name,
                last_check="2025-12-09T20:00:00Z",  # TODO: implementar timestamp real
            )

            models[model_name] = status

            if model_info["available"]:
                if model_info["type"] == "cloud":
                    cloud_available += 1
                else:
                    local_available += 1

        total_available = cloud_available + local_available

        # Determinar salud del sistema
        if total_available >= 3:
            system_health = "healthy"
        elif total_available >= 2:
            system_health = "degraded"
        else:
            system_health = "critical"

        # Estrategia recomendada
        if basic_status.get("routing_enabled", False):
            if local_available > 0:
                recommended_strategy = "full_hybrid_cloud_local"
            else:
                recommended_strategy = "cloud_only"
        else:
            recommended_strategy = "cloud_only"

        return HybridSystemStatus(
            models=models,
            routing_enabled=basic_status.get("routing_enabled", False),
            total_models_available=total_available,
            cloud_models_available=cloud_available,
            local_models_available=local_available,
            recommended_strategy=recommended_strategy,
            system_health=system_health,
        )

    except Exception as e:
        logger.error(f"❌ Error getting hybrid status: {e}")
        raise


@router.get("/hibrido/test", tags=["Híbrido"])
async def test_hybrid_system(
    service: ChatServiceHibridoMejorado = Depends(get_chat_service_hibrido_dependency),
):
    """
    Ejecuta una prueba rápida del sistema híbrido.

    Envía una pregunta simple a través del routing
    para verificar que todo funciona correctamente.
    """
    try:
        test_question = "¿Cuál es la diferencia entre una lista y una tupla en Python?"

        logger.info(f"🧪 Testing hybrid system with: {test_question}")

        # Crear sesión de prueba
        session = service.create_session_from_user("hybrid_test")

        # Enviar pregunta de prueba
        start_time = time.time()
        response = await service.handle_message(
            session_id=str(session.id),
            user_message=test_question,
            agent_mode="architect",
            use_internet=False,
        )
        response_time = time.time() - start_time

        return {
            "success": True,
            "test_question": test_question,
            "response": response[:500] + "..." if len(response) > 500 else response,
            "response_time_ms": int(response_time * 1000),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Error testing hybrid system: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


@router.get("/hibrido/models", tags=["Híbrido"])
async def get_available_models(
    service: ChatServiceHibridoMejorado = Depends(get_chat_service_hibrido_dependency),
):
    """
    Retorna lista de modelos disponibles con capacidades.

    Útil para que el frontend muestre opciones dinámicas
    según lo que esté disponible en tiempo real.
    """
    try:
        status = await service.get_system_status()

        models_info = []

        # Kimi-K2
        if status.get("kimi_k2", {}).get("available", False):
            models_info.append({
                "id": "kimi-k2",
                "name": "Kimi-K2",
                "provider": "Groq",
                "type": "cloud",
                "specialties": ["Python", "Code", "General Chat"],
                "recommended_for": ["code_questions", "general_chat"],
                "speed": "fast",
                "context_window": "128k",
            })

        # Gemini
        if status.get("gemini", {}).get("available", False):
            models_info.append({
                "id": "gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "provider": "Google",
                "type": "cloud",
                "specialties": ["RAG", "Long Context", "PDF Analysis"],
                "recommended_for": ["rag_queries", "document_analysis"],
                "speed": "medium",
                "context_window": "1M",
            })

        # LLaMA3.1:8b
        if status.get("llama3_1_8b", {}).get("available", False):
            models_info.append({
                "id": "llama3.1-8b",
                "name": "LLaMA 3.1 8B",
                "provider": "Ollama (Local)",
                "type": "local",
                "specialties": ["General", "Code", "Reasoning"],
                "recommended_for": ["fallback", "offline_use"],
                "speed": "medium",
                "context_window": "128k",
            })

        # Gemma2:2b
        if status.get("gemma2_2b", {}).get("available", False):
            models_info.append({
                "id": "gemma2-2b",
                "name": "Gemma 2 2B",
                "provider": "Ollama (Local)",
                "type": "local",
                "specialties": ["Lightweight", "Quick Responses"],
                "recommended_for": ["emergency_fallback", "quick_tasks"],
                "speed": "fast",
                "context_window": "8k",
            })

        return {
            "models": models_info,
            "total_available": len(models_info),
            "routing_enabled": status.get("routing_enabled", False),
            "last_updated": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Error getting available models: {e}")
        raise
