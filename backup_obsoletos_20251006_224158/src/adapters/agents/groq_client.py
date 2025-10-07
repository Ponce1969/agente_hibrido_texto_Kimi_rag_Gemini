"""
Adaptador para comunicarse con la API de Groq.
"""
import httpx
from src.adapters.config.settings import settings
from src.adapters.db.message import ChatMessage
from src.adapters.agents.prompt_manager import prompt_manager, TokenMetrics
from src.adapters.agents.prompts import AgentMode

class GroqClient:
    """Cliente para interactuar con la API de Groq."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_chat_completion(
        self, 
        system_prompt: str, 
        messages: list[ChatMessage], 
        *, 
        max_tokens: int | None = None, 
        temperature: float | None = None,
        session_id: str | None = None,
        agent_mode: AgentMode | None = None,
        use_cache: bool = True
    ) -> tuple[str, TokenMetrics | None]:
        """
        Obtiene una respuesta de chat de la API de Groq.
        
        Args:
            system_prompt: Prompt del sistema (puede ser sobreescrito por caché)
            messages: Historial de mensajes
            max_tokens: Tokens máximos de respuesta
            temperature: Temperatura del modelo
            session_id: ID de sesión para caché
            agent_mode: Modo del agente para caché
            use_cache: Si usar sistema de caché de prompts
            
        Returns:
            Tupla (respuesta, métricas)
        """
        metrics = None
        
        # Si se proporciona session_id y agent_mode, usar caché
        if use_cache and session_id and agent_mode:
            # Obtener prompt optimizado (completo o referencia)
            optimized_prompt, is_cached = prompt_manager.get_prompt(
                session_id=session_id,
                agent_mode=agent_mode
            )
            
            # Limitar historial a últimos 5 mensajes
            limited_messages = prompt_manager.limit_history(messages)
            
            # Registrar métricas
            user_msg = messages[-1].content if messages else ""
            metrics = prompt_manager.record_metrics(
                session_id=session_id,
                system_prompt=optimized_prompt,
                history=limited_messages,
                user_message=user_msg,
                is_cached=is_cached
            )
            
            # Usar prompt optimizado y historial limitado
            system_prompt = optimized_prompt
            messages = limited_messages
        
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
        return data["choices"][0]["message"]["content"], metrics

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
