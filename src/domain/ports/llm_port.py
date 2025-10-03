"""
Puerto (Interface) para clientes de modelos de lenguaje (LLM).

Este puerto define el contrato que deben cumplir todos los adaptadores
de LLM (Groq, Gemini, OpenAI, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.chat_models import ChatMessage

type TokenCount = int


class LLMPort(ABC):
    """
    Puerto para clientes de modelos de lenguaje.
    
    Esta interfaz abstrae la comunicación con diferentes proveedores de LLM,
    permitiendo cambiar la implementación sin afectar la lógica de negocio.
    
    Ejemplos de implementaciones:
        - GroqAdapter: Usa la API de Groq (Kimi-K2)
        - GeminiAdapter: Usa la API de Google Gemini
        - OpenAIAdapter: Usa la API de OpenAI
    """
    
    @abstractmethod
    async def get_chat_completion(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        session_id: str | None = None,
        agent_mode: str | None = None,
        use_cache: bool = True,
    ) -> tuple[str, TokenCount | None]:
        """
        Obtiene una respuesta del modelo de lenguaje.
        
        Args:
            system_prompt: Prompt del sistema que define el comportamiento del LLM
            messages: Historial de mensajes de la conversación
            max_tokens: Número máximo de tokens en la respuesta
            temperature: Temperatura del modelo (0.0 = determinista, 1.0 = creativo)
            session_id: ID de sesión para caché de prompts
            agent_mode: Modo del agente (architect, code_generator, etc.)
            use_cache: Si usar sistema de caché de prompts
            
        Returns:
            Tupla con (respuesta_del_llm, tokens_consumidos)
            
        Raises:
            LLMError: Si hay un error en la comunicación con el LLM
            RateLimitError: Si se excede el límite de rate
        """
        ...
    
    @abstractmethod
    async def get_chat_completion_stream(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:  # AsyncIterator[str] en el futuro
        """
        Obtiene una respuesta del modelo en modo streaming.
        
        Args:
            system_prompt: Prompt del sistema
            messages: Historial de mensajes
            max_tokens: Número máximo de tokens
            temperature: Temperatura del modelo
            
        Returns:
            Respuesta completa del LLM (streaming en futuro)
            
        Raises:
            LLMError: Si hay un error en la comunicación
        """
        ...
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> TokenCount:
        """
        Estima el número de tokens en un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Número estimado de tokens
        """
        ...
