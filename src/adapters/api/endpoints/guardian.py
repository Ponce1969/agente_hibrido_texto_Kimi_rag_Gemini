"""
Endpoints para gestión y monitoreo del Guardian.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from src.application.services.guardian_service import GuardianService
from src.adapters.dependencies import get_guardian_service

router = APIRouter(prefix="/guardian", tags=["Guardian"])


@router.get("/stats", response_model=Dict[str, Any])
async def get_guardian_stats(
    guardian_service: GuardianService = Depends(get_guardian_service)
) -> Dict[str, Any]:
    """
    Obtiene estadísticas del Guardian.
    
    Returns:
        Métricas de uso, caché, rate limiting, etc.
    """
    service_metrics = guardian_service.get_metrics()
    client_stats = await guardian_service.client.get_stats()
    
    return {
        "service": service_metrics,
        "client": client_stats,
        "enabled": await guardian_service.client.is_enabled(),
    }


@router.post("/clear-cache")
async def clear_guardian_cache(
    guardian_service: GuardianService = Depends(get_guardian_service)
) -> Dict[str, str]:
    """
    Limpia el caché del Guardian.
    
    Returns:
        Mensaje de confirmación
    """
    guardian_service.clear_cache()
    return {"message": "Caché del Guardian limpiado exitosamente"}


@router.post("/test")
async def test_guardian(
    message: str,
    guardian_service: GuardianService = Depends(get_guardian_service)
) -> Dict[str, Any]:
    """
    Prueba el Guardian con un mensaje.
    
    Args:
        message: Mensaje a analizar
        
    Returns:
        Resultado del análisis
    """
    result = await guardian_service.check_message(message, user_id="test")
    
    return {
        "is_safe": result.is_safe,
        "threat_level": result.threat_level.value,
        "reason": result.reason,
        "confidence": result.confidence,
        "categories": result.categories,
        "checked_at": result.checked_at.isoformat() if result.checked_at else None,
    }
