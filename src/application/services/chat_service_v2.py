"""
Servicio de aplicación de chat refactorizado con arquitectura hexagonal.

Este servicio usa SOLO puertos (interfaces) del dominio, sin dependencias
de implementaciones concretas (adapters).

Tipado estricto para mypy --strict con Python 3.12+
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.ports import LLMPort, ChatRepositoryPort
    from src.domain.models import ChatSession, ChatMessage, ChatSessionCreate, ChatMessageCreate


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
    ) -> None:
        """
        Inicializa el servicio de chat.
        
        Args:
            llm_client: Cliente LLM principal (ej: Groq)
            repository: Repositorio de chat
            fallback_llm: Cliente LLM de respaldo (ej: Gemini)
        """
        self.llm = llm_client
        self.repo = repository
        self.fallback_llm = fallback_llm
    
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
            max_tokens: Tokens máximos de respuesta
            temperature: Temperatura del modelo
            use_fallback_on_error: Si usar LLM de respaldo en caso de error
            
        Returns:
            Respuesta del LLM
            
        Raises:
            ValueError: Si la sesión no existe
        """
        # 1. Verificar que la sesión existe
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
        
        # 4. Construir system prompt
        system_prompt = self._get_system_prompt(agent_mode)
        
        # 5. Obtener respuesta del LLM
        try:
            response, tokens = await self.llm.get_chat_completion(
                system_prompt=system_prompt,
                messages=history,
                max_tokens=max_tokens,
                temperature=temperature,
                session_id=session_id,
                agent_mode=agent_mode,
                use_cache=True,
            )
        except Exception as e:
            # Intentar con fallback si está disponible
            if use_fallback_on_error and self.fallback_llm:
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
