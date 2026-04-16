"""
Adaptador de DeepSeek que implementa LLMPort.

DeepSeek usa una API compatible con OpenAI. Incluye:
- Retry con exponential backoff para errores transitorios
- Circuit breaker para deshabilitar provider tras fallos consecutivos
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from src.adapters.agents.circuit_breaker import CircuitBreaker
from src.adapters.agents.retry import retry_with_backoff
from src.adapters.config.settings import settings
from src.domain.ports.llm_port import LLMPort

if TYPE_CHECKING:
    from src.domain.models import ChatMessage

logger = logging.getLogger(__name__)

# Circuit breaker compartido para DeepSeek
_deepseek_breaker = CircuitBreaker(
    name="deepseek", failure_threshold=3, recovery_seconds=60
)


class DeepSeekAdapter(LLMPort):
    """
    Adaptador de DeepSeek que implementa el puerto LLMPort.

    Incluye retry automático y circuit breaker.
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
        self._breaker = _deepseek_breaker

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
        """Obtiene una respuesta de DeepSeek con retry y circuit breaker."""
        if self._breaker.is_open:
            raise RuntimeError(
                f"DeepSeek circuit breaker open ({self._breaker.state}). "
                f"Provider temporalmente deshabilitado."
            )

        try:
            result = await retry_with_backoff(
                self._call_api,
                system_prompt=system_prompt,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                max_retries=3,
                base_delay=1.0,
            )
            self._breaker.record_success()
            return result
        except Exception:
            self._breaker.record_failure()
            raise

    async def _call_api(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> tuple[str, int | None]:
        """Llamada directa a la API de DeepSeek (sin retry)."""
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

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
        )

        if response.status_code in (401, 403):
            logger.error(
                f"DeepSeek AUTH error ({response.status_code}): API key inválida."
            )
            raise ConnectionRefusedError(
                f"DeepSeek API auth failed ({response.status_code})"
            )

        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens")

        return content, tokens

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
