"""
Adaptador de Groq que implementa LLMPort.

Este adaptador conecta con la API de Groq (Kimi-K2) siguiendo
el patrón de arquitectura hexagonal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from src.domain.ports.llm_port import LLMPort
from src.adapters.config.settings import settings
from src.adapters.agents.prompt_manager import prompt_manager

if TYPE_CHECKING:
    from src.domain.models import ChatMessage


class GroqAdapter(LLMPort):
    """
    Adaptador de Groq que implementa el puerto LLMPort.
    
    Características:
    - Usa API de Groq (Kimi-K2)
    - Sistema de caché de prompts integrado
    - Limitación de historial automática
    - Métricas de tokens
    """
    
    def __init__(self, client: httpx.AsyncClient) -> None:
        """
        Inicializa el adaptador de Groq.
        
        Args:
            client: Cliente HTTP asíncrono para hacer requests
        """
        self.client = client
    
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
    ) -> tuple[str, int | None]:
        """
        Obtiene una respuesta del modelo Kimi-K2 via Groq.
        
        Args:
            system_prompt: Prompt del sistema
            messages: Historial de mensajes
            max_tokens: Tokens máximos de respuesta
            temperature: Temperatura del modelo (0.0-1.0)
            session_id: ID de sesión para caché
            agent_mode: Modo del agente para caché
            use_cache: Si usar sistema de caché
            
        Returns:
            Tupla (respuesta, tokens_consumidos)
        """
        tokens_consumed = None
        
        # Sistema de caché de prompts
        if use_cache and session_id and agent_mode:
            from src.adapters.agents.prompts import AgentMode
            
            # Convertir string a AgentMode si es necesario
            try:
                mode_enum = AgentMode(agent_mode) if isinstance(agent_mode, str) else agent_mode
            except ValueError:
                mode_enum = None
            
            if mode_enum:
                # Obtener prompt optimizado
                optimized_prompt, is_cached = prompt_manager.get_prompt(
                    session_id=session_id,
                    agent_mode=mode_enum
                )
                
                # Limitar historial
                limited_messages = prompt_manager.limit_history(messages)
                
                # Registrar métricas
                user_msg = messages[-1].content if messages else ""
                metrics = prompt_manager.record_metrics(
                    session_id=session_id,
                    system_prompt=optimized_prompt,
                    history=limited_messages,
                    user_message=user_msg,
                    is_cached=is_cached
                )
                
                # Usar prompt y mensajes optimizados
                system_prompt = optimized_prompt
                messages = limited_messages
                tokens_consumed = metrics.total_tokens if metrics else None
        
        # Construir mensajes para API
        api_messages = [
            {"role": "system", "content": system_prompt},
            *[
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ],
        ]
        
        # Llamar a API de Groq
        response = await self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "messages": api_messages,
                "model": settings.groq_model_name,
                "temperature": temperature if temperature is not None else settings.temperature,
                "max_tokens": max_tokens or settings.max_tokens,
            },
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=90.0, pool=10.0),
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        return content, tokens_consumed
    
    async def get_chat_completion_stream(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Obtiene respuesta en modo streaming (no implementado aún).
        
        Por ahora retorna la respuesta completa.
        """
        response, _ = await self.get_chat_completion(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            use_cache=False,  # No usar caché en streaming
        )
        return response
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima tokens usando aproximación simple.
        
        Regla: ~4 caracteres = 1 token
        """
        return len(text) // 4
