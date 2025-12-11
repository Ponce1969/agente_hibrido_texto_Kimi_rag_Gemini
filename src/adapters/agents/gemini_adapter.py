"""
Adaptador de Gemini que implementa LLMPort.

Este adaptador conecta con la API de Google Gemini siguiendo
el patrón de arquitectura hexagonal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from src.adapters.config.settings import settings
from src.domain.ports.llm_port import LLMPort

if TYPE_CHECKING:
    from src.domain.models import ChatMessage


class GeminiAdapter(LLMPort):
    """
    Adaptador de Gemini que implementa el puerto LLMPort.

    Características:
    - Usa API de Google Gemini
    - Compatible con generateContent endpoint
    - Fallback para cuando Groq falla
    """

    def __init__(self, client: httpx.AsyncClient) -> None:
        """
        Inicializa el adaptador de Gemini.

        Args:
            client: Cliente HTTP asíncrono
        """
        self.client = client
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model_name

    def _build_contents(
        self,
        system_prompt: str,
        messages: list[ChatMessage]
    ) -> dict[str, Any]:
        """
        Construye el payload para la API de Gemini.

        Args:
            system_prompt: Prompt del sistema
            messages: Historial de mensajes

        Returns:
            Payload en formato Gemini
        """
        parts: list[dict[str, str]] = []

        if system_prompt:
            parts.append({"text": system_prompt})

        for msg in messages:
            parts.append({"text": f"[{msg.role.value}] {msg.content}"})

        return {
            "contents": [
                {
                    "role": "user",
                    "parts": parts if parts else [{"text": ""}],
                }
            ]
        }

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
        Obtiene una respuesta del modelo Gemini.

        Args:
            system_prompt: Prompt del sistema
            messages: Historial de mensajes
            max_tokens: Tokens máximos de respuesta
            temperature: Temperatura del modelo
            session_id: No usado en Gemini
            agent_mode: No usado en Gemini
            use_cache: No usado en Gemini

        Returns:
            Tupla (respuesta, None) - Gemini no retorna tokens
        """
        if not self.api_key:
            raise RuntimeError("Gemini API key no configurada")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

        payload = self._build_contents(system_prompt, messages)

        # Configuración de generación
        gen_cfg: dict[str, Any] = {}
        if max_tokens is not None:
            gen_cfg["maxOutputTokens"] = max_tokens
        if temperature is not None:
            gen_cfg["temperature"] = temperature

        if gen_cfg:
            payload["generationConfig"] = gen_cfg

        # Llamar a API de Gemini
        response = await self.client.post(
            url,
            json=payload,
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=90.0, pool=10.0),
        )
        response.raise_for_status()

        data = response.json()

        # Extraer texto de respuesta
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini no retornó candidatos")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts:
            raise RuntimeError("Gemini no retornó contenido")

        text = parts[0].get("text", "")

        return text, None  # Gemini no retorna conteo de tokens

    async def get_chat_completion_stream(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Obtiene respuesta en modo streaming (no implementado).

        Por ahora retorna la respuesta completa.
        """
        response, _ = await self.get_chat_completion(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response

    def estimate_tokens(self, text: str) -> int:
        """
        Estima tokens usando aproximación simple.

        Regla: ~4 caracteres = 1 token
        """
        return len(text) // 4
