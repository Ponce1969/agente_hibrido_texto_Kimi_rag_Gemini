"""Endpoint dedicado para Kimi-k2 con búsqueda Bear API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.adapters.dependencies import get_chat_service_dependency
from src.application.services.chat_service import ChatServiceV2

router = APIRouter(prefix="/bear", tags=["bear-search"])


class BearChatRequest(BaseModel):
    """Request para chat con búsqueda Bear."""
    message: str
    session_id: str = "0"
    agent_mode: str = "architect"


class BearChatResponse(BaseModel):
    """Response del chat con búsqueda Bear."""
    response: str
    sources_used: list[dict] = []
    search_performed: bool = False


@router.post("/chat", response_model=BearChatResponse)
async def chat_with_bear_search(
    request: BearChatRequest,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
) -> BearChatResponse:
    """
    Endpoint dedicado para Kimi-k2 con búsqueda en Bear API.

    Este endpoint fuerza el uso de búsqueda en Internet para Kimi-k2,
    ignorando completamente el sistema RAG de Gemini.
    """
    try:
        print(f"🔍 Bear API Endpoint: Recibiendo petición: {request.message}")

        # Forzar búsqueda Bear API directamente
        sources = await service.python_search.search_python_best_practice(request.message)
        print(f"🔍 Bear API: {len(sources)} fuentes encontradas")

        if sources:
            service.last_search_sources = sources
            internet_context = service._build_internet_context(sources)
            print(f"🔍 Bear API: Contexto construido: {len(internet_context)} chars")

            # Construir prompt con contexto
            service._get_system_prompt(request.agent_mode)

            # Usar el servicio directamente sin formato complejo
            response = await service.handle_message(
                session_id=request.session_id,
                user_message=request.message,
                agent_mode=request.agent_mode,
                use_internet=True,
                file_id=None
            )
        else:
            print("🔍 Bear API: Sin resultados, usando fallback")
            response = await service.handle_message(
                session_id=request.session_id,
                user_message=request.message,
                agent_mode=request.agent_mode,
                use_internet=True,
                file_id=None
            )

        # Obtener fuentes usadas
        sources_list = [
            {
                "title": source.title,
                "url": source.url,
                "source_type": source.source_type,
                "reliability": source.reliability
            }
            for source in sources
        ]

        return BearChatResponse(
            response=response,
            sources_used=sources_list,
            search_performed=len(sources) > 0
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
