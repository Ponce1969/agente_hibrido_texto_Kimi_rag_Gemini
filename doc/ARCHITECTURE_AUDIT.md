# 🔍 Auditoría de Arquitectura Hexagonal

**Fecha:** 2 de Octubre 2025  
**Estado:** 🔴 **VIOLACIONES DETECTADAS**

---

## 📋 Resumen Ejecutivo

Se ha realizado una auditoría completa de la arquitectura hexagonal del proyecto y se han detectado **violaciones críticas** en la separación de responsabilidades entre capas.

### **Problemas Encontrados**

🔴 **CRÍTICO:** Application layer importa directamente de Adapters  
🟡 **MODERADO:** Falta de interfaces/puertos bien definidos  
🟡 **MODERADO:** Servicios de aplicación con lógica de infraestructura  

---

## 🏗️ Arquitectura Hexagonal - Principios

### **Reglas Fundamentales**

```
┌─────────────────────────────────────────┐
│           ADAPTERS (Externos)           │
│  ┌─────────────────────────────────┐   │
│  │      APPLICATION (Casos de Uso) │   │
│  │  ┌──────────────────────────┐   │   │
│  │  │   DOMAIN (Lógica Negocio)│   │   │
│  │  │                          │   │   │
│  │  │  - Entidades             │   │   │
│  │  │  - Value Objects         │   │   │
│  │  │  - Interfaces/Puertos    │   │   │
│  │  │  - Reglas de negocio     │   │   │
│  │  │                          │   │   │
│  │  └──────────────────────────┘   │   │
│  │                                  │   │
│  │  - Orquesta dominio              │   │
│  │  - Define puertos                │   │
│  │  - NO conoce infraestructura     │   │
│  │                                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  - Implementa puertos                   │
│  - API, DB, Clientes externos           │
│  - Depende de Application/Domain        │
│                                         │
└─────────────────────────────────────────┘
```

### **Reglas de Dependencia**

1. ✅ **Domain** → NO depende de nadie
2. ✅ **Application** → Depende SOLO de Domain
3. ✅ **Adapters** → Depende de Application y Domain
4. ❌ **Application NO debe importar de Adapters**

---

## 🔴 Violaciones Detectadas

### **1. Application importa de Adapters (CRÍTICO)**

#### **Archivo: `src/application/services/chat_service.py`**

```python
# ❌ VIOLACIÓN: Application importando de Adapters
from src.adapters.db.repository import ChatRepository
from src.adapters.agents.groq_client import GroqClient
from src.adapters.agents.gemini_client import GeminiClient
from src.adapters.agents.prompts import AgentMode, get_system_prompt
from src.adapters.db.message import ChatMessageCreate, MessageRole
from src.adapters.db.chat import ChatSession, ChatSessionCreate
from src.adapters.db.file_models import FileUpload, FileSection
from src.adapters.config.settings import settings
from src.adapters.db.pg_engine import get_pg_engine
from src.adapters.db.embeddings_repository import EmbeddingsRepository
```

**Problema:** El servicio de aplicación conoce detalles de implementación (SQLModel, Groq, Gemini, etc.)

#### **Archivo: `src/application/services/embeddings_service.py`**

```python
# ❌ VIOLACIÓN: Application importando de Adapters
from src.adapters.db.embeddings_repository import EmbeddingsRepository, EMBEDDING_DIM
from src.adapters.config.settings import settings
from src.adapters.db.embeddings_models import EmbeddingChunk
from src.adapters.db.database import engine as sqlite_engine
from src.adapters.db.file_models import FileUpload, FileSection, FileStatus
```

**Problema:** Servicio de aplicación maneja directamente modelos de base de datos

---

## ✅ Elementos Correctos

### **1. Domain Layer (CORRECTO)**

```python
# ✅ Domain NO importa de adapters ni application
src/domain/
├── models/chat_models.py          # Entidades puras
├── repositories/chat_repository.py # Interfaces/Puertos
├── services/chat_domain_service.py # Lógica de dominio
└── exceptions/domain_exceptions.py # Excepciones de dominio
```

