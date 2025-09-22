"""
Servicio de aplicación que contiene la lógica de negocio principal para el chat.
"""
from typing import Optional, List, Dict, Any
from src.adapters.db.repository import ChatRepository
from src.adapters.agents.groq_client import GroqClient
from src.adapters.agents.gemini_client import GeminiClient
from src.adapters.agents.prompts import AgentMode, get_system_prompt
from src.adapters.db.message import ChatMessageCreate, MessageRole
from src.adapters.db.chat import ChatSession, ChatSessionCreate
from src.adapters.db.file_models import FileUpload, FileSection
from src.adapters.config.settings import settings

import io
from pypdf import PdfReader  # type: ignore
import httpx

class ChatService:
    """Orquesta la lógica del chat."""

    def __init__(self, repo: ChatRepository, client: GroqClient, gemini: GeminiClient):
        self.repo = repo
        self.client = client
        self.gemini = gemini

    def create_new_session(self, user_id: str, session_name: Optional[str] = None) -> ChatSession:
        """Crea una nueva sesión de chat para un usuario."""
        session_create = ChatSessionCreate(user_id=user_id, session_name=session_name)
        return self.repo.create_session(session_create)

    async def handle_chat_message(
        self,
        session_id: int,
        user_message: str,
        agent_mode: AgentMode,
        file_id: Optional[int] = None,
        selected_section_ids: Optional[List[int]] = None,
        use_gemini_fallback: Optional[bool] = None,
    ) -> str:
        """Maneja un nuevo mensaje de usuario y retorna la respuesta de la IA."""
        # 1. Guardar el mensaje del usuario
        self.repo.add_message(
            ChatMessageCreate(
                session_id=session_id,
                role=MessageRole.USER,
                content=user_message,
                message_index=0 # El repositorio calculará el índice correcto
            )
        )

        # 2. Obtener el historial de la conversación
        history = self.repo.get_session_messages(session_id)

        # 3. Obtener el prompt del sistema para el agente seleccionado
        system_prompt = get_system_prompt(agent_mode)

        # Helper: transformar historial a formato OpenAI-compatible
        def build_openai_messages() -> List[Dict[str, Any]]:
            msgs: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
            for m in history:
                msgs.append({"role": m.role.value, "content": m.content})
            # Último mensaje del usuario ya está en history; no hace falta añadir de nuevo
            return msgs

        # Si el usuario seleccionó secciones explícitas, construir un contexto conciso y hacer UNA llamada
        if file_id is not None and selected_section_ids:
            from sqlmodel import select
            texts: List[str] = []
            total_chars = 0
            limit = settings.file_context_max_chars
            # Traer en orden los textos de las secciones seleccionadas
            for sid in selected_section_ids:
                sec = self.repo.session.get(FileSection, sid)
                if not sec:
                    continue
                fu = self.repo.session.get(FileUpload, sec.file_id)
                if not fu:
                    continue
                with open(fu.path, "rb") as f:
                    raw = f.read()
                reader = PdfReader(io.BytesIO(raw))
                parts: List[str] = []
                for idx in range(sec.start_page, sec.end_page + 1):
                    try:
                        txt = reader.pages[idx].extract_text() or ""
                    except Exception:
                        txt = ""
                    parts.append(txt)
                section_text = "\n".join(parts)
                # Añadir mientras no superemos el límite
                remaining = limit - total_chars
                if remaining <= 0:
                    break
                texts.append(section_text[:remaining])
                total_chars += min(len(section_text), remaining)

            context = "\n\n".join(texts)
            short_prompt = (
                f"Usa exclusivamente el siguiente contexto de PDF seleccionado para responder de forma concisa.\n"
                f"--- CONTEXTO ---\n{context}\n--- FIN CONTEXTO ---\n\n"
                f"Pregunta: {user_message}"
            )
            # Añadir mensaje USER adicional al historial para mantener trazabilidad
            history = self.repo.get_session_messages(session_id)
            system_prompt = get_system_prompt(agent_mode)
            # Llamada única con menor max_tokens para ahorrar cuota
            prefer_gemini = (
                (settings.llm_provider_preference == "gemini_for_pdf_kimi_for_chat")
                or bool(use_gemini_fallback)
            ) and self.gemini is not None

            if prefer_gemini:
                ai_response_content = await self.gemini.get_chat_completion(
                    system_prompt=system_prompt,
                    messages=history + [type('Obj', (), {'role': MessageRole.USER, 'content': short_prompt})()],
                    max_tokens=min(768, settings.max_tokens),
                    temperature=settings.temperature,
                )
            else:
                try:
                    ai_response_content = await self.client.get_chat_completion(
                        system_prompt=system_prompt,
                        messages=history + [
                            type('Obj', (), {'role': MessageRole.USER, 'content': short_prompt})(),
                        ],
                        max_tokens=min(768, settings.max_tokens),
                    )
                except httpx.HTTPStatusError as e:
                    # Fallback a Gemini si hay 429 de Kimi
                    if e.response is not None and e.response.status_code == 429 and self.gemini:
                        ai_response_content = await self.gemini.get_chat_completion(
                            system_prompt=system_prompt,
                            messages=history + [type('Obj', (), {'role': MessageRole.USER, 'content': short_prompt})()],
                            max_tokens=min(768, settings.max_tokens),
                            temperature=settings.temperature,
                        )
                    else:
                        raise
            # Guardar respuesta
            self.repo.add_message(
                ChatMessageCreate(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=ai_response_content,
                    message_index=0,
                )
            )
            return ai_response_content

        # Tools para PDFs grandes si file_id está presente y NO hay selección explícita
        if file_id is not None:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "list_sections",
                        "description": "Lista secciones del PDF por rangos de páginas",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_id": {"type": "integer"}
                            },
                            "required": ["file_id"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_section_text",
                        "description": "Obtiene texto truncado de una sección específica",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "section_id": {"type": "integer"}
                            },
                            "required": ["section_id"],
                        },
                    },
                },
            ]

            # Funciones reales
            def exec_list_sections(fid: int) -> str:
                from sqlmodel import select
                secs = self.repo.session.exec(
                    select(FileSection).where(FileSection.file_id == fid).order_by(FileSection.start_page)
                ).all()
                items = [
                    {
                        "id": s.id,
                        "start_page": s.start_page,
                        "end_page": s.end_page,
                        "char_count": s.char_count,
                    }
                    for s in secs
                ]
                import json
                return json.dumps({"sections": items})

            def exec_get_section_text(section_id: int) -> str:
                sec = self.repo.session.get(FileSection, section_id)
                if not sec:
                    return "{}"
                fu = self.repo.session.get(FileUpload, sec.file_id)
                if not fu:
                    return "{}"
                with open(fu.path, "rb") as f:
                    raw = f.read()
                reader = PdfReader(io.BytesIO(raw))
                parts: List[str] = []
                for idx in range(sec.start_page, sec.end_page + 1):
                    try:
                        txt = reader.pages[idx].extract_text() or ""
                    except Exception:
                        txt = ""
                    parts.append(txt)
                text = "\n".join(parts)
                if len(text) > settings.file_context_max_chars:
                    text = text[: settings.file_context_max_chars]
                import json
                return json.dumps({"text": text})

            # Orquestación tool-calling (hasta 3 pasos)
            messages_openai = build_openai_messages()
            iterations = 0
            while iterations < 3:
                iterations += 1
                # Limitar tokens en llamadas con tools para evitar 429 por TPD
                try:
                    result = await self.client.chat_with_tools(
                        messages_openai, tools, tool_choice="auto", max_tokens=min(1024, settings.max_tokens)
                    )
                except httpx.HTTPStatusError as e:
                    # Fallback básico: responder sin acceder al PDF (ahorro de tokens)
                    if e.response is not None and e.response.status_code == 429 and self.gemini:
                        # Respuesta acotada sin contexto para no fallar la UX
                        ai_response_content = await self.gemini.get_chat_completion(
                            system_prompt=system_prompt,
                            messages=history,
                            max_tokens=min(512, settings.max_tokens),
                            temperature=settings.temperature,
                        )
                        self.repo.add_message(
                            ChatMessageCreate(
                                session_id=session_id,
                                role=MessageRole.ASSISTANT,
                                content=ai_response_content,
                                message_index=0
                            )
                        )
                        return ai_response_content
                    else:
                        raise
                choice = result.get("choices", [{}])[0]
                msg = choice.get("message", {})
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    # Ejecutar tools y adjuntar outputs
                    for call in tool_calls:
                        fn = call["function"]["name"]
                        import json
                        args = json.loads(call["function"].get("arguments", "{}"))
                        output = "{}"
                        if fn == "list_sections":
                            output = exec_list_sections(args.get("file_id", file_id))
                        elif fn == "get_section_text":
                            output = exec_get_section_text(args.get("section_id"))
                        # Añadir mensaje de tool
                        messages_openai.append(
                            {
                                "role": "tool",
                                "tool_call_id": call.get("id", ""),
                                "name": fn,
                                "content": output,
                            }
                        )
                    # También añadimos el mensaje del assistant que solicitó tool_calls
                    messages_openai.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls})
                    continue
                # Respuesta final
                content = msg.get("content") or ""
                # 5. Guardar la respuesta de la IA
                self.repo.add_message(
                    ChatMessageCreate(
                        session_id=session_id,
                        role=MessageRole.ASSISTANT,
                        content=content,
                        message_index=0
                    )
                )
                return content

        # 4. Llamada estándar sin tools
        ai_response_content = await self.client.get_chat_completion(
            system_prompt=system_prompt,
            messages=history
        )

        # 5. Guardar la respuesta de la IA
        self.repo.add_message(
            ChatMessageCreate(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=ai_response_content,
                message_index=0 # El repositorio calculará el índice correcto
            )
        )

        # 6. Retornar la respuesta de la IA
        return ai_response_content
