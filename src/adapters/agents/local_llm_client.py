"""
Cliente LLM para modelos locales (Ollama - LLaMA3, Gemma2).

Este cliente se conecta a Ollama local para usar modelos como:
- LLaMA3.1:8b
- Gemma2:2b
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from src.domain.ports import LLMPort

logger = logging.getLogger(__name__)


class LocalLLMClient(LLMPort):
    """
    Cliente para modelos locales vía Ollama.

    Este cliente permite usar modelos locales como fallback o complemento
    a los modelos en la nube.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3.1:8b",
        timeout: int = 60,
    ) -> None:
        """
        Inicializa el cliente Ollama.

        Args:
            base_url: URL del servidor Ollama.
            model_name: Modelo a usar.
            timeout: Timeout en segundos.
        """
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        logger.info("LocalLLMClient inicializado: %s en %s", model_name, base_url)

    async def get_chat_completion(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,  # Ignorado por Ollama, pero tipado
        temperature: float | None = None,
        **_: Any,
    ) -> tuple[str, int]:
        """
        Obtiene una respuesta del modelo local.

        Args:
            system_prompt: Prompt del sistema.
            messages: Lista de mensajes del chat.
            max_tokens: Tokens máximos (no utilizado por Ollama).
            temperature: Temperatura de generación.

        Returns:
            Tupla de (respuesta, tokens_estimados).
        """
        ollama_messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

        for msg in messages:
            if msg.get("role") != "system":
                ollama_messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                )

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False,
        }

        if temperature is not None:
            payload["options"] = {"temperature": temperature}

        logger.debug(
            "Enviando a %s: %d mensajes",
            self.model_name,
            len(ollama_messages),
        )

        try:
            start_time = time.time()

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )

            elapsed = time.time() - start_time

            if response.status_code != 200:
                error_msg = f"Error {response.status_code}: {response.text}"
                logger.error("Error en %s: %s", self.model_name, error_msg)
                raise RuntimeError(error_msg)

            data = response.json()
            reply: str = data.get("message", {}).get("content", "")

            estimated_tokens = max(1, len(reply) // 4)

            logger.info(
                "%s respondió: %d caracteres, %d tokens estimados (%.2fs)",
                self.model_name,
                len(reply),
                estimated_tokens,
                elapsed,
            )

            return reply, estimated_tokens

        except httpx.ConnectError as exc:
            error_msg = f"No se puede conectar a Ollama en {self.base_url}"
            logger.error("Error de conexión: %s", error_msg)
            raise RuntimeError(error_msg) from exc

        except Exception as exc:
            logger.error("Error en LocalLLMClient: %s", exc)
            raise

    async def health_check(self) -> bool:
        """
        Verifica si Ollama está disponible y el modelo existe.

        Returns:
            True si el servicio y el modelo están disponibles.
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                return False

            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            if self.model_name not in model_names:
                logger.warning("Modelo %s no encontrado en Ollama", self.model_name)
                return False

            logger.info("Modelo %s está disponible en Ollama", self.model_name)
            return True

        except Exception as exc:
            logger.error("Error en health_check LocalLLM: %s", exc)
            return False

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self.client.aclose()


class LocalLLMFactory:
    """Fábrica de clientes para modelos locales."""

    @staticmethod
    def create_llama_client() -> LocalLLMClient:
        return LocalLLMClient(
            model_name="llama3.1:8b",
            timeout=90,
        )

    @staticmethod
    def create_gemma_client() -> LocalLLMClient:
        return LocalLLMClient(
            model_name="gemma2:2b",
            timeout=60,
        )

    @staticmethod
    async def get_best_available_model() -> LocalLLMClient | None:
        """
        Retorna el mejor modelo local disponible.
        Prioridad: LLaMA3.1:8b > Gemma2:2b
        """
        llama = LocalLLMFactory.create_llama_client()
        if await llama.health_check():
            await llama.close()
            return LocalLLMFactory.create_llama_client()
        await llama.close()

        gemma = LocalLLMFactory.create_gemma_client()
        if await gemma.health_check():
            await gemma.close()
            return LocalLLMFactory.create_gemma_client()
        await gemma.close()

        logger.warning("No hay modelos locales disponibles en Ollama")
        return None
