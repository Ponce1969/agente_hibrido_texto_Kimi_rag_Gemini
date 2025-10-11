"""
Configuración compartida de pytest para todos los tests.
Fixtures reutilizables y configuración de entorno.
"""
import pytest
import os
from pathlib import Path
from typing import Generator
import httpx
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

# Configurar variables de entorno para tests
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DATABASE_URL_PG"] = "postgresql://test:test@localhost:5432/test_db"


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Engine de SQLite en memoria para tests.
    Se crea una vez por sesión de tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Sesión de base de datos para cada test.
    Se hace rollback después de cada test.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def async_client() -> Generator[httpx.AsyncClient, None, None]:
    """Cliente HTTP asíncrono para tests de API."""
    client = httpx.AsyncClient(timeout=30.0)
    yield client
    # Cleanup se hace automáticamente


@pytest.fixture
def sample_pdf_path() -> Path:
    """Path a un PDF de prueba."""
    # Usar el PDF real que ya está indexado
    pdf_path = Path("data/uploads/06_Part_II_Functions_as_Objects.pdf")
    if pdf_path.exists():
        return pdf_path
    # Fallback: crear un PDF dummy si no existe
    return Path(__file__).parent / "fixtures" / "sample.pdf"


@pytest.fixture
def sample_user_message() -> str:
    """Mensaje de usuario de prueba."""
    return "¿Qué son las funciones de primera clase en Python?"


@pytest.fixture
def sample_agent_mode() -> str:
    """Modo de agente de prueba."""
    return "Arquitecto Python Senior"


@pytest.fixture
def mock_groq_response() -> dict:
    """Respuesta mock de Groq API."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Las funciones de primera clase son aquellas que pueden ser tratadas como cualquier otro valor..."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 200,
            "total_tokens": 350
        }
    }


@pytest.fixture
def mock_gemini_response() -> dict:
    """Respuesta mock de Gemini API."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Según el PDF, las funciones de primera clase son..."
                        }
                    ]
                },
                "finishReason": "STOP"
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 9766,
            "candidatesTokenCount": 500,
            "totalTokenCount": 10266
        }
    }


@pytest.fixture
def sample_embedding() -> list[float]:
    """Embedding de prueba (384 dimensiones)."""
    import random
    random.seed(42)
    return [random.random() for _ in range(384)]


@pytest.fixture
def sample_chunks() -> list[dict]:
    """Chunks de prueba para RAG."""
    return [
        {
            "id": 1,
            "file_id": 1,
            "section_id": 1,
            "chunk_index": 0,
            "content": "Las funciones en Python son objetos de primera clase...",
            "distance": 0.15
        },
        {
            "id": 2,
            "file_id": 1,
            "section_id": 1,
            "chunk_index": 1,
            "content": "Esto significa que las funciones pueden ser asignadas a variables...",
            "distance": 0.23
        },
        {
            "id": 3,
            "file_id": 1,
            "section_id": 1,
            "chunk_index": 2,
            "content": "También pueden ser pasadas como argumentos a otras funciones...",
            "distance": 0.31
        }
    ]


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Resetea el entorno antes de cada test.
    Se ejecuta automáticamente.
    """
    # Limpiar variables de entorno que puedan afectar tests
    env_vars_to_clear = ["GROQ_API_KEY", "GEMINI_API_KEY"]
    original_values = {}
    
    for var in env_vars_to_clear:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restaurar valores originales
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value


# Markers personalizados
def pytest_configure(config):
    """Configuración de pytest con markers personalizados."""
    config.addinivalue_line(
        "markers", "unit: marca test como unitario (rápido, sin dependencias externas)"
    )
    config.addinivalue_line(
        "markers", "integration: marca test como de integración (requiere servicios externos)"
    )
    config.addinivalue_line(
        "markers", "slow: marca test como lento (> 1 segundo)"
    )
    config.addinivalue_line(
        "markers", "rag: marca test relacionado con sistema RAG"
    )
    config.addinivalue_line(
        "markers", "api: marca test de endpoints API"
    )
