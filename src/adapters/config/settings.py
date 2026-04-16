"""
Módulo de configuración centralizado para la aplicación.

Utiliza pydantic-settings para cargar y validar la configuración desde
variables de entorno y/o un archivo .env.
"""

import logging

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

logger = logging.getLogger(__name__)


def _mask_key(key: str) -> str:
    """Enmascara una API key mostrando solo los primeros 4 y últimos 4 caracteres."""
    if not key or len(key) < 12:
        return "***EMPTY_OR_TOO_SHORT***" if not key else f"***{len(key)}chars***"
    return f"{key[:4]}...{key[-4:]}"


class Settings(BaseSettings):
    """
    Define las variables de configuración de la aplicación.
    """

    # Configuración para pydantic-settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Entorno ---
    environment: str = Field(
        "production", description="Entorno de ejecución: development o production"
    )

    # --- API Keys y Secretos ---
    groq_api_key: str = Field(..., description="API key para Groq.")
    gemini_api_key: str | None = Field(
        None, description="API key para Gemini (Google AI Studio)"
    )
    deepseek_api_key: str | None = Field(
        None, description="API key para DeepSeek (OpenAI-compatible)"
    )
    bear_api_key: str = Field(
        ..., description="API key para Bear API (búsqueda Python)"
    )

    # --- Seguridad y Autenticación ---
    jwt_secret_key: str = Field(
        ...,
        description="Clave secreta para firmar tokens JWT. DEBE ser única y segura en producción.",
    )
    jwt_expire_minutes: int = Field(
        60,
        description="Tiempo de expiración de tokens JWT en minutos (default: 60 = 1 hora)",
    )
    rag_api_key: str = Field(
        ...,
        description="API Key para proteger el endpoint interno del LLM Gateway (acceso desde CLI).",
    )

    # --- Modelo LLM: Provider Routing ---
    chat_provider: str = Field(
        "groq", description="Provider para chat normal: groq | deepseek | gemini"
    )
    chat_model: str = Field(
        "moonshotai/kimi-k2-instruct-0905",
        description="Modelo para chat normal (usado por el provider seleccionado)",
    )
    rag_provider: str = Field(
        "gemini", description="Provider para RAG/PDFs: gemini | deepseek | groq"
    )
    rag_model: str = Field(
        "gemini-2.5-flash",
        description="Modelo para RAG/PDFs (usado por el provider seleccionado)",
    )
    fallback_provider: str = Field(
        "gemini",
        description="Provider de fallback cuando el principal falla: gemini | deepseek | groq | none",
    )
    fallback_model: str = Field(
        "gemini-2.5-flash",
        description="Modelo de fallback (usado por el provider seleccionado)",
    )
    # Compatibilidad: estos aliases mapean a los nuevos campos
    groq_model_name: str = Field(
        "moonshotai/kimi-k2-instruct-0905",
        description="Alias para chat_model cuando chat_provider=groq.",
    )
    gemini_model_name: str = Field(
        "gemini-2.5-flash",
        description="Alias para rag_model cuando rag_provider=gemini.",
    )
    llm_provider_preference: str = Field(
        "gemini_for_pdf_kimi_for_chat",
        description="Estrategia legacy de routing (se ignora si se usan los nuevos campos).",
    )
    temperature: float = Field(
        0.3, description="Temperatura para la generación del modelo (creatividad)."
    )
    max_tokens: int = Field(
        4096,
        description="Máximo de tokens a generar en la respuesta (ajustado para respuestas concisas)",
    )

    # --- DeepSeek Config ---
    deepseek_base_url: str = Field(
        "https://api.deepseek.com/v1",
        description="URL base de la API de DeepSeek (OpenAI-compatible)",
    )

    # --- Base de Datos ---
    database_url: str = Field(
        "sqlite:///./data/chat_history.db",
        description="URL de conexión a la base de datos por defecto (SQLite).",
    )
    # URL opcional para Postgres (pgvector). Si no se establece, se ignora y la app sigue usando SQLite.
    database_url_pg: str | None = Field(
        default=None,
        description="URL de conexión a PostgreSQL (opcional) para almacenamiento de embeddings con pgvector.",
    )

    # Backend de base de datos a usar
    db_backend: str = Field(
        "sqlite", description="Backend de base de datos: sqlite o postgresql"
    )

    @property
    def effective_database_url(self) -> str:
        """Retorna la URL efectiva de base de datos según la configuración."""
        if self.db_backend == "postgresql" and self.database_url_pg:
            return self.database_url_pg
        return self.database_url

    # --- Archivos / Contexto ---
    file_context_max_chars: int = Field(
        6000,
        description="Máximo de caracteres a incluir del texto extraído de archivos.",
    )
    file_max_pdf_pages: int = Field(
        20,
        description="Máximo de páginas de PDF a procesar (para evitar timeouts). 0 = sin límite",
    )
    file_chapter_max_pages: int = Field(
        12,
        description="Ventana de páginas por sección (capítulo) para segmentar PDFs grandes.",
    )
    file_max_pdf_size_mb: int = Field(
        50,
        description="Tamaño máximo permitido para archivos PDF subidos (en MB)",
    )

    # --- Embeddings / Rendimiento (Optimizado para AMD APU A10, 16GB RAM) ---
    embedding_batch_size: int = Field(
        2,
        description="Tamaño de lote para encode() del modelo de embeddings. Optimizado para bajos recursos (2-4)",
    )

    # --- Chunking de texto (optimizado para definiciones técnicas) ---
    embedding_chunk_size: int = Field(
        800,
        description="Tamaño de chunk de texto para indexación de PDFs (caracteres) - reducido para mejor precisión en definiciones",
    )
    embedding_chunk_overlap: int = Field(
        200,
        description="Solapamiento entre chunks de texto (caracteres) - aumentado para preservar contexto conceptual",
    )

    # --- Búsqueda Python (Brave Search API) ---
    bear_base_url: str = Field(
        "https://api.search.brave.com/res/v1/web/search",
        description="URL base de Brave Search API para búsquedas web especializadas",
    )
    bear_search_enabled: bool = Field(
        True,
        description="Habilitar/deshabilitar búsqueda con Bear API",
    )
    bear_cache_ttl: int = Field(
        3600,
        description="Tiempo de vida del caché en segundos (1 hora por defecto)",
    )
    max_search_results: int = Field(
        10,
        description="Máximo de resultados de búsqueda a incluir en el contexto (aumentado para mejor cobertura)",
    )

    # --- Búsqueda RAG Adaptativa ---
    rag_simple_top_k: int = Field(
        5,
        description="Número de chunks para preguntas simples (¿Qué es X?)",
    )
    rag_normal_top_k: int = Field(
        8,
        description="Número de chunks para preguntas normales",
    )
    rag_complex_top_k: int = Field(
        12,
        description="Número de chunks para preguntas complejas",
    )
    rag_simple_limit: int = Field(
        4000,
        description="Límite de caracteres de contexto para preguntas simples",
    )
    rag_normal_limit: int = Field(
        8000,
        description="Límite de caracteres de contexto para preguntas normales",
    )
    rag_complex_limit: int = Field(
        15000,
        description="Límite de caracteres de contexto para preguntas complejas",
    )

    # --- Guardian (Qwen2.5-1.5B Security) ---
    guardian_enabled: bool = Field(
        True,
        description="Habilitar/deshabilitar Guardian de seguridad",
    )
    guardian_llm_enabled: bool = Field(
        False,
        description="Usar LLM externo (SiliconFlow) para Guardian. False = solo heurísticas (rápido, sin dependencia externa)",
    )
    guardian_api_url: str = Field(
        "https://api.siliconflow.cn/v1/chat/completions",
        description="URL de la API de HuggingFace/SiliconFlow para Qwen Guardian",
    )
    guardian_api_key: str = Field(
        ...,
        description="API key para HuggingFace/SiliconFlow (Qwen Guardian)",
    )
    guardian_timeout: int = Field(
        10,
        description="Timeout en segundos para llamadas al Guardian",
    )
    guardian_max_calls_per_minute: int = Field(
        10,
        description="Máximo de llamadas al Guardian por minuto (rate limiting)",
    )
    guardian_cache_ttl: int = Field(
        3600,
        description="Tiempo de vida del caché del Guardian en segundos (1 hora)",
    )
    guardian_min_length: int = Field(
        20,
        description="Longitud mínima de mensaje para activar Guardian (caracteres)",
    )

    def validate_api_keys(self) -> list[str]:
        """Valida las API keys al arrancar. Retorna lista de problemas encontrados."""
        issues: list[str] = []

        key_configs = [
            ("groq", self.groq_api_key, "gsk_", self.chat_provider == "groq"),
            (
                "deepseek",
                self.deepseek_api_key,
                "sk-",
                self.chat_provider == "deepseek",
            ),
            ("gemini", self.gemini_api_key, "AI", self.rag_provider == "gemini"),
            ("guardian", self.guardian_api_key, "", self.guardian_llm_enabled),
        ]

        for name, key, expected_prefix, is_active in key_configs:
            if not key:
                if is_active:
                    issues.append(
                        f"❌ {name}_api_key: VACÍA pero {name} está activo como provider"
                    )
                else:
                    logger.warning(
                        f"⚠️ {name}_api_key: no configurada (provider inactivo)"
                    )
            else:
                cleaned = key.strip()
                if cleaned != key:
                    issues.append(
                        f"❌ {name}_api_key: tiene espacios en blanco al inicio/final "
                        f"(len={len(key)}, stripped={len(cleaned)})"
                    )
                if expected_prefix and not cleaned.startswith(expected_prefix):
                    issues.append(
                        f"⚠️ {name}_api_key: no empieza con '{expected_prefix}' "
                        f"(empieza con '{cleaned[:6]}...')"
                    )
                if "\n" in key or "\r" in key:
                    issues.append(f"❌ {name}_api_key: contiene saltos de línea")
                logger.info(f"🔑 {name}_api_key: {_mask_key(cleaned)}")

        return issues

    def log_startup_config(self) -> None:
        """Loguea la configuración de startup con validación de keys."""
        issues = self.validate_api_keys()
        logger.info(
            f"LLM Routing: "
            f"chat={self.chat_provider}/{self.chat_model}, "
            f"rag={self.rag_provider}/{self.rag_model}, "
            f"fallback={self.fallback_provider}/{self.fallback_model}"
        )
        guardian_mode = (
            "LLM+heuristics" if self.guardian_llm_enabled else "heuristics-only"
        )
        logger.info(f"Guardian: enabled={self.guardian_enabled}, mode={guardian_mode}")
        if issues:
            for issue in issues:
                logger.error(f"API KEY ISSUE: {issue}")
        else:
            logger.info("All API keys validated successfully")


# Instancia única para ser importada en otros módulos
settings = Settings()
