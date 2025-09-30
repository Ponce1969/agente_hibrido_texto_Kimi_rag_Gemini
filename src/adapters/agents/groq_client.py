"""
Adaptador para comunicarse con la API de Groq.
"""
import httpx
from src.adapters.config.settings import settings
from src.adapters.db.message import ChatMessage

class GroqClient:
    """Cliente para interactuar con la API de Groq."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_chat_completion(
        self, system_prompt: str, messages: list[ChatMessage], *, max_tokens: int | None = None, temperature: float | None = None
    ) -> str:
        """Obtiene una respuesta de chat de la API de Groq."""
        api_messages = [
            {"role": "system", "content": system_prompt},
            *[
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ],
        ]

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
        response.raise_for_status()  # Lanza una excepción si la petición falla
        
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_with_tools(self, messages: list[dict], tools: list[dict], tool_choice: str = "auto", *, max_tokens: int | None = None) -> dict:
        """Envía una conversación con herramientas y devuelve el JSON crudo de la API.

        Espera mensajes en formato OpenAI-compatible, e.g.:
            messages=[{"role":"system","content":"..."}, {"role":"user","content":"..."}]
            tools=[{"type":"function","function":{"name":"...","description":"...","parameters":{...}}}, ...]
        """
        payload = {
            "messages": messages,
            "model": settings.groq_model_name,
            "temperature": settings.temperature,
            "max_tokens": max_tokens or settings.max_tokens,
            "tools": tools,
            "tool_choice": tool_choice,
        }
        resp = await self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=90.0, pool=10.0),
        )
        resp.raise_for_status()
        return resp.json()
