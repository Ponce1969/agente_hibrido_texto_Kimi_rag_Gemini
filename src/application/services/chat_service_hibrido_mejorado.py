"""
Servicio de chat HÍBRIDO MEJORADO con integración de modelos locales.

Este servicio mejora el sistema híbrido existente agregando:
- Modelos locales (LLaMA3.1:8b, Gemma2:2b) como fallback adicional
- Sistema de routing inteligente basado en tipo de pregunta
- Fallback cascade: Kimi-K2 → Gemini → Local → Error
- Métricas mejoradas con tracking de modelos locales
"""

import logging
import time
import traceback
from typing import TYPE_CHECKING

from src.adapters.agents.local_llm_client import LocalLLMFactory
from src.application.services.chat_service import ChatServiceV2
from src.application.services.embeddings_service import EmbeddingsServiceV2
from src.domain.ports import LLMPort

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ChatServiceHibridoMejorado(ChatServiceV2):
    """
    Servicio de chat HÍBRIDO MEJORADO.

    Sistema de routing inteligente:
    1. **RAG con PDFs** → Gemini 2.5 Flash (mejor para contexto largo)
    2. **Chat general** → Kimi-K2 (más rápido y actualizado)
    3. **Código Python** → Kimi-K2 (especializado en Python)
    4. **Fallback 1** → Gemini 2.5 Flash (si Kimi falla)
    5. **Fallback 2** → LLaMA3.1:8b (si todo falla)
    6. **Fallback 3** → Gemma2:2b (último recurso)
    """

    def __init__(
        self,
        llm_client: LLMPort,  # Kimi-K2 (Groq)
        repository,
        *,
        fallback_llm: LLMPort | None = None,  # Gemini
        embeddings_service: EmbeddingsServiceV2 | None = None,
        python_search=None,
        metrics_service=None,
        enable_local_fallback: bool = True,  # Nuevo: habilitar modelos locales
    ) -> None:
        """
        Inicializa el servicio híbrido mejorado.

        Args:
            llm_client: Cliente principal (Kimi-K2)
            repository: Repositorio de chat
            fallback_llm: Cliente fallback (Gemini)
            embeddings_service: Servicio de embeddings
            python_search: Servicio de búsqueda Python
            metrics_service: Servicio de métricas
            enable_local_fallback: Si habilitar modelos locales
        """
        super().__init__(
            llm_client=llm_client,
            repository=repository,
            fallback_llm=fallback_llm,
            embeddings_service=embeddings_service,
            python_search=python_search,
            metrics_service=metrics_service,
        )

        self.enable_local_fallback = enable_local_fallback
        self.local_llama = None
        self.local_gemma = None

        # Inicializar modelos locales si están habilitados
        if enable_local_fallback:
            self._init_local_models()

    def _init_local_models(self) -> None:
        """Inicializa los modelos locales de forma asíncrona."""
        try:
            # Crear clientes (se verificarán su disponibilidad al usarlos)
            self.local_llama = LocalLLMFactory.create_llama_client()
            self.local_gemma = LocalLLMFactory.create_gemma_client()
            logger.info("🏠 Modelos locales inicializados (LLaMA3.1:8b, Gemma2:2b)")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando modelos locales: {e}")
            self.enable_local_fallback = False

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
        Maneja un mensaje con sistema híbrido mejorado.

        El routing inteligente decide qué modelo usar basado en:
        - Tipo de pregunta (RAG vs chat vs código)
        - Disponibilidad de los modelos
        - Complejidad de la pregunta
        """
        start_time = time.time()

        try:
            # 1. Determinar estrategia de routing
            routing_decision = await self._decide_routing(
                user_message=user_message,
                file_id=file_id,
                agent_mode=agent_mode,
            )

            logger.info(f"🎯 Routing decision: {routing_decision}")

            # 2. Ejecutar según la estrategia
            if routing_decision["strategy"] == "rag_gemini":
                response = await self._handle_with_rag_gemini(
                    session_id=session_id,
                    user_message=user_message,
                    file_id=file_id,
                    agent_mode=agent_mode,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                model_used = "gemini-2.5-flash"

            elif routing_decision["strategy"] == "chat_kimi":
                response = await self._handle_with_kimi(
                    session_id=session_id,
                    user_message=user_message,
                    agent_mode=agent_mode,
                    use_internet=use_internet,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                model_used = "kimi-k2"

            elif routing_decision["strategy"] == "code_kimi":
                response = await self._handle_with_kimi_code(
                    session_id=session_id,
                    user_message=user_message,
                    agent_mode=agent_mode,
                    use_internet=use_internet,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                model_used = "kimi-k2-code"

            else:
                # Fallback con cascada completa
                response, model_used = await self._handle_with_fallback_cascade(
                    session_id=session_id,
                    user_message=user_message,
                    agent_mode=agent_mode,
                    file_id=file_id,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    use_internet=use_internet,
                )

            # 3. Registrar métricas mejoradas
            response_time = time.time() - start_time
            await self._record_enhanced_metrics(
                session_id=session_id,
                user_message=user_message,
                response=response,
                model_used=model_used,
                routing_decision=routing_decision,
                response_time=response_time,
                file_id=file_id,
            )

            return response

        except Exception as e:
            logger.error(f"❌ Error en handle_message híbrido: {e}")
            logger.error(traceback.format_exc())
            raise

    async def _decide_routing(
        self,
        user_message: str,
        file_id: int | None,
        agent_mode: str,
    ) -> dict:
        """
        Decide la mejor estrategia de routing.

        Returns:
            Dict con estrategia y razón
        """
        # 1. RAG con PDFs → Siempre Gemini (mejor para contexto largo)
        if file_id and self.embeddings:
            return {
                "strategy": "rag_gemini",
                "reason": "PDF context available - Gemini best for long context",
                "confidence": 0.9,
            }

        # 2. Preguntas de código Python → Kimi-K2 (especializado)
        python_keywords = [
            "python", "código", "función", "clase", "import", "def ",
            "print(", "for ", "if ", "while ", "try:", "except:",
            "lista", "diccionario", "tupla", "set", "numpy", "pandas",
            "django", "flask", "fastapi", "sqlalchemy", "pytest"
        ]

        is_python_question = any(
            keyword in user_message.lower() for keyword in python_keywords
        )

        if is_python_question and agent_mode in ["architect", "code_generator"]:
            return {
                "strategy": "code_kimi",
                "reason": "Python code question - Kimi-K2 specialized",
                "confidence": 0.8,
            }

        # 3. Chat general → Kimi-K2 (más rápido)
        return {
            "strategy": "chat_kimi",
            "reason": "General chat - Kimi-K2 fastest",
            "confidence": 0.7,
        }

    async def _handle_with_rag_gemini(
        self,
        session_id: str,
        user_message: str,
        file_id: int,
        agent_mode: str,
        max_tokens: int | None,
        temperature: float | None,
    ) -> str:
        """Maneja preguntas RAG con Gemini."""
        logger.info(f"🤖 Using Gemini for RAG with file_id={file_id}")

        # Usar la lógica RAG existente del padre
        return await super().handle_message(
            session_id=session_id,
            user_message=user_message,
            agent_mode=agent_mode,
            file_id=file_id,
            max_tokens=max_tokens or 2048,  # Más tokens para RAG
            temperature=temperature or 0.3,
            use_fallback_on_error=True,  # Permitir fallback
            use_internet=False,  # RAG no necesita internet
        )

    async def _handle_with_kimi(
        self,
        session_id: str,
        user_message: str,
        agent_mode: str,
        use_internet: bool,
        max_tokens: int | None,
        temperature: float | None,
    ) -> str:
        """Maneja chat general con Kimi-K2."""
        logger.info("🤖 Using Kimi-K2 for general chat")

        return await super().handle_message(
            session_id=session_id,
            user_message=user_message,
            agent_mode=agent_mode,
            file_id=None,  # Sin RAG
            max_tokens=max_tokens,
            temperature=temperature,
            use_fallback_on_error=True,  # Permitir fallback
            use_internet=use_internet,
        )

    async def _handle_with_kimi_code(
        self,
        session_id: str,
        user_message: str,
        agent_mode: str,
        use_internet: bool,
        max_tokens: int | None,
        temperature: float | None,
    ) -> str:
        """Maneja preguntas de código con Kimi-K2 especializado."""
        logger.info("🤖 Using Kimi-K2 for Python code")

        # Forzar modo de arquitecto Python para código
        code_mode = "architect" if agent_mode == "architect" else agent_mode

        return await super().handle_message(
            session_id=session_id,
            user_message=user_message,
            agent_mode=code_mode,
            file_id=None,  # Sin RAG
            max_tokens=max_tokens,
            temperature=temperature or 0.2,  # Menos temperatura para código
            use_fallback_on_error=True,  # Permitir fallback
            use_internet=use_internet,
        )

    async def _handle_with_fallback_cascade(
        self,
        session_id: str,
        user_message: str,
        agent_mode: str,
        file_id: int | None,
        max_tokens: int | None,
        temperature: float | None,
        use_internet: bool,
    ) -> tuple[str, str]:
        """
        Ejecuta cascada completa de fallback.

        Returns:
            Tuple of (response, model_used)
        """
        logger.info("🔄 Executing fallback cascade...")

        # Strategy 1: Kimi-K2 (principal)
        try:
            response = await super().handle_message(
                session_id=session_id,
                user_message=user_message,
                agent_mode=agent_mode,
                file_id=file_id,
                max_tokens=max_tokens,
                temperature=temperature,
                use_fallback_on_error=False,  # No fallback recursivo
                use_internet=use_internet,
            )
            return response, "kimi-k2-fallback"
        except Exception as e:
            logger.warning(f"⚠️ Kimi-K2 failed in cascade: {e}")

        # Strategy 2: Gemini (fallback en la nube)
        if self.fallback_llm:
            try:
                logger.info("🤖 Trying Gemini as cloud fallback...")
                response, _ = await self.fallback_llm.get_chat_completion(
                    system_prompt=self._get_system_prompt(agent_mode),
                    messages=[{"role": "user", "content": user_message}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response, "gemini-2.5-flash-fallback"
            except Exception as e:
                logger.warning(f"⚠️ Gemini failed in cascade: {e}")

        # Strategy 3: LLaMA3.1:8b (local fallback)
        if self.enable_local_fallback and self.local_llama:
            try:
                logger.info("🏠 Trying LLaMA3.1:8b as local fallback...")
                if await self.local_llama.health_check():
                    response, _ = await self.local_llama.get_chat_completion(
                        system_prompt=self._get_system_prompt(agent_mode),
                        messages=[{"role": "user", "content": user_message}],
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return response, "llama3.1-8b-local"
            except Exception as e:
                logger.warning(f"⚠️ LLaMA3.1:8b failed in cascade: {e}")

        # Strategy 4: Gemma2:2b (último recurso local)
        if self.enable_local_fallback and self.local_gemma:
            try:
                logger.info("🏠 Trying Gemma2:2b as last resort...")
                if await self.local_gemma.health_check():
                    response, _ = await self.local_gemma.get_chat_completion(
                        system_prompt=self._get_system_prompt(agent_mode),
                        messages=[{"role": "user", "content": user_message}],
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return response, "gemma2-2b-local"
            except Exception as e:
                logger.warning(f"⚠️ Gemma2:2b failed in cascade: {e}")

        # Strategy 5: Error final
        error_msg = (
            "❌ Todos los modelos fallaron. Por favor:\n"
            "1. Verifica tu conexión a internet\n"
            "2. Revisa que Ollama esté corriendo (docker-compose up -d)\n"
            "3. Verifica las API keys en .env\n"
            "4. Intenta con una pregunta más simple"
        )
        logger.error("💥 Complete cascade failure")
        return error_msg, "error-all-models-failed"

    async def _record_enhanced_metrics(
        self,
        session_id: str,
        user_message: str,
        response: str,
        model_used: str,
        routing_decision: dict,
        response_time: float,
        file_id: int | None,
    ) -> None:
        """
        Registra métricas mejoradas con tracking del sistema híbrido.
        """
        try:
            # Estimar tokens
            prompt_tokens = len(user_message) // 4
            completion_tokens = len(response) // 4

            # Usar el servicio de métricas del padre
            self.metrics.record_agent_usage(
                session_id=session_id,
                agent_mode=routing_decision.get("strategy", "unknown"),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time=response_time,
                model_name=model_used,
                has_rag_context=bool(file_id),
                rag_chunks_used=1 if file_id else 0,
                file_id=str(file_id) if file_id else None,
                used_bear_search=False,  # Se registra en el padre si se usa
                bear_sources_count=0,
            )

            # Log mejorado
            logger.info(
                f"📊 Enhanced metrics: {model_used} | "
                f"Strategy: {routing_decision.get('strategy')} | "
                f"Confidence: {routing_decision.get('confidence', 0):.2f} | "
                f"Time: {response_time:.2f}s | "
                f"Tokens: {prompt_tokens + completion_tokens}"
            )

        except Exception as e:
            logger.error(f"❌ Error recording enhanced metrics: {e}")

    async def get_system_status(self) -> dict:
        """
        Retorna el estado de todos los modelos disponibles.

        Útil para dashboard y diagnóstico.
        """
        status = {
            "kimi_k2": {"available": True, "type": "cloud"},
            "gemini": {"available": bool(self.fallback_llm), "type": "cloud"},
            "llama3_1_8b": {"available": False, "type": "local"},
            "gemma2_2b": {"available": False, "type": "local"},
            "routing_enabled": self.enable_local_fallback,
        }

        # Verificar modelos locales
        if self.enable_local_fallback:
            if self.local_llama:
                status["llama3_1_8b"]["available"] = await self.local_llama.health_check()
            if self.local_gemma:
                status["gemma2_2b"]["available"] = await self.local_gemma.health_check()

        return status

    async def close(self) -> None:
        """Cierra todos los clientes."""
        await super().close() if hasattr(super(), 'close') else None

        if self.local_llama:
            await self.local_llama.close()
        if self.local_gemma:
            await self.local_gemma.close()