**Análisis:**
- ✅ Solo usa tipos de Python estándar
- ✅ Define interfaces (puertos)
- ✅ No conoce infraestructura
- ✅ Lógica de negocio pura

### **2. Adapters Layer (CORRECTO)**

```python
# ✅ Adapters implementa puertos del dominio
src/adapters/
├── db/domain_repository.py        # Implementa ChatRepositoryInterface
├── agents/groq_client.py          # Cliente externo
├── agents/gemini_client.py        # Cliente externo
├── api/endpoints/                 # Controladores HTTP
└── streamlit/                     # UI
```

---

## 🔧 Solución Propuesta

### **Estrategia de Refactorización**

#### **Paso 1: Mover Modelos a Domain**

```
ANTES:
src/adapters/db/message.py         # ❌ En adapters
src/adapters/db/chat.py            # ❌ En adapters

DESPUÉS:
src/domain/models/message.py       # ✅ En domain
src/domain/models/session.py       # ✅ En domain
```

#### **Paso 2: Crear Puertos (Interfaces) en Domain**

```python
# src/domain/ports/llm_port.py
from abc import ABC, abstractmethod
from typing import List
from ..models.message import Message

class LLMPort(ABC):
    """Puerto para clientes LLM (Groq, Gemini, etc.)"""
    
    @abstractmethod
    async def get_completion(
        self,
        system_prompt: str,
        messages: List[Message],
        **kwargs
    ) -> str:
        pass

# src/domain/ports/repository_port.py
class ChatRepositoryPort(ABC):
    """Puerto para repositorio de chat"""
    
    @abstractmethod
    def save_message(self, message: Message) -> None:
        pass
    
    @abstractmethod
    def get_session_messages(self, session_id: str) -> List[Message]:
        pass
```

#### **Paso 3: Application usa Puertos**

```python
# src/application/services/chat_service.py
from src.domain.ports.llm_port import LLMPort
from src.domain.ports.repository_port import ChatRepositoryPort
from src.domain.models.message import Message

class ChatService:
    def __init__(
        self,
        llm_client: LLMPort,           # ✅ Puerto, no implementación
        repository: ChatRepositoryPort  # ✅ Puerto, no implementación
    ):
        self.llm = llm_client
        self.repo = repository
    
    async def handle_message(self, user_input: str) -> str:
        # ✅ Usa puertos, no conoce implementación
        messages = self.repo.get_session_messages(session_id)
        response = await self.llm.get_completion(prompt, messages)
        return response
```

#### **Paso 4: Adapters implementa Puertos**

```python
# src/adapters/agents/groq_adapter.py
from src.domain.ports.llm_port import LLMPort
from src.domain.models.message import Message

class GroqAdapter(LLMPort):
    """Implementación del puerto LLM usando Groq"""
    
    async def get_completion(
        self,
        system_prompt: str,
        messages: List[Message],
        **kwargs
    ) -> str:
        # Implementación específica de Groq
        ...
```

#### **Paso 5: Inyección de Dependencias en API**

```python
# src/adapters/api/endpoints/chat.py
from src.application.services.chat_service import ChatService
from src.adapters.agents.groq_adapter import GroqAdapter
from src.adapters.db.chat_repository_impl import ChatRepositoryImpl

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # ✅ Inyección de dependencias
    llm = GroqAdapter(client)
    repo = ChatRepositoryImpl(session)
    service = ChatService(llm, repo)
    
    response = await service.handle_message(request.message)
    return {"response": response}
```

---

## 📊 Análisis de Impacto

### **Archivos a Refactorizar**

