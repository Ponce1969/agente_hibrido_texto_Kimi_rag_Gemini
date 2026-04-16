"""
Adaptador de Groq que implementa LLMPort.

Incluye retry con exponential backoff y circuit breaker.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from src.adapters.agents.circuit_breaker import CircuitBreaker
from src.adapters.agents.prompt_manager import prompt_manager
from src.adapters.agents.retry import retry_with_backoff
from src.adapters.config.settings import settings
from src.domain.ports.llm_port import LLMPort

if TYPE_CHECKING:
    from src.domain.models import ChatMessage

logger = logging.getLogger(__name__)

_groq_breaker = CircuitBreaker(name="groq", failure_threshold=3, recovery_seconds=60)


class GroqAdapter(LLMPort):
    """Adaptador de Groq con retry, circuit breaker y caché de prompts."""

    def __init__(self, client: httpx.AsyncClient, model: str | None = None) -> None:
        self.client = client
        self.model = model or settings.groq_model_name
        raw_key = settings.groq_api_key
        self.api_key = raw_key.strip() if raw_key else ""
        if not self.api_key:
            logger.warning(
                "Groq API key vacía. Las llamadas fallarán con 401. "
                "Configurá GROQ_API_KEY en .env"
            )
        self._breaker = _groq_breaker

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
        if self._breaker.is_open:
            raise RuntimeError(
                f"Groq circuit breaker open ({self._breaker.state}). "
                f"Provider temporalmente deshabilitado."
            )

        tokens_consumed = None

        if use_cache and session_id and agent_mode:
            from src.adapters.agents.prompts import AgentMode

            try:
                mode_enum = (
                    AgentMode(agent_mode) if isinstance(agent_mode, str) else agent_mode
                )
            except ValueError:
                mode_enum = None

            if mode_enum:
                optimized_prompt, is_cached = prompt_manager.get_prompt(
                    session_id=session_id, agent_mode=mode_enum
                )
                limited_messages = prompt_manager.limit_history(messages)
                user_msg = messages[-1].content if messages else ""
                metrics = prompt_manager.record_metrics(
                    session_id=session_id,
                    system_prompt=optimized_prompt,
                    history=limited_messages,
                    user_message=user_msg,
                    is_cached=is_cached,
                )
                system_prompt = optimized_prompt
                messages = limited_messages
                tokens_consumed = metrics.total_tokens if metrics else None

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
            content, _ = result
            return content, tokens_consumed
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
        api_messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": msg.role.value, "content": msg.content} for msg in messages],
        ]

        response = await self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "messages": api_messages,
                "model": self.model,
                "temperature": temperature
                if temperature is not None
                else settings.temperature,
                "max_tokens": max_tokens or settings.max_tokens,
            },
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=90.0, pool=10.0),
        )

        if response.status_code in (401, 403):
            logger.error(f"Groq AUTH error ({response.status_code}): API key inválida.")
            raise ConnectionRefusedError(
                f"Groq API auth failed ({response.status_code})"
            )

        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return content, None

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
            use_cache=False,
        )
        return response

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
