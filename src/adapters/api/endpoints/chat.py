"""
Endpoints de la API para gestionar el chat.

MIGRADO: Usa ChatServiceV2 con arquitectura hexagonal
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.adapters.agents.prompts import AgentMode
from src.adapters.dependencies import get_chat_service_dependency
from src.application.services.chat_service import ChatServiceV2

logger = logging.getLogger(__name__)

# Configurar limiter para este router
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


# --- Schemas de la API (Pydantic) ---

class ChatRequest(BaseModel):
    session_id: int
    message: str
    mode: AgentMode
    file_id: int | None = None
    selected_section_ids: list[int] | None = None
    use_gemini_fallback: bool | None = None

class ChatResponse(BaseModel):
    reply: str

class NewSessionRequest(BaseModel):
    user_id: str

class NewSessionResponse(BaseModel):
    session_id: int

# --- Endpoints ---

@router.post("/sessions", response_model=NewSessionResponse, status_code=201)
def create_new_session(
    request: NewSessionRequest,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Crea una nueva sesión de chat."""
    try:
        session = service.create_session_from_user(request.user_id)
        return NewSessionResponse(session_id=session.id)
    except Exception as e:
        logger.error(f"Error al crear sesión: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear la sesión")


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # Límite: 10 requests por minuto (consume tokens LLM)
async def handle_chat(
    request: Request,
    chat_request: ChatRequest,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Maneja un mensaje de chat y devuelve la respuesta de la IA."""
    try:
        logger.info(f"Request de chat recibida para sesión {chat_request.session_id}")
        logger.debug(f"Detalles del request: {chat_request.model_dump_json()}")

        reply = await service.handle_message(
            session_id=str(chat_request.session_id),
            user_message=chat_request.message,
            agent_mode=chat_request.mode.value,
            file_id=chat_request.file_id,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error(f"Error en handle_chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al procesar el mensaje")


class ChatMessageDTO(BaseModel):
    role: str
    content: str
    index: int


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageDTO])
def get_session_messages_api(
    session_id: int,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Devuelve los mensajes persistidos para una sesión de chat."""
    try:
        messages = service.get_session_messages(str(session_id))
        if not messages:
            # Aún si la sesión existe pero no tiene mensajes, devolvemos 200 con lista vacía
            session = service.get_session(str(session_id))
            if not session:
                 raise HTTPException(status_code=404, detail="Sesión no encontrada")

        return [
            ChatMessageDTO(role=m.role.value, content=m.content, index=m.message_index)
            for m in messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener mensajes de sesión {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al obtener mensajes")


class SessionSummaryDTO(BaseModel):
    id: int
    user_id: str
    session_name: str | None = None
    message_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


@router.get("/sessions", response_model=list[SessionSummaryDTO])
def list_sessions(
    user_id: str = Query(..., description="Usuario dueño de las sesiones"),
    limit: int = Query(30, ge=1, le=200),
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Lista las sesiones de un usuario con detalles."""
    try:
        sessions_details = service.list_sessions_for_user(user_id, limit)
        return [SessionSummaryDTO(**details) for details in sessions_details]
    except Exception as e:
        logger.error(f"Error al listar sesiones para el usuario {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al listar sesiones")


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Elimina una sesión de chat."""
    try:
        success = service.delete_session(str(session_id))
        if not success:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return None  # HTTP 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar sesión {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al eliminar la sesión")
