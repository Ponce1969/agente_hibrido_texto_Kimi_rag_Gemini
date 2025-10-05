"""
Endpoints de la API para gestionar el chat.

REFACTORIZADO: Usa arquitectura hexagonal con ChatServiceV2
"""
from fastapi import APIRouter, Depends, HTTPException, Query
import traceback
from pydantic import BaseModel
from sqlmodel import Session

from src.adapters.db.database import get_session
from src.adapters.dependencies import get_chat_service_dependency
from src.application.services.chat_service_v2 import ChatServiceV2
from src.adapters.agents.prompts import AgentMode

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
    service: ChatService = Depends(get_chat_service),
):
    """Crea una nueva sesión de chat."""
    try:
        session = service.create_new_session(user_id=request.user_id)
        return NewSessionResponse(session_id=session.id)
    except Exception as e:
        # Devolver detalle para facilitar diagnóstico en desarrollo
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"create_new_session error: {e}\n{tb}")


@router.post("/chat", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Maneja un mensaje de chat y devuelve la respuesta de la IA."""
    try:
        reply = await service.handle_chat_message(
            session_id=request.session_id,
            user_message=request.message,
            agent_mode=request.mode,
            file_id=request.file_id,
            selected_section_ids=request.selected_section_ids,
            use_gemini_fallback=request.use_gemini_fallback,
        )
        return ChatResponse(reply=reply)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error en la API de IA: {e.response.text}",
        )
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"handle_chat error: {e}\n{tb}")


class ChatMessageDTO(BaseModel):
    role: str
    content: str
    index: int


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageDTO])
def get_session_messages_api(
    session_id: int,
    session: Session = Depends(get_session),
):
    """Devuelve los mensajes persistidos para una sesión de chat."""
    try:
        repo = ChatRepository(session)
        msgs = repo.get_session_messages(session_id)
        return [
            ChatMessageDTO(role=m.role.value, content=m.content, index=m.message_index)
            for m in msgs
        ]
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"get_session_messages error: {e}\n{tb}")


class SessionSummaryDTO(BaseModel):
    id: int
    user_id: str
    session_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@router.get("/sessions", response_model=list[SessionSummaryDTO])
def list_sessions(
    user_id: str = Query(..., description="Usuario dueño de las sesiones"),
    limit: int = Query(30, ge=1, le=200),
    session: Session = Depends(get_session),
):
    try:
        repo = ChatRepository(session)
        items = repo.get_user_sessions(user_id=user_id, limit=limit)
        out: list[SessionSummaryDTO] = []
        for s in items:
            out.append(
                SessionSummaryDTO(
                    id=s.id,
                    user_id=s.user_id,
                    session_name=getattr(s, "session_name", None),
                    created_at=s.created_at.isoformat() if getattr(s, "created_at", None) else None,
                    updated_at=s.updated_at.isoformat() if getattr(s, "updated_at", None) else None,
                )
            )
        return out
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"list_sessions error: {e}\n{tb}")


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, session: Session = Depends(get_session)):
    try:
        repo = ChatRepository(session)
        ok = repo.delete_session(session_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"delete_session error: {e}\n{tb}")
