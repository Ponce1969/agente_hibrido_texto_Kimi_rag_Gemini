"""
API endpoints para métricas de tokens y caché de prompts.
"""

from fastapi import APIRouter
from src.adapters.agents.prompt_manager import prompt_manager

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/session/{session_id}")
async def get_session_metrics(session_id: str):
    """
    Obtiene métricas de tokens para una sesión específica.
    
    Returns:
        Estadísticas de la sesión incluyendo tokens ahorrados
    """
    stats = prompt_manager.get_session_stats(session_id)
    return {
        "session_id": session_id,
        "stats": stats
    }


@router.get("/global")
async def get_global_metrics():
    """
    Obtiene métricas globales de todas las sesiones.
    
    Returns:
        Estadísticas globales del sistema
    """
    stats = prompt_manager.get_global_stats()
    return {
        "global_stats": stats,
        "total_sessions": stats["total_sessions"],
        "total_calls": stats["total_calls"],
        "total_tokens_used": stats["total_tokens"],
        "total_tokens_saved": stats["total_saved"],
        "savings_percentage": stats["savings_percentage"]
    }


@router.get("/recent")
async def get_recent_metrics(limit: int = 10):
    """
    Obtiene las métricas más recientes.
    
    Args:
        limit: Número de métricas a retornar
        
    Returns:
        Lista de métricas recientes
    """
    recent = prompt_manager.metrics[-limit:] if prompt_manager.metrics else []
    
    return {
        "count": len(recent),
        "metrics": [
            {
                "session_id": m.session_id,
                "call_number": m.call_number,
                "total_tokens": m.total_tokens,
                "system_tokens": m.system_tokens,
                "history_tokens": m.history_tokens,
                "user_tokens": m.user_tokens,
                "is_cached": m.is_cached
            }
            for m in recent
        ]
    }


@router.delete("/cache/{session_id}")
async def clear_session_cache(session_id: str):
    """
    Limpia el caché de una sesión específica.
    
    Args:
        session_id: ID de la sesión a limpiar
        
    Returns:
        Confirmación de limpieza
    """
    prompt_manager.clear_session_cache(session_id)
    return {
        "message": f"Cache cleared for session {session_id}",
        "session_id": session_id
    }
