"""
Adaptador de Gemini que implementa LLMPort.

Incluye retry con exponential backoff y circuit breaker.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from src.adapters.agents.circuit_breaker import CircuitBreaker
from src.adapters.agents.retry import retry_with_backoff
from src.adapters.config.settings import settings
from src.domain.ports.llm_port import LLMPort

if TYPE_CHECKING:
    from src.domain.models import ChatMessage

import logging

logger = logging.getLogger(__name__)

_gemini_breaker = CircuitBreaker(
    name="gemini", failure_threshold=3, recovery_seconds=60
)


class GeminiAdapter(LLMPort):
    """Adaptador de Gemini con retry y circuit breaker."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model_name
        self._breaker = _gemini_breaker

    def _build_contents(
        self, system_prompt: str, messages: list[ChatMessage]
    ) -> dict[str, Any]:
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
        if not self.api_key:
            raise RuntimeError("Gemini API key no configurada")

        if self._breaker.is_open:
            raise RuntimeError(
                f"Gemini circuit breaker open ({self._breaker.state}). "
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
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

        payload = self._build_contents(system_prompt, messages)

        gen_cfg: dict[str, Any] = {}
        if max_tokens is not None:
            gen_cfg["maxOutputTokens"] = max_tokens
        if temperature is not None:
            gen_cfg["temperature"] = temperature

        if gen_cfg:
            payload["generationConfig"] = gen_cfg

        headers = {"x-goog-api-key": self.api_key}

        response = await self.client.post(
            url,
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=90.0, pool=10.0),
        )
        response.raise_for_status()

        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini no retornó candidatos")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts:
            raise RuntimeError("Gemini no retornó contenido")

        text = parts[0].get("text", "")

        return text, None

    async def get_chat_completion_stream(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        response, _ = await self.get_chat_completion(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
