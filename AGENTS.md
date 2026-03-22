# AGENTS.md - Development Guidelines for AI Coding Agents

> This file provides guidelines and commands for AI agents working on this codebase.
> Last updated: 2026-03-21

---

## Project Overview

**Name:** agente_hibrido_texto_Kimi_rag_Gemini  
**Type:** Python 3.12+ FastAPI/Streamlit application with RAG, hexagonal architecture  
**Description:** Multi-agent AI assistant with RAG, Brave Search, and security guardian

---

## 1. Build, Lint, and Test Commands

### Prerequisites
```bash
# Install dependencies using uv (recommended) or pip
uv sync --dev
# or
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_chat_service.py

# Run a single test function
pytest tests/test_chat_service.py::TestChatServiceBasic::test_chat_without_rag -v

# Run tests by marker
pytest -m unit          # Unit tests only (fast, no external deps)
pytest -m integration   # Integration tests (requires external services)
pytest -m rag           # RAG-related tests
pytest -m api           # API endpoint tests
pytest -m slow          # Slow tests (>1 second)

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality Tools

```bash
# Run ruff linter (all checks)
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Format code with ruff (preferred) or black
ruff format .
# or
black src/ tests/

# Run mypy type checker
mypy src/

# Run all quality checks (lint + type check)
ruff check . && mypy src/
```

### Application Commands

```bash
# Development server (FastAPI)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Streamlit frontend
streamlit run src/adapters/streamlit/app.py

# Production server with gunicorn
gunicorn -c gunicorn.conf.py src.main:app

# Docker deployment
docker compose up --build
```

---

## 2. Code Style Guidelines

### 2.1 Python Version and Imports

- **Python version:** 3.12+ required
- **Import order** (enforced by ruff `I` rules):
  1. Standard library (`from __future__ import annotations`, `typing`, `datetime`)
  2. Third-party packages (fastapi, sqlmodel, pydantic, etc.)
  3. Local imports (`from src...`)

```python
from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Session, select

from src.adapters.db.repository import ChatRepository
from src.domain.models import ChatSession

if TYPE_CHECKING:
    from src.domain.ports import LLMPort
```

### 2.2 Type Annotations

- **Always use type hints** for function signatures
- **Return types:** Required for all public methods
- **Use `|` instead of `Optional`** (Python 3.10+ union syntax)
- **Use `TYPE_CHECKING`** block for imports that cause circular dependencies

```python
# Good
def get_session(session_id: str) -> ChatSession | None:
    ...

async def handle_message(
    self,
    session_id: str,
    user_message: str,
    *,
    agent_mode: str = "architect",
    file_id: int | None = None,
) -> str:
    ...

# Bad - missing return type
def get_session(session_id):
    ...
```

### 2.3 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | lowercase_snake_case | `chat_service.py` |
| Classes | PascalCase | `ChatService`, `LLMPort` |
| Functions | snake_case | `get_session`, `create_message` |
| Constants | UPPER_SNAKE_CASE | `MAX_TOKENS`, `DEFAULT_TIMEOUT` |
| Type aliases | PascalCase | `TokenCount`, `EmbeddingVector` |
| Private methods | _leading_underscore | `_get_llm_response` |
| Private attributes | _leading_underscore | `self._cache` |

### 2.4 Code Formatting

- **Line length:** 88 characters (ruff/black default)
- **Indentation:** 4 spaces (no tabs)
- **Docstrings:** Use triple double quotes, Google-style for modules/classes/methods
- **No trailing whitespace**
- **Blank lines:** 2 between top-level definitions, 1 between methods

```python
class ChatService:
    """Servicio de chat siguiendo arquitectura hexagonal."""

    def __init__(self, llm_client: LLMPort) -> None:
        """Initialize the service."""
        self._llm = llm_client

    def get_session(self, session_id: str) -> ChatSession | None:
        """Obtiene una sesión por su ID."""
        return self._repo.get_session(session_id)
```

### 2.5 Error Handling

- **Domain exceptions:** Use custom exceptions from `src.domain.exceptions`
- **Never swallow exceptions silently:** Always log or re-raise
- **Use specific exception types:** Catch specific exceptions, not bare `Exception`
- **Include context in exceptions:** Pass relevant data to exception constructors

```python
# Good
from src.domain.exceptions import ChatSessionNotFoundError

def get_session(self, session_id: str) -> ChatSession | None:
    session = self._repo.get_session(session_id)
    if not session:
        raise ChatSessionNotFoundError(session_id)
    return session

# Good - handle with context
try:
    await self._llm.get_chat_completion(...)
except Exception as e:
    logger.error(f"LLM error: {e}")
    raise AIProviderError(provider="groq", reason=str(e)) from e

