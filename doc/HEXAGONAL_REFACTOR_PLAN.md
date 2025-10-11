# 🔧 Plan de Refactorización Hexagonal

**Fecha:** 2 de Octubre 2025  
**Objetivo:** Corregir 15 violaciones críticas de arquitectura hexagonal  
**Estado:** 📋 **PLANIFICADO**

---

## 📊 Análisis Actual

### **Violaciones Detectadas**

```
Total: 15 violaciones críticas
├─ application/services/chat_service.py        → 10 violaciones
└─ application/services/embeddings_service.py  → 5 violaciones

Problema: Application importa directamente de Adapters
```

### **Dependencias Actuales (INCORRECTAS)**

```
❌ application → adapters  (VIOLACIÓN)
✅ adapters → application  (CORRECTO)
✅ domain → ninguna        (CORRECTO)
```

---

## 🎯 Objetivo Final

### **Dependencias Correctas**

```
✅ domain → ninguna
✅ application → domain
✅ adapters → application + domain
```

### **Arquitectura Objetivo**

```
┌─────────────────────────────────────────────────┐
│                   ADAPTERS                      │
│  ┌─────────────────────────────────────────┐   │
│  │           APPLICATION                   │   │
│  │  ┌──────────────────────────────────┐   │   │
│  │  │          DOMAIN                  │   │   │
│  │  │                                  │   │   │
│  │  │  Puertos (Interfaces):          │   │   │
│  │  │  - LLMPort                       │   │   │
│  │  │  - RepositoryPort                │   │   │
│  │  │  - EmbeddingsPort                │   │   │
│  │  │                                  │   │   │
│  │  │  Modelos:                        │   │   │
│  │  │  - ChatMessage                   │   │   │
│  │  │  - ChatSession                   │   │   │
│  │  │  - FileDocument                  │   │   │
│  │  │                                  │   │   │
│  │  └──────────────────────────────────┘   │   │
│  │                                          │   │
│  │  Servicios (usan puertos):              │   │
│  │  - ChatService                           │   │
│  │  - EmbeddingsService                     │   │
│  │                                          │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Implementaciones (de puertos):                │
│  - GroqAdapter (LLMPort)                       │
│  - GeminiAdapter (LLMPort)                     │
│  - SQLChatRepository (RepositoryPort)          │
│  - PostgresEmbeddingsRepo (EmbeddingsPort)     │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 📋 Plan de Implementación

### **Fase 1: Crear Puertos en Domain (2 horas)**

#### **1.1 Crear estructura de puertos**

```bash
mkdir -p src/domain/ports
touch src/domain/ports/__init__.py
touch src/domain/ports/llm_port.py
touch src/domain/ports/repository_port.py
touch src/domain/ports/embeddings_port.py
```

#### **1.2 Definir LLMPort**

```python
# src/domain/ports/llm_port.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.chat_models import ChatMessage

