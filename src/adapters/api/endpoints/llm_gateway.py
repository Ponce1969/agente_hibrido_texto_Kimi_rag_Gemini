"""
Endpoint Interno LLM Gateway para Modelos Locales.

Este endpoint es exclusivo para modelos locales (LLaMA, Gemma) y no es visible
en el frontend. Permite que los modelos locales accedan al RAG y Kimi sin
modificar la arquitectura existente.

Flujo: LLaMA (local) → /api/internal/llm-gateway → Backend → RAG/Kimi → Cache → Respuesta
"""
import hashlib
import logging
import sqlite3
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.adapters.dependencies import get_chat_service_dependency
from src.application.services.chat_service_hibrido_mejorado import (
    ChatServiceHibridoMejorado,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas del Gateway ---

class LLMGatewayRequest(BaseModel):
    """Request para el LLM Gateway interno."""
    query: str
    mode: str = "auto"  # "auto" | "kimi" | "rag"
    session_id: int = 1  # Sesión por defecto para modelos locales


class LLMGatewayResponse(BaseModel):
    """Response del LLM Gateway."""
    answer: str
    mode_used: str
    cached: bool
    timestamp: str


# --- Cache SQLite para respuestas ---

class ResponseCache:
    """Cache simple en SQLite para respuestas del gateway."""

    def __init__(self, db_path: str = "llm_gateway_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE NOT NULL,
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    mode_used TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            conn.commit()

    def _get_query_hash(self, query: str, mode: str) -> str:
        """Genera hash único para query+mode."""
        content = f"{query.lower().strip()}:{mode}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, query: str, mode: str) -> str | None:
        """Obtiene respuesta cacheada si no ha expirado."""
        query_hash = self._get_query_hash(query, mode)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT answer FROM cached_responses
                WHERE query_hash = ? AND expires_at > datetime('now')
            """, (query_hash,))
            result = cursor.fetchone()

            if result:
                logger.info(f"Cache HIT para query: {query[:50]}...")
                return result[0]

            logger.info(f"Cache MISS para query: {query[:50]}...")
            return None

    def save(self, query: str, answer: str, mode: str, ttl_hours: int = 24):
        """Guarda respuesta en cache con TTL."""
        query_hash = self._get_query_hash(query, mode)
        expires_at = datetime.now(UTC).replace(microsecond=0) + timedelta(hours=ttl_hours)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cached_responses
                (query_hash, query, answer, mode_used, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query_hash, query, answer, mode, expires_at))
            conn.commit()
            logger.info(f"Respuesta cacheada para query: {query[:50]}...")


# Instancia global del cache
cache = ResponseCache()


# --- Heurísticas para modo automático ---

def should_use_rag(query: str) -> bool:
    """
    Heurísticas para decidir si usar RAG o Kimi en modo automático.

    RAG para:
    - Preguntas sobre conceptos técnicos específicos
    - Definiciones y explicaciones detalladas
    - Referencias a documentos o libros
    - Preguntas con "qué es", "cómo funciona", "explicar"

    Kimi para:
    - Consultas generales
    - Preguntas cortas y conversacionales
    - Tareas que no requieren conocimiento profundo
    """
    query_lower = query.lower()

    # Indicadores fuertes de RAG
    rag_keywords = [
        "qué es", "qué significa", "cómo funciona", "explicar",
        "definición", "principio", "concepto", "según el pdf",
        "según el libro", "documentación", "technical", "arquitectura"
    ]

    # Indicadores de Kimi
    kimi_keywords = [
        "hola", "buenos días", "cómo estás", "gracias",
        "tiempo", "clima", "noticias", "conversar"
    ]

    # Priorizar RAG para preguntas técnicas
    for keyword in rag_keywords:
        if keyword in query_lower:
            return True

    # Priorizar Kimi para conversación
    for keyword in kimi_keywords:
        if keyword in query_lower:
            return False

    # Por defecto, usar RAG para queries más largas (técnicas)
    return len(query) > 50


# --- Endpoint del Gateway ---

@router.post("/llm-gateway", response_model=LLMGatewayResponse)
async def llm_gateway(
    request: LLMGatewayRequest,
    service: ChatServiceHibridoMejorado = Depends(get_chat_service_dependency),
):
    """
    Gateway interno para modelos locales LLaMA/Gemma.

    Este endpoint permite que los modelos locales accedan al RAG y Kimi
    sin modificar el frontend. Incluye cache y heurísticas automáticas.
    """
    try:
        # 1. Verificar cache primero
        cached_answer = cache.get(request.query, request.mode)
        if cached_answer:
            return LLMGatewayResponse(
                answer=cached_answer,
                mode_used=request.mode,
                cached=True,
                timestamp=datetime.now(UTC).isoformat()
            )

        # 2. Decidir modo de procesamiento
        if request.mode == "auto":
            mode_used = "rag" if should_use_rag(request.query) else "kimi"
        else:
            mode_used = request.mode

        logger.info(f"Procesando query con modo: {mode_used}")

        # 3. Llamar al servicio correspondiente
        if mode_used == "rag":
            answer = await service._handle_with_rag_gemini(
                session_id=str(request.session_id),
                user_message=request.query
            )
        elif mode_used == "kimi":
            answer = await service._handle_with_kimi(
                session_id=str(request.session_id),
                user_message=request.query
            )
        else:
            raise HTTPException(status_code=400, detail=f"Modo no soportado: {request.mode}")

        # 4. Guardar en cache
        cache.save(request.query, answer, mode_used)

        # 5. Devolver respuesta
        return LLMGatewayResponse(
            answer=answer,
            mode_used=mode_used,
            cached=False,
            timestamp=datetime.now(UTC).isoformat()
        )

    except Exception as e:
        logger.error(f"Error en llm_gateway: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del gateway: {str(e)}") from None


@router.get("/llm-gateway/status")
async def gateway_status():
    """Endpoint de estado para monitoreo del gateway."""
    try:
        with sqlite3.connect(cache.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as active
                FROM cached_responses
            """)
            stats = cursor.fetchone()

        return {
            "status": "operational",
            "cache_stats": {
                "total_cached": stats[0] or 0,
                "active_entries": stats[1] or 0
            },
            "timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Error en gateway_status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }
