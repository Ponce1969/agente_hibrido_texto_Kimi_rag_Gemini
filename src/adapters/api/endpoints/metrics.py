"""Endpoints para métricas y dashboard."""
from fastapi import APIRouter, Query
from typing import Dict, List
from src.application.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])
metrics_service = MetricsService()


@router.get("/summary")
async def get_metrics_summary(
    days: int = Query(default=7, ge=1, le=365, description="Días a consultar")
) -> Dict:
    """
    Obtener resumen de métricas.
    
    Args:
        days: Cantidad de días a consultar (1-365)
    
    Returns:
        Dict con resumen de métricas
    """
    return metrics_service.get_metrics_summary(days=days)


@router.get("/daily")
async def get_daily_metrics(
    days: int = Query(default=30, ge=1, le=365, description="Días a consultar")
) -> List[Dict]:
    """
    Obtener métricas diarias para gráficos.
    
    Args:
        days: Cantidad de días a consultar (1-365)
    
    Returns:
        Lista de métricas diarias
    """
    return metrics_service.get_daily_metrics(days=days)


@router.get("/top-agents")
async def get_top_agents(
    days: int = Query(default=7, ge=1, le=365, description="Días a consultar"),
    limit: int = Query(default=5, ge=1, le=20, description="Cantidad de agentes")
) -> List[Dict]:
    """
    Obtener agentes más usados.
    
    Args:
        days: Cantidad de días a consultar
        limit: Cantidad máxima de agentes a retornar
    
    Returns:
        Lista de agentes ordenados por uso
    """
    return metrics_service.get_top_agents(days=days, limit=limit)


@router.get("/errors")
async def get_recent_errors(
    limit: int = Query(default=10, ge=1, le=100, description="Cantidad de errores")
) -> List[Dict]:
    """
    Obtener errores recientes.
    
    Args:
        limit: Cantidad máxima de errores a retornar
    
    Returns:
        Lista de errores recientes
    """
    return metrics_service.get_recent_errors(limit=limit)
