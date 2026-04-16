"""
Adaptador de DeepSeek que implementa LLMPort.

DeepSeek usa una API compatible con OpenAI, lo que permite
reutilizar el patrón de request con mínimos cambios.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from src.adapters.config.settings import settings
from src.domain.ports.llm_port import LLMPort

if TYPE_CHECKING:
    from src.domain.models import ChatMessage

logger = logging.getLogger(__name__)


class DeepSeekAdapter(LLMPort):
    """
    Adaptador de DeepSeek que implementa el puerto LLMPort.

    DeepSeek ofrece una API OpenAI-compatible, haciendo la integración
    directa y simple. Costo: ~$0.28/M input, ~$0.88/M output (DeepSeek-V3).
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        model: str = "deepseek-chat",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.client = client
        self.model = model
        raw_key = api_key or settings.deepseek_api_key or ""
        self.api_key = raw_key.strip()
        if not self.api_key:
            logger.warning(
                "DeepSeek API key vacía. Las llamadas fallarán con 401. "
                "Configurá DEEPSEEK_API_KEY en .env"
            )
        self.base_url = (base_url or settings.deepseek_base_url).rstrip("/")

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
        """Obtiene una respuesta de DeepSeek via API OpenAI-compatible."""
        api_messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": msg.role.value, "content": msg.content} for msg in messages],
        ]

        payload: dict = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature
            if temperature is not None
            else settings.temperature,
            "max_tokens": max_tokens or settings.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens = usage.get("total_tokens")

            return content, tokens

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (401, 403):
                logger.error(
                    f"DeepSeek AUTH error ({status}): API key inválida o sin permisos. "
                    f"Respuesta: {e.response.text[:300]}"
                )
                raise ConnectionRefusedError(
                    f"DeepSeek API auth failed ({status}): verificá DEEPSEEK_API_KEY"
                ) from e
            logger.error(f"DeepSeek API error: {status} - {e.response.text[:500]}")
            raise
        except httpx.TimeoutException:
            logger.error("DeepSeek API timeout")
            raise
        except Exception as e:
            logger.error(f"DeepSeek unexpected error: {e}")
            raise

    async def get_chat_completion_stream(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Streaming no implementado - retorna respuesta completa."""
        response, _ = await self.get_chat_completion(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            use_cache=False,
        )
        return response

    def estimate_tokens(self, text: str) -> int:
        """Estima tokens: ~4 caracteres = 1 token."""
        return len(text) // 4
