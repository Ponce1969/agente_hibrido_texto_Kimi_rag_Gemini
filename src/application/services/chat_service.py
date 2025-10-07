"""
Servicio de aplicación de chat refactorizado con arquitectura hexagonal.

Este servicio usa SOLO puertos (interfaces) del dominio, sin dependencias
de implementaciones concretas (adapters).

Tipado estricto para mypy --strict con Python 3.12+
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.ports import LLMPort, ChatRepositoryPort, EmbeddingsPort
    from src.domain.models import ChatSession, ChatMessage, ChatSessionCreate, ChatMessageCreate
    from src.application.services.embeddings_service_v2 import EmbeddingsServiceV2


class ChatServiceV2:
    """
    Servicio de aplicación para chat siguiendo arquitectura hexagonal.
    
    Este servicio orquesta la lógica de negocio sin conocer detalles
    de implementación (Groq, Gemini, SQLite, PostgreSQL, etc.).
    
    Principios:
    - Depende SOLO de puertos (interfaces)
    - No importa de adapters
    - Lógica de negocio pura
    - Fácil de testear con mocks
    """
    
    def __init__(
        self,
        llm_client: LLMPort,
        repository: ChatRepositoryPort,
        *,
        fallback_llm: LLMPort | None = None,
        embeddings_service: EmbeddingsServiceV2 | None = None,
    ) -> None:
        """
        Inicializa el servicio de chat.
        
        Args:
            llm_client: Cliente LLM principal (ej: Groq)
            repository: Repositorio de chat
            fallback_llm: Cliente LLM de respaldo (ej: Gemini)
            embeddings_service: Servicio de embeddings para RAG (opcional)
        """
        self.llm = llm_client
        self.repo = repository
        self.fallback_llm = fallback_llm
        self.embeddings = embeddings_service
    
    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """
        Crea una nueva sesión de chat.
        
        Args:
            session_data: Datos para crear la sesión
            
        Returns:
            Sesión creada
        """
        return self.repo.create_session(session_data)
    
    def get_session(self, session_id: str) -> ChatSession | None:
        """
        Obtiene una sesión por su ID.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Sesión encontrada o None
        """
        return self.repo.get_session(session_id)
    
    def list_sessions(self, *, limit: int = 50) -> list[ChatSession]:
        """
        Lista las sesiones de chat.
        
        Args:
            limit: Número máximo de sesiones
            
        Returns:
            Lista de sesiones
        """
        return self.repo.list_sessions(limit=limit)
    
    async def handle_message(
        self,
        session_id: str,
        user_message: str,
        *,
        agent_mode: str = "architect",
        file_id: int | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        use_fallback_on_error: bool = True,
    ) -> str:
        """
        Maneja un mensaje del usuario y retorna la respuesta del LLM.
        
        Args:
            session_id: ID de la sesión
            user_message: Mensaje del usuario
            agent_mode: Modo del agente (architect, code_generator, etc.)
            file_id: ID del archivo PDF para RAG (opcional)
            max_tokens: Tokens máximos de respuesta
            temperature: Temperatura del modelo
            use_fallback_on_error: Si usar LLM de respaldo en caso de error
            
            Respuesta del LLM
            
        Raises:
            ValueError: Si la sesión no existe
        """
        # 1. Validar o crear sesión
        if session_id == "0" or not session_id:
            # Crear nueva sesión si no existe
            from datetime import datetime, UTC
            from src.domain.models import ChatSessionCreate
            
            session_data = ChatSessionCreate(
                user_id="streamlit_user",
                title=f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
            )
            new_session = self.repo.create_session(session_data)
            session_id = str(new_session.id)
        else:
            # Validar que la sesión existe
            session = self.repo.get_session(session_id)
            if not session:
                raise ValueError(f"Sesión {session_id} no encontrada")
        
        # 2. Guardar mensaje del usuario
        from src.domain.models import ChatMessageCreate, MessageRole
        
        user_msg_data = ChatMessageCreate(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
        )
        self.repo.add_message(user_msg_data)
        
        # 3. Obtener historial de mensajes
        history = self.repo.get_session_messages(session_id)
        
        # 4. Buscar contexto RAG si hay file_id
        rag_context = ""
        if file_id and self.embeddings:
            try:
                # Buscar chunks relevantes
                results = await self.embeddings.search_similar(
                    query=user_message,
                    file_id=str(file_id),
                    top_k=5
                )
                
                if results:
                    print(f"✅ RAG: {len(results)} chunks encontrados para file_id={file_id}")
                    # Construir contexto con límite de 8000 caracteres
                    limit = 8000
                    acc = 0
                    parts: list[str] = []
                    
                    for r in results:
                        remaining = limit - acc
                        if remaining <= 100:  # Mínimo para que valga la pena
                            break
                        
                        # EmbeddingsServiceV2 retorna 'text', no 'content'
                        content = r.get('text', '')
                        chunk_idx = r.get('chunk_index', 0)
                        similarity = r.get('similarity', 0.0)
                        
                        if not content:
                            print(f"⚠️ Chunk {chunk_idx} sin contenido: {r.keys()}")
                            continue
                        
                        snippet = content[:remaining]
                        parts.append(f"[chunk {chunk_idx}, score={similarity:.3f}]\n{snippet}")
                        acc += len(snippet)
                    
                    rag_context = "\n\n".join(parts)
                    print(f"📄 Contexto RAG: {acc} caracteres de {len(parts)} chunks")
                    print(f"🔍 Preview contexto: {rag_context[:300]}...")
                else:
                    print(f"⚠️ RAG: No se encontraron chunks para file_id={file_id}")
            except Exception as e:
                print(f"❌ Error en búsqueda RAG: {e}")
                import traceback
                traceback.print_exc()
        
        # 5. Construir system prompt
        system_prompt = self._get_system_prompt(agent_mode)
        
        # Si hay contexto RAG, PRIORIZAR el contexto del PDF
        if rag_context:
            # Prompt EXPLÍCITO que identifica el archivo
            system_prompt = (
                f"Eres un asistente experto en análisis de documentos. El usuario ha cargado un documento PDF (identificado como file_id={file_id}).\n\n"
                "**INSTRUCCIONES CRÍTICAS:**\n"
                f"1. Tienes acceso COMPLETO al contenido del documento file_id={file_id}\n"
                "2. El contenido del documento se proporciona a continuación\n"
                "3. Cuando el usuario pregunte por 'file_id={file_id}', se refiere al documento que tienes aquí\n"
                "4. NUNCA digas 'no tengo acceso' - SÍ tienes el documento completo abajo\n\n"
                f"--- CONTENIDO COMPLETO DEL DOCUMENTO file_id={file_id} ---\n\n"
                f"{rag_context}\n\n"
                "--- FIN DEL DOCUMENTO ---\n\n"
                "Responde todas las preguntas basándote en este contenido. Si te preguntan si ves el documento, responde SÍ."
            )
            print(f"🎯 System prompt RAG: {len(system_prompt)} caracteres")
        
        # 6. Obtener respuesta del LLM
        # IMPORTANTE: Sistema híbrido
        # - RAG (con file_id) → Gemini 2.5 (fallback_llm)
        # - Chat normal → Kimi-K2 (llm)
        
        if rag_context and self.fallback_llm:
            # RAG: Usar Gemini (mejor para contextos largos)
            print(f"🤖 Usando Gemini 2.5 para RAG")
            
            try:
                response, tokens = await self.fallback_llm.get_chat_completion(
                    system_prompt=system_prompt,
                    messages=history,
                    max_tokens=max_tokens or 2048,  # Más tokens para RAG
                    temperature=temperature or 0.3,
                )
            except Exception as e:
                print(f"❌ Error en Gemini: {e}")
                raise
        else:
            # Chat normal: Usar Kimi-K2 (más rápido)
            print(f"🤖 Usando Kimi-K2 para chat normal")
            
            try:
                response, tokens = await self.llm.get_chat_completion(
                    system_prompt=system_prompt,
                    messages=history,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    session_id=session_id,
                    agent_mode=agent_mode,
                    use_cache=True,  # Caché solo para chat normal
                )
            except Exception as e:
                # Fallback a Gemini si Kimi falla
                if use_fallback_on_error and self.fallback_llm:
                    print(f"⚠️ Kimi-K2 falló, usando Gemini como fallback")
                    response, tokens = await self.fallback_llm.get_chat_completion(
                        system_prompt=system_prompt,
                        messages=history,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                else:
                    raise
        
        # 6. Guardar respuesta del asistente
        assistant_msg_data = ChatMessageCreate(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response,
        )
        self.repo.add_message(assistant_msg_data)
        
        return response
    
    def _get_system_prompt(self, agent_mode: str) -> str:
        """
        Obtiene el system prompt para un modo de agente.
        
        Args:
            agent_mode: Modo del agente
            
        Returns:
            System prompt
        """
        # Prompts básicos por modo
        prompts = {
            "architect": (
                "Eres un arquitecto de software senior especializado en Python 3.12+. "
                "Produces código mantenible siguiendo arquitectura hexagonal, SOLID y Clean Code. "
                "Usas FastAPI, SQLModel, Pydantic v2, pytest. "
                "Siempre incluyes type hints completos y docstrings."
            ),
            "code_generator": (
                "Eres un ingeniero de código especializado en Python 3.12+. "
                "Generas soluciones eficientes y modernas. "
                "Usas FastAPI, SQLAlchemy, asyncio. "
                "Código listo para producción con tests."
            ),
            "security_analyst": (
                "Eres un auditor de seguridad especializado en Python. "
                "Identificas vulnerabilidades OWASP Top 10. "
                "Usas bandit, semgrep, pip-audit. "
                "Proporcionas mitigaciones claras."
            ),
            "database_specialist": (
                "Eres un especialista en bases de datos PostgreSQL 15+. "
                "Optimizas esquemas y queries. "
                "Usas EXPLAIN ANALYZE, índices, RLS. "
                "SQL optimizado con justificación."
            ),
            "refactor_engineer": (
                "Eres un ingeniero de refactoring especializado en Python 3.12+. "
                "Reduces complejidad sin cambiar comportamiento. "
                "Aplicas SOLID, patrones de refactoring. "
                "Código más limpio y mantenible."
            ),
        }
        
        return prompts.get(agent_mode, prompts["architect"])