# Bad - silent swallow
try:
    do_something()
except:
    pass
```

### 2.6 Logging

- **Use `logger = logging.getLogger(__name__)`** at module level
- **Log levels:** DEBUG for development, INFO for operations, ERROR for failures
- **Include context:** Use f-strings with relevant data

```python
logger = logging.getLogger(__name__)

logger.debug(f"Processing message: {message_id}")
logger.info(f"Session created: {session_id}")
logger.warning(f"Rate limit approaching: {current}/{max}")
logger.error(f"LLM request failed: {error}", exc_info=True)
```

### 2.7 Async/Await

- **Use async for I/O operations:** Database, HTTP calls, file operations
- **Never mix sync and async** without proper wrapping
- **Use `asyncio.to_thread()`** for blocking sync operations in async context

```python
# Good
async def fetch_data(self, url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Wrap sync code in async context
async def list_sessions(self) -> list[ChatSession]:
    import asyncio
    def _query():
        return self.session.exec(select(ChatSession)).all()
    return await asyncio.to_thread(_query)
```

---

## 3. Architecture Guidelines (Hexagonal/Ports & Adapters)

### Directory Structure

```
src/
├── domain/           # Pure business logic, no external dependencies
│   ├── models/       # Domain entities and DTOs
│   ├── ports/        # Interface definitions (ABC)
│   ├── services/     # Domain services
│   └── exceptions/   # Domain exceptions
├── application/      # Use cases, orchestration
│   └── services/     # Application services
└── adapters/         # Implementations
    ├── api/          # FastAPI endpoints
    ├── db/           # Database repositories
    ├── agents/       # LLM clients (Groq, Gemini)
    └── tools/        # External tools (Brave, Guardian)
```

### Ports (Interfaces)

Define ports as abstract base classes in `src/domain/ports/`:

```python
class LLMPort(ABC):
    @abstractmethod
    async def get_chat_completion(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        max_tokens: int | None = None,
    ) -> tuple[str, int]:
        ...
```

### Dependency Injection

- **Inject ports in constructors** for flexibility and testability
- **Use keyword-only arguments** after `self` to make dependencies explicit

```python
class ChatService:
    def __init__(
        self,
        llm_client: LLMPort,
        repository: ChatRepositoryPort,
        *,
        fallback_llm: LLMPort | None = None,
    ) -> None:
        self._llm = llm_client
        self._repo = repository
        self._fallback_llm = fallback_llm
```

---

## 4. Testing Guidelines

### Test Structure

```python
@pytest.mark.unit
class TestChatServiceBasic:
    """Tests básicos del servicio de chat."""

    @pytest.mark.asyncio
    async def test_chat_without_rag(self):
        """Verifica que el chat funcione sin RAG."""
        mock_llm = AsyncMock()
        mock_llm.get_chat_completion.return_value = ("Respuesta", 50)

        mock_repo = AsyncMock()
        mock_session = ChatSession(user_id="test")
        mock_repo.get_session.return_value = mock_session

        service = ChatServiceV2(llm_client=mock_llm, repository=mock_repo)

        response = await service.handle_message(session_id="1", user_message="Hola")

        assert response == "Respuesta"
        mock_llm.get_chat_completion.assert_called_once()
```

### Test Conventions

- **Use markers:** `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.asyncio`
- **One assertion concept per test:** Don't cram multiple assertions
- **Use descriptive names:** `test_creates_session_with_default_title`
- **Mock external dependencies:** LLM clients, database connections

### Fixtures

Use `tests/conftest.py` for shared fixtures:
- `db_session` - Database session for tests
- `sample_pdf_path` - Path to test PDF
- `mock_groq_response` - Mock LLM responses
- `sample_chunks` - Mock RAG chunks

---

## 5. Git Commit Convention

Use conventional commits:

```bash
feat: add adaptive RAG search
fix: handle session not found error
refactor: extract embeddings service
docs: update deployment guide
test: add tests for chat service
chore: update dependencies
```

---

## 6. Configuration

- **Environment variables:** Use `.env` file (see `.env.example`)
- **Settings:** Use `pydantic-settings` in `src/adapters/config/settings.py`
- **Never hardcode secrets:** Always use environment variables

---

## 7. Important File Locations

| Purpose | Path |
|---------|------|
| Main app | `src/main.py` |
| API endpoints | `src/adapters/api/` |
| Settings | `src/adapters/config/settings.py` |
| Domain models | `src/domain/models/` |
| Domain ports | `src/domain/ports/` |
| Application services | `src/application/services/` |
| Tests | `tests/` |
| Pytest config | `pytest.ini` |
| Ruff config | `pyproject.toml` |
