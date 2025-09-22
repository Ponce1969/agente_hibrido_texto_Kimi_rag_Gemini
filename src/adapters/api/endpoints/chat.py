"""
Endpoints de la API para gestionar el chat.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
import traceback
from pydantic import BaseModel
from sqlmodel import Session

from src.adapters.db.database import get_session
from src.adapters.db.repository import ChatRepository
from src.adapters.agents.groq_client import GroqClient
from src.application.services.chat_service import ChatService
from src.adapters.agents.gemini_client import GeminiClient
from src.adapters.agents.prompts import AgentMode

router = APIRouter()

# --- Inyección de Dependencias ---

def get_groq_client() -> GroqClient:
    """Dependency para obtener el cliente de Groq."""
    return GroqClient(client=httpx.AsyncClient())


def get_chat_service(
    session: Session = Depends(get_session),
    client: GroqClient = Depends(get_groq_client),
) -> ChatService:
    """Dependency para obtener el servicio de chat."""
    repo = ChatRepository(session)
    gemini = GeminiClient(client=httpx.AsyncClient())
    return ChatService(repo, client, gemini)


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
