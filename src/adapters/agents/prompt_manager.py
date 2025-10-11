"""
Sistema de gestión de prompts con caché inteligente para reducir tokens.

Estrategia:
- Primera llamada por sesión: prompt completo + few-shot (~1750 tokens)
- Llamadas subsecuentes: referencia corta (~300-400 tokens)
- Historial limitado a 5 mensajes más recientes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from src.adapters.agents.prompts import AgentMode, get_system_prompt


@dataclass
class TokenMetrics:
    """Métricas de consumo de tokens por llamada."""
    
    session_id: str
    call_number: int
    system_tokens: int
    history_tokens: int
    user_tokens: int
    total_tokens: int
    is_cached: bool


class PromptManager:
    """
    Gestor de prompts con caché por sesión para optimizar consumo de tokens.
    
    Funcionalidad:
    - Cachea el prompt completo después de la primera llamada
    - Usa referencias cortas en llamadas subsecuentes
    - Limita historial a N mensajes más recientes
    - Registra métricas de tokens consumidos
    """
    
    # Configuración
    MAX_HISTORY_MESSAGES: Final[int] = 5  # Últimos 5 mensajes (user + assistant)
    CHARS_PER_TOKEN: Final[float] = 4.0   # Aproximación: 4 chars = 1 token
    
    def __init__(self):
        # Caché de prompts por sesión: {session_id: {agent_mode: prompt_completo}}
        self._prompt_cache: dict[str, dict[AgentMode, str]] = {}
        # Contador de llamadas por sesión
        self._call_count: dict[str, int] = {}
        # Métricas acumuladas
        self.metrics: list[TokenMetrics] = []
    
    def get_prompt(
        self,
        session_id: str,
        agent_mode: AgentMode,
        include_few_shot: bool = True
    ) -> tuple[str, bool]:
        """
        Obtiene el prompt optimizado para la sesión.
        
        Args:
            session_id: ID de la sesión de chat
            agent_mode: Modo del agente
            include_few_shot: Si incluir ejemplos (solo primera llamada)
            
        Returns:
            Tupla (prompt, is_cached)
            - Primera llamada: (prompt_completo, False)
            - Llamadas subsecuentes: (referencia_corta, True)
        """
        # Incrementar contador de llamadas
        if session_id not in self._call_count:
            self._call_count[session_id] = 0
        self._call_count[session_id] += 1
        
        call_num = self._call_count[session_id]
        
        # Primera llamada: prompt completo
        if call_num == 1:
            prompt = get_system_prompt(agent_mode)
            
            # Cachear para futuras llamadas
            if session_id not in self._prompt_cache:
                self._prompt_cache[session_id] = {}
            self._prompt_cache[session_id][agent_mode] = prompt
            
            return prompt, False
        
        # Llamadas subsecuentes: referencia corta
        else:
            # Crear referencia corta al prompt cacheado
            short_ref = self._create_short_reference(agent_mode)
            return short_ref, True
    
    def _create_short_reference(self, agent_mode: AgentMode) -> str:
        """
        Crea una referencia corta al prompt completo.
        
        Reduce de ~2000 tokens a ~100-150 tokens.
        """
        # Mapeo de modos a referencias cortas
        references = {
            AgentMode.PYTHON_ARCHITECT: (
                "Role: SoftwareArchitect-15y (Python 3.12+)\n"
                "Focus: Hexagonal Architecture, SOLID, Clean Code\n"
                "Stack: FastAPI, SQLAlchemy 2.0, Pydantic v2\n"
                "Output: Type-hinted code with docstrings\n"
                "Quality: mypy --strict, ruff check, 90% coverage"
            ),
            AgentMode.CODE_GENERATOR: (
                "Role: CodeEngineer (Python 3.12+)\n"
                "Focus: Efficient modern Python solutions\n"
                "Stack: FastAPI, SQLAlchemy, asyncio\n"
                "Output: Production-ready code with tests"
            ),
            AgentMode.SECURITY_ANALYST: (
                "Role: SecurityAuditor\n"
                "Focus: OWASP Top 10, CVE scanning, SAST\n"
                "Tools: bandit, semgrep, pip-audit\n"
                "Output: Vulnerability report + mitigation"
            ),
            AgentMode.DATABASE_SPECIALIST: (
                "Role: DBA-Specialist (PostgreSQL 15+)\n"
                "Focus: Schema design, query optimization\n"
                "Tools: EXPLAIN ANALYZE, indexes, RLS\n"
                "Output: Optimized SQL + rationale"
            ),
            AgentMode.REFACTOR_ENGINEER: (
                "Role: RefactorEngineer (Python 3.12+)\n"
                "Focus: Code smells, SOLID principles\n"
                "Tools: ruff, mypy, radon\n"
                "Output: Refactored code + explanation"
            ),
        }
        
        return references.get(agent_mode, f"Role: {agent_mode.value}")
    
    def limit_history(self, messages: list) -> list:
        """
        Limita el historial a los últimos N mensajes.
        
        Args:
            messages: Lista completa de mensajes
            
        Returns:
            Lista truncada a MAX_HISTORY_MESSAGES más recientes
        """
        if len(messages) <= self.MAX_HISTORY_MESSAGES:
            return messages
        
        # Tomar últimos N mensajes
        return messages[-self.MAX_HISTORY_MESSAGES:]
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima tokens usando aproximación simple.
        
        Args:
            text: Texto a estimar
            
        Returns:
            Número estimado de tokens
        """
        return int(len(text) / self.CHARS_PER_TOKEN)
    
    def record_metrics(
        self,
        session_id: str,
        system_prompt: str,
        history: list,
        user_message: str,
        is_cached: bool
    ) -> TokenMetrics:
        """
        Registra métricas de tokens para una llamada.
        
        Args:
            session_id: ID de sesión
            system_prompt: Prompt del sistema usado
            history: Mensajes del historial
            user_message: Mensaje del usuario
            is_cached: Si se usó caché
            
        Returns:
            Métricas de la llamada
        """
        # Calcular tokens
        system_tokens = self.estimate_tokens(system_prompt)
        
        # Tokens del historial
        history_text = " ".join([msg.content for msg in history])
        history_tokens = self.estimate_tokens(history_text)
        
        user_tokens = self.estimate_tokens(user_message)
        total_tokens = system_tokens + history_tokens + user_tokens
        
        # Crear métrica
        metrics = TokenMetrics(
            session_id=session_id,
            call_number=self._call_count.get(session_id, 0),
            system_tokens=system_tokens,
            history_tokens=history_tokens,
            user_tokens=user_tokens,
            total_tokens=total_tokens,
            is_cached=is_cached
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def get_session_stats(self, session_id: str) -> dict:
        """
        Obtiene estadísticas de una sesión.
        
        Args:
            session_id: ID de sesión
            
        Returns:
            Diccionario con estadísticas
        """
        session_metrics = [m for m in self.metrics if m.session_id == session_id]
        
        if not session_metrics:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "avg_tokens_per_call": 0,
                "tokens_saved": 0
            }
        
        total_calls = len(session_metrics)
        total_tokens = sum(m.total_tokens for m in session_metrics)
        avg_tokens = total_tokens / total_calls if total_calls > 0 else 0
        
        # Calcular ahorro (primera llamada vs resto)
        first_call_tokens = session_metrics[0].total_tokens if session_metrics else 0
        cached_calls = [m for m in session_metrics if m.is_cached]
        avg_cached_tokens = (
            sum(m.total_tokens for m in cached_calls) / len(cached_calls)
            if cached_calls else 0
        )
        tokens_saved = (first_call_tokens - avg_cached_tokens) * len(cached_calls)
        
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "avg_tokens_per_call": int(avg_tokens),
            "tokens_saved": int(tokens_saved),
            "first_call_tokens": first_call_tokens,
            "avg_cached_tokens": int(avg_cached_tokens),
            "savings_percentage": (
                int((tokens_saved / (total_tokens + tokens_saved)) * 100)
                if total_tokens > 0 else 0
            )
        }
    
    def clear_session_cache(self, session_id: str) -> None:
        """Limpia el caché de una sesión específica."""
        if session_id in self._prompt_cache:
            del self._prompt_cache[session_id]
        if session_id in self._call_count:
            del self._call_count[session_id]
    
    def get_global_stats(self) -> dict:
        """Obtiene estadísticas globales de todas las sesiones."""
        if not self.metrics:
            return {
                "total_sessions": 0,
                "total_calls": 0,
                "total_tokens": 0,
                "total_saved": 0,
                "avg_tokens_per_call": 0,
                "savings_percentage": 0
            }
        
        sessions = set(m.session_id for m in self.metrics)
        total_tokens = sum(m.total_tokens for m in self.metrics)
        
        # Calcular ahorro total
        total_saved = 0
        for session_id in sessions:
            stats = self.get_session_stats(session_id)
            total_saved += stats["tokens_saved"]
        
        return {
            "total_sessions": len(sessions),
            "total_calls": len(self.metrics),
            "total_tokens": total_tokens,
            "total_saved": total_saved,
            "avg_tokens_per_call": int(total_tokens / len(self.metrics)),
            "savings_percentage": (
                int((total_saved / (total_tokens + total_saved)) * 100)
                if total_tokens > 0 else 0
            )
        }


# Instancia global del gestor
prompt_manager = PromptManager()
