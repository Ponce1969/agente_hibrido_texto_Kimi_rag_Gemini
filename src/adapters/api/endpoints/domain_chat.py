"""
Endpoint de chat refactorizado para usar el Domain Layer.

Este endpoint ahora usa el servicio de aplicación que implementa
la arquitectura hexagonal correctamente.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
import traceback
from pydantic import BaseModel
from sqlmodel import Session

from ..db.database import get_session
from ..application.services.domain_chat_service import ChatApplicationService
from ..agents.prompts import AgentMode
from ..domain import ChatSessionNotFoundError, InvalidMessageError, AIProviderError

router = APIRouter()

# --- Inyección de Dependencias ---

def get_chat_application_service() -> ChatApplicationService:
    """Dependency para obtener el servicio de aplicación."""
    return ChatApplicationService()

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
async def create_new_session(
    request: NewSessionRequest,
    service: ChatApplicationService = Depends(get_chat_application_service),
):
    """Crea una nueva sesión de chat."""
    try:
        session = await service.create_new_session(user_id=request.user_id)
        return NewSessionResponse(session_id=session.id)
    except ValueError as e:
        # Errores de validación del dominio
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Errores inesperados
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"create_new_session error: {e}\n{tb}")


@router.post("/chat", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    service: ChatApplicationService = Depends(get_chat_application_service),
):
    """Maneja un mensaje de chat y devuelve la respuesta de la IA."""
    try:
        reply = await service.handle_chat_message(
            session_id=request.session_id,
            user_id="current_user",  # TODO: Obtener de autenticación
            user_message=request.message,
            agent_mode=request.mode,
            file_id=request.file_id,
            selected_section_ids=request.selected_section_ids,
            use_gemini_fallback=request.use_gemini_fallback,
        )
        return ChatResponse(reply=reply)
    except ChatSessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Sesión no encontrada: {e}")
    except InvalidMessageError as e:
        raise HTTPException(status_code=400, detail=f"Mensaje inválido: {e}")
    except AIProviderError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error en el servicio de IA: {e}"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error en la API de IA: {e.response.text}",
        )
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"handle_chat error: {e}\n{tb}")


@router.get("/sessions/{user_id}")
async def get_user_sessions(
    user_id: str,
    service: ChatApplicationService = Depends(get_chat_application_service),
):
    """Obtiene todas las sesiones de un usuario."""
    try:
        sessions = await service.get_user_sessions(user_id)
        return {
            "sessions": [
                {
                    "id": session.id,
                    "session_name": session.session_name,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "is_active": session.is_active,
                    "message_count": session.get_message_count(),
                }
                for session in sessions
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"get_user_sessions error: {e}\n{tb}")


@router.get("/sessions/{user_id}/{session_id}/messages")
async def get_session_messages(
    user_id: str,
    session_id: int,
    service: ChatApplicationService = Depends(get_chat_application_service),
):
    """Obtiene los mensajes de una sesión específica."""
    try:
        messages = await service.get_session_messages(session_id, user_id)
        return {
            "messages": [
                {
                    "id": getattr(msg, 'id', None),  # TODO: Agregar ID a domain model
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "message_index": msg.message_index,
                }
                for msg in messages
            ]
        }
    except ChatSessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Sesión no encontrada: {e}")
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"get_session_messages error: {e}\n{tb}")
