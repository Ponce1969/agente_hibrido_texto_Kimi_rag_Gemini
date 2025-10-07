"""
Endpoints de la API para gestionar el chat.

MIGRADO: Usa ChatServiceV2 con arquitectura hexagonal
"""
from fastapi import APIRouter, Depends, HTTPException, Query
import traceback
from pydantic import BaseModel

from src.adapters.dependencies import get_chat_service_dependency
from src.application.services.chat_service import ChatServiceV2
from src.adapters.agents.prompts import AgentMode
from src.domain.models.chat_models import ChatSessionCreate

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
        from datetime import datetime, UTC
        session_data = ChatSessionCreate(
            user_id=request.user_id,
            title=f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"  # El modelo de dominio usa 'title'
        )
        session = service.create_session(session_data)
        return NewSessionResponse(session_id=int(session.id))
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"create_new_session error: {e}\n{tb}")


@router.post("/chat", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Maneja un mensaje de chat y devuelve la respuesta de la IA."""
    try:
        # DEBUG: Log de request
        print(f"🔍 [CHAT ENDPOINT] Request recibida:")
        print(f"   session_id: {request.session_id}")
        print(f"   message: {request.message[:100]}...")
        print(f"   mode: {request.mode.value}")
        print(f"   file_id: {request.file_id}")  # ✅ CRÍTICO
        print(f"   use_gemini_fallback: {request.use_gemini_fallback}")
        
        # handle_message maneja automáticamente la creación de sesión si es necesario
        reply = await service.handle_message(
            session_id=str(request.session_id),
            user_message=request.message,
            agent_mode=request.mode.value,
            file_id=request.file_id,  # ✅ Pasar file_id para RAG
        )
        return ChatResponse(reply=reply)
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
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Devuelve los mensajes persistidos para una sesión de chat."""
    try:
        session = service.get_session(str(session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return [
            ChatMessageDTO(role=m.role.value, content=m.content, index=m.message_index)
            for m in session.messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"get_session_messages error: {e}\n{tb}")


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
    try:
        sessions = service.list_sessions(limit=limit)
        out: list[SessionSummaryDTO] = []
        for s in sessions:
            # Filtrar por user_id si es necesario
            if s.user_id == user_id:
                # Contar mensajes dinámicamente
                msg_count = service.repo.count_session_messages(str(s.id))
                
                out.append(
                    SessionSummaryDTO(
                        id=int(s.id),
                        user_id=s.user_id,
                        session_name=s.session_name if hasattr(s, 'session_name') else None,
                        message_count=msg_count,
                        created_at=s.created_at.isoformat() if s.created_at else None,
                        updated_at=s.updated_at.isoformat() if s.updated_at else None,
                    )
                )
        return out[:limit]
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"list_sessions error: {e}\n{tb}")


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
    """Elimina una sesión de chat."""
    try:
        ok = service.repo.delete_session(str(session_id))
        if not ok:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"delete_session error: {e}\n{tb}")
