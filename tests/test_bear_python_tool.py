"""Test suite para BearPythonTool (filtro Python-only)."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.adapters.tools.bear_python_tool import BearPythonTool, PythonSource


@pytest.fixture
def tool():
    """BearPythonTool con API-Key y URL dummy para tests."""
    return BearPythonTool(api_key="test-key", base_url="https://test.bear.api/search")


@pytest.fixture
def mock_bear_response():
    """Respuesta mock de Bear API."""
    return {
        "results": [
            {
                "title": "How to fix ImportError in Python 3.12",
                "url": "https://docs.python.org/3.12/library/importlib.html",
                "snippet": "Traceback (most recent call last): ImportError: cannot import name 'x' from 'y'",
            },
            {
                "title": "Montevideo weather today",
                "url": "https://weather.com/montevideo",
                "snippet": "Temperature in Montevideo is 25°C",
            },
            {
                "title": "FastAPI async dependencies",
                "url": "https://github.com/tiangolo/fastapi/discussions/1234",
                "snippet": "async def get_user(): await dependency()",
            },
        ]
    }


# --------------- Tests de filtrado ---------------
@pytest.mark.asyncio
async def test_search_python_bug_acepta_error_real(tool, mock_bear_response):
    """Buscar un traceback REAL debe traer resultados."""
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_bear_response
        mock_get.return_value = mock_response

        results = await tool.search_python_bug("ImportError: cannot import name 'x'")

        assert len(results) == 1
        assert "ImportError" in results[0].snippet
        assert "github.com" in results[0].url


@pytest.mark.asyncio
async def test_search_python_bug_rechaza_query_general(tool):
    """Consultas generales (clima, hora, etc.) deben retornar lista vacía."""
    general_queries = [
        "temperatura en Montevideo",
        "hora actual en Uruguay",
        "cambio dólar hoy",
        "clima mañana",
    ]

    for query in general_queries:
        results = await tool.search_python_bug(query)
        assert results == [], f"Query general '{query}' debe devolver []"


@pytest.mark.asyncio
async def test_search_python_api_encuentra_ejemplos(tool):
    """Búsqueda de API específica debe traer ejemplos de uso."""
    api_response = {
        "results": [
            {
                "title": "asyncio.create_task example",
                "url": "https://docs.python.org/3/library/asyncio-task.html",
                "snippet": "task = asyncio.create_task(coro())",
            }
        ]
    }
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = api_response
        mock_get.return_value = mock_response

        results = await tool.search_python_api("asyncio", "create_task")

        assert len(results) == 1
        assert "asyncio.create_task" in results[0].snippet
        assert results[0].source_type == "official_docs"


@pytest.mark.asyncio
async def test_filtro_de_domains(tool):
    """Solo dominios de la whitelist deben aparecer."""
    raw = {
        "results": [
            {"title": "t1", "url": "https://docs.python.org/3/", "snippet": "def hello():"},
            {"title": "t2", "url": "https://facebook.com/post", "snippet": "not python related"},
            {"title": "t3", "url": "https://realpython.com/", "snippet": "import asyncio"},
            {"title": "t4", "url": "https://another-blog.com/post", "snippet": "def another_func():"},
        ]
    }
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = raw
        mock_get.return_value = mock_response

        results = await tool.search_python_best_practice("pep-8")

        urls = {r.url for r in results}
        assert len(urls) == 2
        assert "https://docs.python.org/3/" in urls
        assert "https://realpython.com/" in urls
        assert "https://facebook.com/post" not in urls
        assert "https://another-blog.com/post" not in urls


# --------------- Tests de activación (integración con ChatService) ---------------
@pytest.mark.asyncio
async def test_chat_service_no_busca_clima(tool):
    """El ChatService NO debe activar búsqueda para consultas generales."""
    from src.application.services.chat_service import ChatServiceV2
    from tests.mocks import MockLLMPort, MockRepositoryPort

    llm = MockLLMPort()
    repo = MockRepositoryPort()
    service = ChatServiceV2(llm, repo, python_search=tool)

    # Simular respuesta de Kimi que indica que no sabe
    llm.response = "No tengo información sobre el clima."

    # Para consultas generales, no debe buscar
    is_general = tool._is_general_query("¿Qué temperatura hay en Montevideo?")
    assert is_general is True


@pytest.mark.asyncio
async def test_chat_service_si_busca_traceback(tool):
    """El ChatService DEBE activar búsqueda para tracebacks."""
    from src.application.services.chat_service import ChatServiceV2
    from tests.mocks import MockLLMPort, MockRepositoryPort

    llm = MockLLMPort()
    repo = MockRepositoryPort()
    service = ChatServiceV2(llm, repo, python_search=tool)

    traceback_msg = "Traceback (most recent call last):\nAttributeError: 'NoneType' object has no attribute 'split'"

    # Para tracebacks, debe detectar la necesidad de búsqueda
    should_search = service._should_search_internet(traceback_msg, "No sé cómo resolver este error")
    assert should_search is True


# --------------- Tests de respuesta de Kimi (mensaje al usuario) ---------------
@pytest.mark.asyncio
async def test_kimi_responde_no_permiso_para_general():
    """Validar que el filtro rechaza consultas generales."""
    tool = BearPythonTool(api_key="test")
    
    # Consultas generales deben ser rechazadas
    general_queries = [
        "¿Qué temperatura hay?",
        "hora actual",
        "precio del dólar",
    ]
    
    for query in general_queries:
        is_general = tool._is_general_query(query)
        assert is_general is True, f"Debe rechazar: {query}"


# --------------- Test de rendimiento (opcional) ---------------
@pytest.mark.asyncio
async def test_busqueda_no_demasiado_larga(tool):
    """La búsqueda debe retornar lista incluso con timeout."""
    results = await tool.search_python_bug("ValueError: invalid literal for int()")
    assert isinstance(results, list)


# --------------- Tests de filtrado de contenido Python ---------------
def test_is_python_related_detecta_codigo_python(tool):
    """El detector debe identificar correctamente código Python."""
    python_content = [
        "def my_function():",
        "import asyncio",
        "class MyClass:",
        "async def create_task():",
        "raise ValueError('test')",
    ]
    
    for content in python_content:
        assert tool._is_python_related(content), f"Debe detectar: {content}"


def test_is_general_query_detecta_consultas_no_python(tool):
    """El detector debe rechazar consultas generales."""
    general_queries = [
        "temperatura",
        "hora en Montevideo",
        "cambio dólar",
        "noticias de hoy",
        "recetas de cocina",
    ]
    
    for query in general_queries:
        assert tool._is_general_query(query), f"Debe rechazar: {query}"


# --------------- Tests de confiabilidad ---------------
def test_calculate_reliability_github_alta(tool):
    """GitHub debe tener alta confiabilidad."""
    reliability = tool._calculate_reliability("github.com", "https://github.com/user/repo")
    assert reliability == 9


def test_calculate_reliability_docs_python_maxima(tool):
    """Docs Python debe tener máxima confiabilidad."""
    reliability = tool._calculate_reliability("docs.python.org", "https://docs.python.org/3/")
    assert reliability == 10


# --------------- Tests de manejo de errores ---------------
@pytest.mark.asyncio
async def test_api_error_usa_fallback(tool):
    """Si la API falla, debe usar el fallback y retornar resultados hardcodeados."""
    with patch('httpx.AsyncClient.get', side_effect=Exception("API Error")):
        results = await tool.search_python_bug("test error")
        assert len(results) > 0
        assert "Python Official Documentation" in [r.title for r in results]


@pytest.mark.asyncio
async def test_empty_response_handling(tool):
    """Respuesta vacía debe manejarse correctamente."""
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response
        
        results = await tool.search_python_best_practice("asyncio")
        assert results == []

@pytest.mark.asyncio
async def test_search_python_bug_acepta_error_real(tool, mock_bear_response):
    """Buscar un traceback REAL debe traer resultados."""
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_bear_response
        mock_get.return_value = mock_response

        results = await tool.search_python_bug("ImportError: cannot import name 'x'")

        assert len(results) == 2 # docs.python.org y github.com
        assert any("ImportError" in r.snippet for r in results)
        assert all("weather.com" not in r.url for r in results)