class LLMPort(ABC):
    """Puerto para clientes de modelos de lenguaje."""
    
    @abstractmethod
    async def get_chat_completion(
        self,
        system_prompt: str,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Obtiene una respuesta del modelo de lenguaje."""
        pass
```

#### **1.3 Definir RepositoryPort**

```python
# src/domain/ports/repository_port.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.chat_models import ChatSession, ChatMessage

class ChatRepositoryPort(ABC):
    """Puerto para repositorio de chat."""
    
    @abstractmethod
    def create_session(self, title: str) -> ChatSession:
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        pass
    
    @abstractmethod
    def add_message(self, message: ChatMessage) -> None:
        pass
    
    @abstractmethod
    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        pass
```

#### **1.4 Definir EmbeddingsPort**

```python
# src/domain/ports/embeddings_port.py
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

class EmbeddingsPort(ABC):
    """Puerto para servicio de embeddings."""
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> np.ndarray:
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        query_embedding: np.ndarray,
        file_id: str,
        top_k: int = 5
    ) -> List[dict]:
        pass
```

---

### **Fase 2: Mover Modelos a Domain (1 hora)**

#### **2.1 Consolidar modelos en domain**

```python
# src/domain/models/chat_models.py (ya existe, mejorar)
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class ChatMessage:
    id: Optional[int]
    session_id: str
    role: MessageRole
    content: str
    message_index: int
    created_at: Optional[datetime] = None

@dataclass
class ChatSession:
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
```

#### **2.2 Crear modelos de archivo**

```python
# src/domain/models/file_models.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class FileStatus(Enum):
    PENDING = "pending"
    INDEXED = "indexed"
    ERROR = "error"

@dataclass
class FileDocument:
    id: Optional[int]
    filename: str
    file_path: str
    status: FileStatus
    total_chunks: int = 0
    created_at: Optional[datetime] = None
```

---

### **Fase 3: Refactorizar Application (3 horas)**

#### **3.1 Refactorizar ChatService**

```python
# src/application/services/chat_service.py
from typing import Optional, List
from src.domain.ports.llm_port import LLMPort
from src.domain.ports.repository_port import ChatRepositoryPort
from src.domain.ports.embeddings_port import EmbeddingsPort
from src.domain.models.chat_models import ChatMessage, MessageRole

class ChatService:
    """Servicio de aplicación para chat (sin dependencias de adapters)."""
    
    def __init__(
        self,
        llm_client: LLMPort,
        repository: ChatRepositoryPort,
        embeddings_service: Optional[EmbeddingsPort] = None
    ):
        self.llm = llm_client
        self.repo = repository
        self.embeddings = embeddings_service
    
    async def handle_message(
        self,
        session_id: str,
        user_message: str,
        agent_mode: str,
        file_id: Optional[str] = None
    ) -> str:
        """Maneja un mensaje del usuario."""
        
        # 1. Guardar mensaje del usuario
        user_msg = ChatMessage(
            id=None,
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
            message_index=0
        )
        self.repo.add_message(user_msg)
        
        # 2. Obtener historial
        history = self.repo.get_session_messages(session_id)
        
        # 3. Obtener contexto de PDF si existe
        context = None
        if file_id and self.embeddings:
            # Generar embedding de la pregunta
            query_emb = await self.embeddings.generate_embedding(user_message)
            # Buscar chunks similares
            similar = await self.embeddings.search_similar(query_emb, file_id)
            context = "\n".join([s["text"] for s in similar])
        
        # 4. Construir prompt
        system_prompt = self._get_system_prompt(agent_mode)
        if context:
            system_prompt += f"\n\nContexto del PDF:\n{context}"
        
        # 5. Obtener respuesta del LLM
        response = await self.llm.get_chat_completion(
            system_prompt=system_prompt,
            messages=history
        )
        
        # 6. Guardar respuesta
        assistant_msg = ChatMessage(
            id=None,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response,
            message_index=0
        )
        self.repo.add_message(assistant_msg)
        
        return response
    
    def _get_system_prompt(self, agent_mode: str) -> str:
        """Obtiene el prompt del sistema según el modo."""
        # Lógica de dominio pura
        prompts = {
            "architect": "Eres un arquitecto de software...",
            "code_generator": "Eres un ingeniero de código...",
            # etc.
        }
        return prompts.get(agent_mode, "Eres un asistente útil.")
```

#### **3.2 Refactorizar EmbeddingsService**

```python
# src/application/services/embeddings_service.py
from typing import List
import numpy as np
from src.domain.ports.embeddings_port import EmbeddingsPort

class EmbeddingsService:
    """Servicio de aplicación para embeddings."""
    
    def __init__(self, embeddings_port: EmbeddingsPort):
        self.embeddings = embeddings_port
    
    async def index_document(
        self,
        file_id: str,
        chunks: List[str]
    ) -> int:
        """Indexa un documento en chunks."""
        indexed = 0
        
        for chunk in chunks:
            embedding = await self.embeddings.generate_embedding(chunk)
            await self.embeddings.store_embedding(file_id, chunk, embedding)
            indexed += 1
        
        return indexed
    
    async def search_context(
        self,
        query: str,
        file_id: str,
        top_k: int = 5
    ) -> List[str]:
        """Busca contexto relevante para una query."""
        query_emb = await self.embeddings.generate_embedding(query)
        results = await self.embeddings.search_similar(query_emb, file_id, top_k)
        return [r["text"] for r in results]
```

---

### **Fase 4: Crear Adaptadores (2 horas)**

#### **4.1 Adaptar GroqClient**

```python
# src/adapters/agents/groq_adapter.py
from typing import List, Optional
import httpx
from src.domain.ports.llm_port import LLMPort
from src.domain.models.chat_models import ChatMessage
from src.adapters.config.settings import settings

class GroqAdapter(LLMPort):
    """Adaptador de Groq que implementa LLMPort."""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    async def get_chat_completion(
        self,
        system_prompt: str,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Implementación específica de Groq."""
        
        api_messages = [
            {"role": "system", "content": system_prompt},
            *[
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
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
                "temperature": temperature or settings.temperature,
                "max_tokens": max_tokens or settings.max_tokens,
            }
        )
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
```

#### **4.2 Adaptar Repository**

```python
# src/adapters/db/chat_repository_adapter.py
from typing import List, Optional
from sqlmodel import Session, select
from src.domain.ports.repository_port import ChatRepositoryPort
from src.domain.models.chat_models import ChatSession, ChatMessage
from src.adapters.db.chat import ChatSessionDB, ChatMessageDB  # Modelos SQLModel

class SQLChatRepositoryAdapter(ChatRepositoryPort):
    """Adaptador de repositorio SQL que implementa ChatRepositoryPort."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_session(self, title: str) -> ChatSession:
        """Crea una sesión en la base de datos."""
        db_session = ChatSessionDB(title=title)
        self.session.add(db_session)
        self.session.commit()
        
        # Convertir de modelo DB a modelo de dominio
        return ChatSession(
            id=db_session.id,
            title=db_session.title,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Obtiene una sesión."""
        db_session = self.session.get(ChatSessionDB, session_id)
        if not db_session:
            return None
        
        return ChatSession(
            id=db_session.id,
            title=db_session.title,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )
    
    def add_message(self, message: ChatMessage) -> None:
        """Agrega un mensaje."""
        db_message = ChatMessageDB(
            session_id=message.session_id,
            role=message.role.value,
            content=message.content,
            message_index=message.message_index
        )
        self.session.add(db_message)
        self.session.commit()
    
    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """Obtiene mensajes de una sesión."""
        statement = select(ChatMessageDB).where(
            ChatMessageDB.session_id == session_id
        ).order_by(ChatMessageDB.message_index)
        
        db_messages = self.session.exec(statement).all()
        
        return [
            ChatMessage(
                id=msg.id,
                session_id=msg.session_id,
                role=MessageRole(msg.role),
                content=msg.content,
                message_index=msg.message_index,
                created_at=msg.created_at
            )
            for msg in db_messages
        ]
```

---

### **Fase 5: Actualizar Endpoints (1 hora)**

#### **5.1 Inyección de dependencias en API**

```python
# src/adapters/api/endpoints/chat.py
from fastapi import APIRouter, Depends
import httpx
from sqlmodel import Session

from src.application.services.chat_service import ChatService
from src.adapters.agents.groq_adapter import GroqAdapter
from src.adapters.agents.gemini_adapter import GeminiAdapter
from src.adapters.db.chat_repository_adapter import SQLChatRepositoryAdapter
from src.adapters.db.database import get_session

router = APIRouter()

def get_chat_service(session: Session = Depends(get_session)) -> ChatService:
    """Factory para crear ChatService con dependencias inyectadas."""
    
    # Crear adaptadores
    http_client = httpx.AsyncClient()
    llm_adapter = GroqAdapter(http_client)
    repo_adapter = SQLChatRepositoryAdapter(session)
    
    # Crear servicio con puertos
    return ChatService(
        llm_client=llm_adapter,
        repository=repo_adapter
    )

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """Endpoint de chat con inyección de dependencias."""
    
    response = await service.handle_message(
        session_id=request.session_id,
        user_message=request.message,
        agent_mode=request.agent_mode
    )
    
    return {"response": response}
```

---

### **Fase 6: Tests y Validación (1 hora)**

#### **6.1 Tests con mocks de puertos**

```python
# tests/test_chat_service_hexagonal.py
import pytest
from unittest.mock import AsyncMock
from src.application.services.chat_service import ChatService
from src.domain.models.chat_models import ChatMessage, MessageRole

class MockLLMPort:
    """Mock del puerto LLM."""
    
    async def get_chat_completion(self, system_prompt, messages, **kwargs):
        return "Respuesta mock"

class MockRepositoryPort:
    """Mock del puerto Repository."""
    
    def __init__(self):
        self.messages = []
    
    def add_message(self, message):
        self.messages.append(message)
    
    def get_session_messages(self, session_id):
        return self.messages

@pytest.mark.asyncio
async def test_chat_service_with_mocks():
    """Test del servicio usando mocks de puertos."""
    
    # Arrange
    mock_llm = MockLLMPort()
    mock_repo = MockRepositoryPort()
    service = ChatService(mock_llm, mock_repo)
    
    # Act
    response = await service.handle_message(
        session_id="test",
        user_message="Hola",
        agent_mode="architect"
    )
    
    # Assert
    assert response == "Respuesta mock"
    assert len(mock_repo.messages) == 2  # user + assistant
```

---

## 📊 Checklist de Implementación

### **Fase 1: Puertos**
- [ ] Crear `domain/ports/__init__.py`
- [ ] Crear `domain/ports/llm_port.py`
- [ ] Crear `domain/ports/repository_port.py`
- [ ] Crear `domain/ports/embeddings_port.py`

### **Fase 2: Modelos**
- [ ] Mejorar `domain/models/chat_models.py`
- [ ] Crear `domain/models/file_models.py`
- [ ] Mover enums a domain

### **Fase 3: Application**
- [ ] Refactorizar `application/services/chat_service.py`
- [ ] Refactorizar `application/services/embeddings_service.py`
- [ ] Eliminar imports de adapters

### **Fase 4: Adapters**
- [ ] Crear `adapters/agents/groq_adapter.py`
- [ ] Crear `adapters/agents/gemini_adapter.py`
- [ ] Crear `adapters/db/chat_repository_adapter.py`
- [ ] Crear `adapters/db/embeddings_adapter.py`

### **Fase 5: API**
- [ ] Actualizar endpoints con inyección de dependencias
- [ ] Crear factories de servicios
- [ ] Actualizar `main.py`

### **Fase 6: Tests**
- [ ] Crear tests con mocks de puertos
- [ ] Validar arquitectura con script
- [ ] Ejecutar suite completa

---

## 🎯 Resultado Esperado

### **Antes (15 violaciones)**

```
❌ application → adapters
```

### **Después (0 violaciones)**

```
✅ domain → ninguna
✅ application → domain
✅ adapters → application + domain
```

---

## ⏱️ Estimación Total

```
Fase 1: Puertos           → 2 horas
Fase 2: Modelos           → 1 hora
Fase 3: Application       → 3 horas
Fase 4: Adapters          → 2 horas
Fase 5: API               → 1 hora
Fase 6: Tests             → 1 hora

TOTAL: 10 horas
```

---

## 📝 Próximos Pasos

1. **Revisar y aprobar** este plan
2. **Crear branch** `feature/hexagonal-architecture`
3. **Implementar** por fases
4. **Validar** con `scripts/analyze_architecture.py`
5. **Merge** cuando 0 violaciones

---

*Plan creado: 2 de Octubre 2025*  
*Estimación: 10 horas de trabajo*
