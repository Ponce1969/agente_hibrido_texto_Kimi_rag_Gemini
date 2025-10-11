"""
Servicio de aplicación de chat refactorizado con arquitectura hexagonal.

Este servicio usa SOLO puertos (interfaces) del dominio, sin dependencias
de implementaciones concretas (adapters).

Tipado estricto para mypy --strict con Python 3.12+
"""

from __future__ import annotations

import logging
import re
import traceback
from datetime import datetime, UTC
from typing import TYPE_CHECKING

from src.domain.models import ChatMessageCreate, ChatSessionCreate, MessageRole

if TYPE_CHECKING:
    from src.domain.models import ChatMessage, ChatSession
    from src.domain.ports import ChatRepositoryPort, EmbeddingsPort, LLMPort
    from src.domain.ports.python_search_port import PythonSearchPort, PythonSource
    from src.application.services.embeddings_service_v2 import EmbeddingsServiceV2


logger = logging.getLogger(__name__)


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
        python_search: PythonSearchPort | None = None,
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
        self.python_search = python_search
        
        # Almacenar últimas fuentes usadas para feedback
        self.last_search_sources: list[PythonSource] = []
    
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

    def create_session_from_user(self, user_id: str) -> ChatSession:
        """Crea una nueva sesión para un usuario con un título por defecto."""
        session_data = ChatSessionCreate(
            user_id=user_id,
            title=f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
        )
        return self.create_session(session_data)

    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión de chat."""
        return self.repo.delete_session(session_id)

    def get_session_messages(self, session_id: str) -> list[ChatMessage]:
        """Obtiene todos los mensajes de una sesión."""
        return self.repo.get_session_messages(session_id)

    def list_sessions_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        """Lista las sesiones de un usuario con el conteo de mensajes."""
        all_sessions = self.repo.list_sessions(limit=limit * 2)
        user_sessions = [s for s in all_sessions if s.user_id == user_id]
        
        detailed_sessions = []
        for s in user_sessions[:limit]:
            message_count = self.repo.count_session_messages(s.id)
            detailed_sessions.append(
                {
                    "id": int(s.id),
                    "user_id": s.user_id,
                    "session_name": s.title if hasattr(s, 'title') else None,
                    "message_count": message_count,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
            )
        return detailed_sessions

    
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
        use_internet: bool = True,
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
                    logger.info(f"✅ RAG: {len(results)} chunks encontrados para file_id={file_id}")
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
                            logger.warning(f"⚠️ Chunk {chunk_idx} sin contenido: {r.keys()}")
                            continue
                        
                        snippet = content[:remaining]
                        parts.append(f"[chunk {chunk_idx}, score={similarity:.3f}]\n{snippet}")
                        acc += len(snippet)
                    
                    rag_context = "\n\n".join(parts)
                    logger.info(f"📄 Contexto RAG: {acc} caracteres de {len(parts)} chunks")
                    logger.debug(f"🔍 Preview contexto: {rag_context[:300]}...")
                else:
                    logger.warning(f"⚠️ RAG: No se encontraron chunks para file_id={file_id}")
            except Exception as e:
                logger.error(f"❌ Error en búsqueda RAG: {e}")
                logger.error(traceback.format_exc())
        
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
            logger.debug(f"🎯 System prompt RAG: {len(system_prompt)} caracteres")
        
        # 6. Obtener respuesta inicial del LLM
        initial_response, tokens = await self._get_llm_response(
            system_prompt=system_prompt,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
            session_id=session_id,
            agent_mode=agent_mode,
            use_fallback_on_error=use_fallback_on_error,
            has_rag=bool(rag_context),
        )
        
        # 7. Verificar si necesita búsqueda en Internet
        if use_internet and self.python_search and not rag_context:
            if self._should_search_internet(user_message, initial_response):
                sources = await self._search_python_sources(user_message)
                if sources:
                    self.last_search_sources = sources
                    context = self._build_internet_context(sources)
                    
                    # Re-llamar al LLM con contexto adicional
                    enriched_prompt = (
                        f"{system_prompt}\n\n"
                        f"🔍 Información adicional de fuentes Python confiables:\n"
                        f"{context}\n\n"
                        f"Usa esta información para proporcionar una respuesta más precisa y actualizada."
                    )
                    
                    response, tokens = await self._get_llm_response(
                        system_prompt=enriched_prompt,
                        history=history,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        session_id=session_id,
                        agent_mode=agent_mode,
                        use_fallback_on_error=use_fallback_on_error,
                        has_rag=bool(rag_context),
                    )
                else:
                    response = initial_response
            else:
                response = initial_response
        else:
            response = initial_response
        
        # 8. Guardar respuesta del asistente
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
    
    def _should_search_internet(self, user_message: str, kimi_response: str) -> bool:
        """Detecta si Kimi no pudo resolver el problema y necesita búsqueda."""
        # Señales AMPLIADAS de que Kimi no tiene la información
        uncertainty_signals = [
            r"\bno (tengo|cuento con|puedo proporcionar)\b",
            r"\b(desconozco|ignoro|no estoy seguro)\b",
            r"\bno puedo\b",
            r"\bno tengo\b",
            r"\bno dispongo\b",
            r"\bpodrías consultar\b",
            r"\bpodrías buscar\b",
            r"\berror.*desconocido\b",
            r"\bno encuentro\b",
            r"\bno tengo acceso\b",
            r"\bno puedo ver\b",
            r"\bno disponible\b",
            r"\bcomo modelo de lenguaje\b",  # ¡CLAVE! Detecta cuando dice "como modelo"
            r"\bno tengo la capacidad\b",
            r"\bno puedo navegar\b",
            r"\bno puedo acceder\b",
        ]
        
        kimis_uncertain = any(
            re.search(pattern, kimi_response, re.IGNORECASE) 
            for pattern in uncertainty_signals
        )

        # Si el usuario menciona GitHub, búsqueda o internet
        search_mentioned = bool(
            re.search(r"\b(github|buscar|internet|repo|repositorio)\b", user_message, re.IGNORECASE)
        )

        # Si el usuario menciona un traceback o error específico
        traceback_mentioned = bool(
            re.search(r"Traceback|Error|Exception", user_message, re.IGNORECASE)
        )
        
        # Si menciona arquitectura hexagonal o patrones específicos
        architecture_mentioned = bool(
            re.search(r"\b(arquitectura hexagonal|clean architecture|ports and adapters)\b", user_message, re.IGNORECASE)
        )
        
        # Si pregunta por una API específica
        api_question = bool(
            re.search(r"\b(cómo usar|cómo funciona|ejemplo de|ejemplos de)\b.*\w+", user_message, re.IGNORECASE)
        )

        # Activar siempre que NO sea una consulta general rechazada
        is_general_query = bool(
            re.search(r"\b(clima|temperatura|hora|dólar|euro|noticias|recetas)\b", user_message, re.IGNORECASE)
        )
        
        # Activar para preguntas sobre versiones, novedades y actualizaciones
        version_question = bool(
            re.search(r"\b(nueva versión|última versión|actualización|lanzamiento|release)\b.*\bpython\b", user_message, re.IGNORECASE)
        )

        return (kimis_uncertain or search_mentioned or traceback_mentioned or 
                architecture_mentioned or api_question or version_question) and not is_general_query

    async def _search_python_sources(self, user_message: str) -> list[PythonSource]:
        """Ejecuta búsqueda Bear para cualquier pregunta Python válida."""
        if not self.python_search:
            return []
            
        # Determinar tipo de búsqueda basado en el contenido
        search_type = "general"
        
        if "Traceback" in user_message:
            search_type = "bug"
            return await self.python_search.search_python_bug(user_message)
        elif re.search(r"\b(cómo usar|ejemplo|funciona)\b.*\w+\.\w+", user_message, re.IGNORECASE):
            api_match = re.search(r"(\w+)\.(\w+)", user_message)
            if api_match:
                module, attr = api_match.groups()
                return await self.python_search.search_python_api(module, attr)
        elif re.search(r"\b(nueva versión|última versión|actualización|lanzamiento|release)\b.*\bpython\b", user_message, re.IGNORECASE):
            search_type = "version"
            return await self.python_search.search_python_best_practice("latest python version release")
        
        # Default: búsqueda general para cualquier pregunta Python válida
        return await self.python_search.search_python_best_practice(user_message)

    def _build_internet_context(self, sources: list[PythonSource]) -> str:
        """Construye el contexto para el LLM con las fuentes encontradas."""
        lines = []
        for source in sources:
            lines.append(f"📚 **{source.title}** ({source.source_type}, confiabilidad: {source.reliability}/10)")
            lines.append(f"🔗 {source.url}")
            lines.append(f"💡 {source.snippet}")
            lines.append("")
        return "\n".join(lines)

    async def _get_llm_response(
        self,
        system_prompt: str,
        history: list[dict],
        max_tokens: int | None,
        temperature: float | None,
        session_id: str,
        agent_mode: str,
        use_fallback_on_error: bool,
        has_rag: bool,
    ) -> tuple[str, int]:
        """Helper para obtener respuesta del LLM con lógica de fallback."""
        # IMPORTANTE: Sistema híbrido
        # - RAG (con file_id) → Gemini 2.5 (fallback_llm)
        # - Chat normal → Kimi-K2 (llm)
        
        if has_rag and self.fallback_llm:
            # RAG: Usar Gemini (mejor para contextos largos)
            logger.info(f"🤖 Usando Gemini 2.5 para RAG")
            
            try:
                response, tokens = await self.fallback_llm.get_chat_completion(
                    system_prompt=system_prompt,
                    messages=history,
                    max_tokens=max_tokens or 2048,  # Más tokens para RAG
                    temperature=temperature or 0.3,
                )
                return response, tokens
            except Exception as e:
                logger.error(f"❌ Error en Gemini: {e}")
                raise
        else:
            # Chat normal: Usar Kimi-K2 (más rápido)
            logger.info(f"🤖 Usando Kimi-K2 para chat normal")
            
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
                return response, tokens
            except Exception as e:
                # Fallback a Gemini si Kimi falla
                if use_fallback_on_error and self.fallback_llm:
                    logger.warning(f"⚠️ Kimi-K2 falló, usando Gemini como fallback. Error: {e}")
                    response, tokens = await self.fallback_llm.get_chat_completion(
                        system_prompt=system_prompt,
                        messages=history,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return response, tokens
                else:
                    raise
