"""
Router de proveedores LLM basado en configuración.

Selecciona el adapter correcto (Groq, Gemini, DeepSeek) según
los campos chat_provider, rag_provider y fallback_provider en settings.
Esto permite cambiar de proveedor sin modificar código de servicio.
"""

from __future__ import annotations

import logging

import httpx

from src.adapters.config.settings import settings
from src.domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

_VALID_PROVIDERS = {"groq", "gemini", "deepseek", "none"}


def _create_adapter(provider: str, model: str, client: httpx.AsyncClient) -> LLMPort:
    """Crea una instancia del adapter según el nombre del proveedor."""
    if provider == "groq":
        from src.adapters.agents.groq_adapter import GroqAdapter

        return GroqAdapter(client=client)

    if provider == "gemini":
        from src.adapters.agents.gemini_adapter import GeminiAdapter

        return GeminiAdapter(client=client)

    if provider == "deepseek":
        from src.adapters.agents.deepseek_adapter import DeepSeekAdapter

        return DeepSeekAdapter(client=client, model=model)

    raise ValueError(
        f"Proveedor LLM desconocido: '{provider}'. "
        f"Opciones válidas: {', '.join(_VALID_PROVIDERS - {'none'})}"
    )


def get_chat_llm(client: httpx.AsyncClient) -> LLMPort:
    """
    Retorna el adapter LLM para chat normal.

    Usa settings.chat_provider y settings.chat_model.
    """
    provider = settings.chat_provider.lower()
    if provider not in _VALID_PROVIDERS - {"none"}:
        raise ValueError(f"chat_provider inválido: '{provider}'")

    model = settings.chat_model or settings.groq_model_name
    logger.info(f"LLM Router: chat_provider={provider}, model={model}")
    return _create_adapter(provider, model, client)


def get_rag_llm(client: httpx.AsyncClient) -> LLMPort:
    """
    Retorna el adapter LLM para RAG/PDFs.

    Usa settings.rag_provider y settings.rag_model.
    """
    provider = settings.rag_provider.lower()
    if provider not in _VALID_PROVIDERS - {"none"}:
        raise ValueError(f"rag_provider inválido: '{provider}'")

    model = settings.rag_model or settings.gemini_model_name
    logger.info(f"LLM Router: rag_provider={provider}, model={model}")
    return _create_adapter(provider, model, client)


def get_fallback_llm(client: httpx.AsyncClient) -> LLMPort | None:
    """
    Retorna el adapter LLM de fallback, o None si está deshabilitado.

    Usa settings.fallback_provider y settings.fallback_model.
    fallback_provider='none' deshabilita el fallback.
    """
    provider = settings.fallback_provider.lower()
    if provider == "none":
        logger.info("LLM Router: fallback deshabilitado (fallback_provider=none)")
        return None

    if provider not in _VALID_PROVIDERS - {"none"}:
        raise ValueError(f"fallback_provider inválido: '{provider}'")

    model = settings.fallback_model or settings.gemini_model_name
    logger.info(f"LLM Router: fallback_provider={provider}, model={model}")
    return _create_adapter(provider, model, client)


def log_routing_config() -> None:
    """Loguea la configuración de routing al inicio de la aplicación."""
    logger.info(
        f"LLM Routing config: "
        f"chat={settings.chat_provider}/{settings.chat_model}, "
        f"rag={settings.rag_provider}/{settings.rag_model}, "
        f"fallback={settings.fallback_provider}/{settings.fallback_model}"
    )