| Archivo | Tipo | Acción |
|---------|------|--------|
| `application/services/chat_service.py` | 🔴 Crítico | Refactorizar completamente |
| `application/services/embeddings_service.py` | 🔴 Crítico | Refactorizar completamente |
| `application/services/domain_chat_service.py` | 🟡 Revisar | Verificar dependencias |
| `domain/models/` | 🟢 Crear | Agregar modelos faltantes |
| `domain/ports/` | 🟢 Crear | Crear interfaces/puertos |
| `adapters/agents/` | 🟡 Adaptar | Implementar puertos |
| `adapters/db/` | 🟡 Adaptar | Implementar puertos |

### **Estimación de Esfuerzo**

```
Fase 1: Crear puertos en Domain          → 2 horas
Fase 2: Mover modelos a Domain            → 1 hora
Fase 3: Refactorizar Application          → 3 horas
Fase 4: Adaptar Adapters                  → 2 horas
Fase 5: Actualizar tests                  → 1 hora
Fase 6: Validación y documentación        → 1 hora

TOTAL: ~10 horas
```

---

## 🎯 Beneficios de la Refactorización

### **1. Testabilidad**

```python
# ANTES: Difícil de testear
def test_chat_service():
    # ❌ Necesita DB real, API de Groq, etc.
    service = ChatService()
    ...

# DESPUÉS: Fácil de testear
def test_chat_service():
    # ✅ Usa mocks de puertos
    mock_llm = MockLLMPort()
    mock_repo = MockRepositoryPort()
    service = ChatService(mock_llm, mock_repo)
    ...
```

### **2. Flexibilidad**

```python
# ✅ Cambiar de Groq a OpenAI sin tocar Application
llm = OpenAIAdapter()  # En vez de GroqAdapter
service = ChatService(llm, repo)
```

### **3. Mantenibilidad**

- ✅ Cambios en infraestructura no afectan lógica de negocio
- ✅ Lógica de negocio independiente de frameworks
- ✅ Fácil agregar nuevos adaptadores

---

## 📋 Plan de Acción

### **Prioridad Alta (Esta Semana)**

- [ ] Crear estructura de puertos en `domain/ports/`
- [ ] Definir interfaces: `LLMPort`, `RepositoryPort`, `EmbeddingsPort`
- [ ] Mover modelos críticos a `domain/models/`

### **Prioridad Media (Próxima Semana)**

- [ ] Refactorizar `chat_service.py` para usar puertos
- [ ] Refactorizar `embeddings_service.py` para usar puertos
- [ ] Crear adaptadores que implementen puertos

### **Prioridad Baja (Cuando sea posible)**

- [ ] Actualizar documentación de arquitectura
- [ ] Crear diagramas de dependencias
- [ ] Agregar ejemplos de uso

---

## 🔍 Checklist de Validación

### **Para cada archivo de Application:**

- [ ] ¿Importa de `src.adapters`? → ❌ Refactorizar
- [ ] ¿Usa interfaces/puertos? → ✅ Correcto
- [ ] ¿Conoce detalles de DB/API? → ❌ Refactorizar
- [ ] ¿Solo orquesta dominio? → ✅ Correcto

### **Para cada archivo de Domain:**

- [ ] ¿Importa de `src.adapters`? → ❌ Refactorizar
- [ ] ¿Importa de `src.application`? → ❌ Refactorizar
- [ ] ¿Solo usa tipos Python estándar? → ✅ Correcto
- [ ] ¿Define interfaces claras? → ✅ Correcto

---

## 📚 Referencias

- **Clean Architecture** - Robert C. Martin
- **Hexagonal Architecture** - Alistair Cockburn
- **Domain-Driven Design** - Eric Evans
- **Ports and Adapters Pattern**

---

## 🎯 Próximos Pasos

1. **Revisar y aprobar** este análisis
2. **Decidir** si refactorizar ahora o después del merge
3. **Crear branch** `feature/hexagonal-refactor`
4. **Implementar** cambios por fases
5. **Validar** con tests
6. **Documentar** arquitectura final

---

*Auditoría realizada: 2 de Octubre 2025*  
*Próxima revisión: Después de refactorización*
