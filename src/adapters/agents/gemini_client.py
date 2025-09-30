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
        
        # Extraer texto con múltiples intentos
        try:
            # Intento 1: Formato estándar
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                
                # Verificar si hay contenido
                if "content" in candidate:
                    content = candidate["content"]
                    
                    # Verificar si hay parts
                    if "parts" in content and len(content["parts"]) > 0:
                        # Puede haber múltiples parts, concatenarlos
                        text_parts = []
                        for part in content["parts"]:
                            if "text" in part:
                                text_parts.append(part["text"])
                        
                        if text_parts:
                            return "\n".join(text_parts)
                
                # Si no hay content pero hay finishReason, puede ser que se cortó
                if "finishReason" in candidate:
                    reason = candidate["finishReason"]
                    if reason == "MAX_TOKENS":
                        return "⚠️ La respuesta fue truncada por límite de tokens. Por favor, haz una pregunta más específica."
                    elif reason == "SAFETY":
                        return "⚠️ La respuesta fue bloqueada por filtros de seguridad."
            
            # Si llegamos aquí, la respuesta no tiene el formato esperado
            print(f"⚠️ Respuesta de Gemini con formato inesperado: {data}")
            return "⚠️ Error: No se pudo extraer la respuesta de Gemini. Por favor, intenta de nuevo."
            
        except Exception as e:
            print(f"❌ Error parseando respuesta de Gemini: {e}")
            return f"⚠️ Error procesando respuesta: {str(e)}"
