"""
Cliente mínimo para la API de Gemini (Google AI Studio).
Usa el endpoint generateContent de la API REST.
"""
from __future__ import annotations
import httpx
from typing import List, Dict, Any, Optional
from src.adapters.config.settings import settings
from src.adapters.db.message import ChatMessage


class GeminiClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model_name

    def _build_contents(self, system_prompt: str, messages: List[ChatMessage]) -> Dict[str, Any]:
        parts: List[Dict[str, str]] = []
        if system_prompt:
            parts.append({"text": system_prompt})
        for m in messages:
            parts.append({"text": f"[{m.role.value}] {m.content}"})
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
        messages: List[ChatMessage],
        *,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini API key no configurada")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = self._build_contents(system_prompt, messages)
        gen_cfg: Dict[str, Any] = {}
        if max_tokens is not None:
            gen_cfg["maxOutputTokens"] = max_tokens
        if temperature is not None:
            gen_cfg["temperature"] = temperature
        if gen_cfg:
            payload["generationConfig"] = gen_cfg
        resp = await self.client.post(url, json=payload, timeout=httpx.Timeout(connect=10.0, read=90.0, write=90.0, pool=10.0))
        resp.raise_for_status()
        data = resp.json()
        # Extraer texto
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            # Respuesta inesperada
            return str(data)
