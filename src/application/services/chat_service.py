"""
Servicio de aplicación de chat refactorizado con arquitectura hexagonal.

Este servicio usa SOLO puertos (interfaces) del dominio, sin dependencias
de implementaciones concretas (adapters).

Tipado estricto para mypy --strict con Python 3.12+
"""

from __future__ import annotations

import logging
import re
import time
import traceback
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.application.services.metrics_service import MetricsService
from src.application.services.rag_context_service import RagContextService
from src.domain.models import ChatMessageCreate, ChatSessionCreate, MessageRole

if TYPE_CHECKING:
    from src.application.services.embeddings_service_v2 import EmbeddingsServiceV2
    from src.domain.models import ChatMessage, ChatSession
    from src.domain.ports import ChatRepositoryPort, FileRepositoryPort, LLMPort
    from src.domain.ports.python_search_port import PythonSearchPort, PythonSource


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
        metrics_service: MetricsService | None = None,
        file_repository: FileRepositoryPort | None = None,
        document_mapper: Any | None = None,
    ) -> None:
        """
        Inicializa el servicio de chat.

        Args:
            llm_client: Cliente LLM principal (ej: Groq)
            repository: Repositorio de chat
            fallback_llm: Cliente LLM de respaldo (ej: Gemini)
            embeddings_service: Servicio de embeddings para RAG (opcional)
            python_search: Servicio de búsqueda Python (opcional)
            metrics_service: Servicio de métricas (opcional)
            file_repository: Repositorio de archivos (opcional, para RAG context)
            document_mapper: Mapper de documentos (opcional, inyectado desde afuera)
        """
        self.llm = llm_client
        self.repo = repository
        self.fallback_llm = fallback_llm
        self.embeddings = embeddings_service
        self.python_search = python_search

        self.context_service = None
        self.document_mapper = document_mapper or None
        if file_repository:
            self.context_service = RagContextService(file_repository)
            if not self.document_mapper:
                from src.adapters.db.document_mapper import DocumentMapper

                self.document_mapper = DocumentMapper(file_repository)

        self.metrics = metrics_service or MetricsService()

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
            title=f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
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
            message_count = self.repo.count_session_messages(str(s.id))
            detailed_sessions.append(
                {
                    "id": int(s.id),
                    "user_id": s.user_id,
                    "session_name": s.title if hasattr(s, "title") else None,
                    "message_count": message_count,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
            )
        return detailed_sessions

    def _resolve_target_file_id(
        self, session_id: str, user_message: str, provided_file_id: int | None
    ) -> int | None:
        """
        Resuelve qué archivo usar como contexto para RAG.

        Prioridad:
        1. ID explícito en el mensaje (ej: "ID:5")
        2. ID proporcionado por la UI (sidebar select)
        3. Referencia contextual (ej: "este documento") apuntando al último usado
        """
        # 1. Buscar mención explícita "ID:X" en el mensaje
        if self.document_mapper:
            explicit_id = self.document_mapper.parse_document_reference_from_text(
                user_message
            )
            if explicit_id:
                logger.info(
                    f"📄 Detectada referencia explícita a archivo ID:{explicit_id}"
                )
                return explicit_id

        # 2. Usar ID proporcionado por UI (si existe)
        if provided_file_id:
            return provided_file_id

        # 3. Verificar referencia contextual ("este pdf")
        if (
            self.context_service
            and self.context_service.is_referencing_current_document(user_message)
        ):
            context_id = self.context_service.get_current_file_id(session_id)
            if context_id:
                logger.info(
                    f"📄 Detectada referencia contextual a archivo ID:{context_id}"
                )
                return context_id

        return None

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
            use_internet: Si usar búsqueda en Internet

        Returns:
            Respuesta del LLM

        Raises:
            ValueError: Si la sesión no existe
        """
        # Iniciar timer para métricas
        start_time = time.time()

        # --- RESOLUCIÓN DE CONTEXTO RAG ---
        # Determinar el file_id real a usar
        resolved_file_id = self._resolve_target_file_id(
            session_id, user_message, file_id
        )

        # Si se resolvió un archivo, actualizar el contexto de la sesión
        if resolved_file_id:
            if self.context_service:
                self.context_service.set_current_file_id(session_id, resolved_file_id)
            # Usar el ID resuelto en lugar del proporcionado
            file_id = resolved_file_id
        # ----------------------------------

        rag_chunks_count = 0
        used_bear = False
        bear_sources_count = 0
        model_used = "kimi-k2"  # Default
        # 1. Validar o crear sesión
        if session_id == "0" or not session_id:
            # Crear nueva sesión si no existe
            session_data = ChatSessionCreate(
                user_id="streamlit_user",
                title=f"Chat {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}",
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
                # 🎯 BÚSQUEDA ADAPTATIVA: Ajustar top_k según complejidad de la pregunta
                # Preguntas complejas necesitan más contexto para aprovechar ventana de Gemini
                from src.adapters.config.settings import settings

                question_length = len(user_message)
                is_complex = any(
                    word in user_message.lower()
                    for word in [
                        # Análisis y comparación
                        "compara",
                        "diferencia",
                        "diferencias",
                        "relación",
                        "relaciona",
                        "contrasta",
                        "versus",
                        "vs",
                        "frente a",
                        "comparación",
                        # Explicación profunda
                        "explica detalladamente",
                        "explica en detalle",
                        "profundiza",
                        "desarrolla",
                        "elabora",
                        "detalla",
                        "describe en profundidad",
                        "extiende",
                        "amplía",
                        "expande",
                        # Análisis técnico
                        "analiza",
                        "evalúa",
                        "examina",
                        "investiga",
                        "estudia",
                        "revisa",
                        "inspecciona",
                        "diagnostica",
                        # Enumeración y listado
                        "enumera",
                        "lista",
                        "identifica",
                        "menciona todos",
                        "cuáles son",
                        "qué tipos",
                        "qué clases",
                        # Síntesis y conexión
                        "sintetiza",
                        "resume extensamente",
                        "conecta",
                        "vincula",
                        "integra",
                        "unifica",
                        "combina",
                        # Ejemplos y casos
                        "ejemplos",
                        "ejemplo práctico",
                        "casos de uso",
                        "casos prácticos",
                        "demuestra",
                        "ilustra",
                        "muestra cómo",
                        # Procedimientos y pasos
                        "paso a paso",
                        "procedimiento",
                        "proceso completo",
                        "cómo hacer",
                        "implementar",
                        "aplicar en la práctica",
                        # Conceptos avanzados
                        "ventajas y desventajas",
                        "pros y contras",
                        "beneficios y limitaciones",
                        "implicaciones",
                        "consecuencias",
                        "impacto",
                        # Contexto técnico (SQL, programación)
                        "optimización",
                        "rendimiento",
                        "mejor práctica",
                        "mejores prácticas",
                        "arquitectura",
                        "diseño",
                        "patrones",
                        "estrategias",
                    ]
                )

                # Ajustar top_k dinámicamente usando configuración
                if is_complex or question_length > 100:
                    top_k = settings.rag_complex_top_k  # Preguntas complejas
                    limit = settings.rag_complex_limit
                    complexity = "compleja"
                elif question_length > 50:
                    top_k = settings.rag_normal_top_k  # Preguntas normales
                    limit = settings.rag_normal_limit
                    complexity = "normal"
                else:
                    top_k = settings.rag_simple_top_k  # Preguntas simples
                    limit = settings.rag_simple_limit
                    complexity = "simple"

                logger.info(
                    f"🎯 Búsqueda adaptativa ({complexity}): top_k={top_k}, limit={limit} chars"
                )

                # Buscar chunks relevantes
                # Búsqueda más precisa para definiciones técnicas
                results = await self.embeddings.search_similar(
                    query=user_message,
                    file_id=str(file_id),
                    top_k=8,  # Más chunks para mejor contexto
                    min_similarity=0.65,  # Umbral más estricto
                )

                if results:
                    logger.info(
                        f"✅ RAG: {len(results)} chunks encontrados para file_id={file_id}"
                    )
                    acc = 0
                    parts: list[str] = []

                    for r in results:
                        remaining = limit - acc
                        if remaining <= 100:  # Mínimo para que valga la pena
                            break

                        # EmbeddingsServiceV2 retorna 'text', no 'content'
                        content = r.get("text", "")
                        chunk_idx = r.get("chunk_index", 0)
                        similarity = r.get("similarity", 0.0)

                        if not content:
                            logger.warning(
                                f"⚠️ Chunk {chunk_idx} sin contenido: {r.keys()}"
                            )
                            continue

                        snippet = content[:remaining]
                        parts.append(
                            f"[chunk {chunk_idx}, score={similarity:.3f}]\n{snippet}"
                        )
                        acc += len(snippet)

                    rag_context = "\n\n".join(parts)
                    rag_chunks_count = len(parts)  # Guardar para métricas
                    model_used = "gemini-2.5-flash"  # RAG usa Gemini
                    logger.info(
                        f"📄 Contexto RAG: {acc} caracteres de {rag_chunks_count} chunks"
                    )
                    logger.debug(f"🔍 Preview contexto: {rag_context[:300]}...")
                else:
                    logger.warning(
                        f"⚠️ RAG: No se encontraron chunks para file_id={file_id}"
                    )
            except Exception as e:
                logger.error(f"❌ Error en búsqueda RAG: {e}")
                logger.error(traceback.format_exc())

        # 5. Construir system prompt
        system_prompt = self._get_system_prompt(agent_mode)

        # Si hay contexto RAG, PRIORIZAR el contexto del PDF
        if rag_context:
            # Prompt MEJORADO para respuestas técnicas en español
            system_prompt = (
                f"Eres un asistente experto en análisis técnico de documentos. El usuario ha cargado un documento PDF.\n\n"
                "**INSTRUCCIONES OBLIGATORIAS:**\n"
                "1. SIEMPRE responde en español\n"
                "2. NO menciones 'Chunk', 'fragmento', 'sección' ni números de referencia interna\n"
                "3. Responde de forma técnica y concisa\n"
                "4. Estructura con bullets y secciones claras\n"
                "5. Si el usuario pide 'puntos importantes', lista solo los conceptos clave\n"
                "6. Permite que el usuario pida más detalles sobre puntos específicos\n"
                "7. NUNCA inventes información que no esté en el documento\n\n"
                f"--- CONTENIDO DEL DOCUMENTO ---\n\n"
                f"{rag_context}\n\n"
                "--- FIN DEL DOCUMENTO ---\n\n"
                "Responde basándote únicamente en este contenido."
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
        used_bear = False  # Inicializar variables antes del bloque condicional
        bear_sources_count = 0
        if use_internet and self.python_search and not rag_context:
            logger.info("🔍 Verificando si necesita búsqueda web...")
            if self._should_search_internet(user_message, initial_response):
                logger.info("✅ Kimi solicitó búsqueda web. Activando Brave Search...")
                sources = await self._search_python_sources(user_message)
                if sources:
                    used_bear = True  # Marcar uso de Bear API
                    bear_sources_count = len(sources)  # Contar fuentes
                    self.last_search_sources = sources
                    context = self._build_internet_context(sources)

                    logger.info(
                        f"📚 Contexto web construido: {len(context)} caracteres de {len(sources)} fuentes"
                    )

                    # Re-llamar al LLM con contexto adicional
                    # IMPORTANTE: Incluir el contexto DENTRO del system prompt para que Kimi lo vea como conocimiento base
                    enriched_prompt = (
                        f"{system_prompt}\n\n"
                        f"--- INFORMACIÓN ACTUALIZADA DE INTERNET ---\n"
                        f"{context}\n"
                        f"--- FIN DE INFORMACIÓN ACTUALIZADA ---\n\n"
                        f"INSTRUCCIÓN CRÍTICA: Acabas de recibir información actualizada de fuentes confiables. "
                        f"Usa ESTA información para responder la pregunta del usuario. "
                        f"NO digas que no tienes información. "
                        f"Proporciona una respuesta completa basándote en el contexto actualizado que acabas de recibir."
                    )

                    logger.info("🤖 Re-llamando a Kimi con contexto web...")

                    # Usar el historial completo (el LLM verá el contexto actualizado en el system prompt)
                    response, tokens = await self._get_llm_response(
                        system_prompt=enriched_prompt,
                        history=history,  # Usar historial completo
                        max_tokens=max_tokens,
                        temperature=temperature,
                        session_id=session_id,
                        agent_mode=agent_mode,
                        use_fallback_on_error=use_fallback_on_error,
                        has_rag=bool(rag_context),
                    )
                    logger.info(
                        f"✅ Respuesta con contexto web generada: {len(response)} caracteres"
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

        # 9. Registrar métricas
        response_time = time.time() - start_time
        try:
            # Extraer tokens de la respuesta (manejar diferentes formatos)
            prompt_tokens = 0
            completion_tokens = 0

            if isinstance(tokens, dict):
                # Formato diccionario (algunos LLMs)
                prompt_tokens = tokens.get("prompt_tokens", 0)
                completion_tokens = tokens.get("completion_tokens", 0)
            elif isinstance(tokens, int):
                # Formato entero (Groq retorna total)
                # Estimar: ~70% completion, 30% prompt
                completion_tokens = int(tokens * 0.7)
                prompt_tokens = tokens - completion_tokens
            elif tokens is None:
                # Gemini no retorna tokens, estimar basado en longitud
                prompt_tokens = len(user_message) // 4  # ~4 chars por token
                completion_tokens = len(response) // 4
                logger.debug(
                    f"⚠️ Tokens estimados (LLM no los proporciona): {prompt_tokens + completion_tokens}"
                )
            else:
                # Caso inesperado, estimar
                prompt_tokens = len(user_message) // 4
                completion_tokens = len(response) // 4
                logger.warning(f"⚠️ Tipo de tokens inesperado: {type(tokens)}")

            self.metrics.record_agent_usage(
                session_id=session_id,
                agent_mode=agent_mode,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time=response_time,
                model_name=model_used,
                has_rag_context=bool(rag_context),
                rag_chunks_used=rag_chunks_count,
                file_id=str(file_id) if file_id else None,
                used_bear_search=used_bear,
                bear_sources_count=bear_sources_count,
            )
            logger.info(
                f"📊 Métricas registradas: {prompt_tokens + completion_tokens} tokens, {response_time:.2f}s, modelo={model_used}"
            )
        except Exception as e:
            logger.error(f"❌ Error registrando métricas: {e}")
            logger.error(traceback.format_exc())

        return response

    def _get_system_prompt(self, agent_mode: str) -> str:
        """
        Obtiene el system prompt para un modo de agente.

        Args:
            agent_mode: Modo del agente (puede ser el valor del enum o el nombre)

        Returns:
            System prompt
        """
        # Importar get_system_prompt de prompts.py
        from src.adapters.agents.prompts import AgentMode, get_system_prompt

        # Instrucción común sobre limitaciones de conocimiento (específica para Kimi-K2)
        knowledge_cutoff = (
            "\n\n**REGLAS DE CONOCIMIENTO Y BÚSQUEDA WEB (Kimi-K2):**\n"
            "Tu conocimiento base cubre hasta Python 3.13 (inclusive) y enero 2025.\n\n"
            "**PARA PREGUNTAS TÉCNICAS DE PYTHON:**\n"
            "- Responde normalmente con tu conocimiento experto de Python\n"
            "- Mantén la calidad técnica y precisión en arquitectura, código y mejores prácticas\n"
            "- Usa tu experiencia como arquitecto/software engineer senior\n\n"
            "**CUANDO NECESITES BÚSQUEDA WEB:**\n"
            "Si la pregunta requiere información más actual o menciona explícitamente:\n"
            "- Python 3.14, 3.15, 'dev', 'main branch', 'nightly'\n"
            "- Librerías sin soporte estable o releases muy recientes\n"
            "- Eventos/noticias/releases posteriores a enero 2025\n"
            "- Preguntas sobre clima, noticias, información en tiempo real\n\n"
            'ENTONCES responde: "Voy a buscar información actualizada sobre esto."\n\n'
            "**IMPORTANTE:** Prioriza siempre respuestas técnicas de alta calidad. "
            "Usa búsqueda web solo cuando sea estrictamente necesario para información actualizada."
        )

        try:
            # Intentar obtener el prompt del módulo prompts.py
            # get_system_prompt acepta tanto enum como string
            base_prompt = get_system_prompt(agent_mode)
            # Agregar las reglas de conocimiento
            return base_prompt + knowledge_cutoff
        except (KeyError, ValueError) as e:
            # Fallback: usar prompt por defecto del arquitecto
            logger.warning(
                f"⚠️ No se encontró prompt para modo '{agent_mode}', usando Arquitecto por defecto. Error: {e}"
            )
            base_prompt = get_system_prompt(AgentMode.PYTHON_ARCHITECT)
            return base_prompt + knowledge_cutoff

    def _should_search_internet(self, user_message: str, kimi_response: str) -> bool:
        """Detecta si Kimi no pudo resolver el problema y necesita búsqueda."""
        if "voy a buscar información actualizada sobre esto" in kimi_response.lower():
            return True

        if "voy a buscarlo en internet" in kimi_response.lower():
            return True

        uncertainty_signals = [
            r"\bno tengo información suficiente\b",
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
            r"\bcomo modelo de lenguaje\b",
            r"\bno tengo la capacidad\b",
            r"\bno puedo navegar\b",
            r"\bno puedo acceder\b",
        ]

        kimis_uncertain = any(
            re.search(pattern, kimi_response, re.IGNORECASE)
            for pattern in uncertainty_signals
        )

        traceback_mentioned = bool(
            re.search(r"Traceback|Error|Exception", user_message, re.IGNORECASE)
        )

        is_general_query = bool(
            re.search(
                r"\b(clima|temperatura|hora|dólar|euro|noticias|recetas)\b",
                user_message,
                re.IGNORECASE,
            )
        )

        return (kimis_uncertain or traceback_mentioned) and not is_general_query

    async def _search_python_sources(self, user_message: str) -> list[PythonSource]:
        """Ejecuta búsqueda Bear para cualquier pregunta Python válida."""
        if not self.python_search:
            return []

        # Determinar tipo de búsqueda basado en el contenido

        if "Traceback" in user_message:
            return await self.python_search.search_python_bug(user_message)
        elif re.search(
            r"\b(cómo usar|ejemplo|funciona)\b.*\w+\.\w+", user_message, re.IGNORECASE
        ):
            api_match = re.search(r"(\w+)\.(\w+)", user_message)
            if api_match:
                module, attr = api_match.groups()
                return await self.python_search.search_python_api(module, attr)
        elif re.search(
            r"\b(nueva versión|última versión|actualización|lanzamiento|release)\b.*\bpython\b",
            user_message,
            re.IGNORECASE,
        ):
            return await self.python_search.search_python_best_practice(
                "latest python version release"
            )

        # Default: búsqueda general para cualquier pregunta Python válida
        return await self.python_search.search_python_best_practice(user_message)

    def _build_internet_context(self, sources: list[PythonSource]) -> str:
        """Construye el contexto para el LLM con las fuentes encontradas."""
        lines = []
        for source in sources:
            lines.append(
                f"📚 **{source.title}** ({source.source_type}, confiabilidad: {source.reliability}/10)"
            )
            lines.append(f"🔗 {source.url}")
            lines.append(f"💡 {source.snippet}")
            lines.append("")
        return "\n".join(lines)

    async def _get_llm_response(
        self,
        system_prompt: str,
        history: list,  # list[ChatMessage] pero evitamos import circular
        max_tokens: int | None,
        temperature: float | None,
        session_id: str,
        agent_mode: str,
        use_fallback_on_error: bool,
        has_rag: bool,
    ) -> tuple[str, int | None]:
        """Helper para obtener respuesta del LLM con lógica de fallback."""
        # IMPORTANTE: Sistema híbrido
        # - RAG (con file_id) → Gemini 2.5 (fallback_llm)
        # - Chat normal → Kimi-K2 (llm)

        if has_rag and self.fallback_llm:
            # RAG: Usar provider de fallback (configurable, default: Gemini)
            logger.info("🤖 Usando LLM de fallback para RAG")

            try:
                response, tokens = await self.fallback_llm.get_chat_completion(
                    system_prompt=system_prompt,
                    messages=history,
                    max_tokens=max_tokens
                    or 8192,  # Aumentado para respuestas completas
                    temperature=temperature or 0.3,
                )
                return response, tokens
            except Exception as e:
                logger.error(f"❌ Error en Gemini: {e}")
                raise
        else:
            # Chat normal: Usar provider principal (configurable, default: Groq/Kimi)
            logger.info("🤖 Usando LLM principal para chat")

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
                    logger.warning(
                        f"⚠️ Kimi-K2 falló, usando Gemini como fallback. Error: {e}"
                    )
                    response, tokens = await self.fallback_llm.get_chat_completion(
                        system_prompt=system_prompt,
                        messages=history,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return response, tokens
                else:
                    raise
