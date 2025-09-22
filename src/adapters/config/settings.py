"""
Módulo de configuración centralizado para la aplicación.

Utiliza pydantic-settings para cargar y validar la configuración desde
variables de entorno y/o un archivo .env.
"""

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


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

    # --- API Keys y Secretos ---
    groq_api_key: str = Field(..., description="API key para Groq.")
    gemini_api_key: str | None = Field(None, description="API key para Gemini (Google AI Studio)")
    
    # --- Modelo LLM ---
    groq_model_name: str = Field(
        "moonshotai/kimi-k2-instruct",
        description="Nombre del modelo de Groq a utilizar.",
    )
    gemini_model_name: str = Field(
        "gemini-2.5-flash",
        description="Nombre del modelo de Gemini a utilizar para fallback o PDFs.",
    )
    llm_provider_preference: str = Field(
        "gemini_for_pdf_kimi_for_chat",
        description="Estrategia de proveedor: kimi_first_gemini_fallback | gemini_for_pdf_kimi_for_chat",
    )
    temperature: float = Field(
        0.3, description="Temperatura para la generación del modelo (creatividad)."
    )
    max_tokens: int = Field(
        4096, description="Máximo de tokens a generar en la respuesta."
    )

    # --- Base de Datos ---
    database_url: str = Field(
        "sqlite:///./data/chat_history.db",
        description="URL de conexión a la base de datos, apuntando al volumen de Docker.",
    )

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


# Instancia única para ser importada en otros módulos
settings = Settings()
