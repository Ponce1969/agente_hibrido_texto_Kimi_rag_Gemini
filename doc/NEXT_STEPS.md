# 📋 Próximos Pasos - Cleanup y Migración Final

**Fecha:** 4 de Octubre 2025  
**Estado Actual:** ✅ Arquitectura hexagonal implementada, endpoints pendientes de migrar

---

## 🎯 Situación Actual

### **✅ Completado (Día 1-3)**

- ✅ Arquitectura hexagonal implementada
- ✅ Puertos creados (LLMPort, ChatRepositoryPort, EmbeddingsPort)
- ✅ Adaptadores creados (Groq, Gemini, GeminiEmbeddings, Repository)
- ✅ Servicios refactorizados (ChatServiceV2, EmbeddingsServiceV2)
- ✅ Dependencies (DI factory) creado
- ✅ 36 tests pasando (100%)
- ✅ Sistema de embeddings migrado a Gemini API

### **⏸️ Pendiente**

- ⏸️ Actualizar endpoints para usar servicios v2
- ⏸️ Eliminar archivos antiguos
- ⏸️ Renombrar v2 → oficial
- ⏸️ Validación final (0 violaciones)

---

## 📂 Archivos Actuales

### **Archivos NUEVOS (Arquitectura Hexagonal)** ✅

```
src/domain/ports/
├── llm_port.py                        ✅ Interface LLM
├── repository_port.py                 ✅ Interface Repository
└── embeddings_port.py                 ✅ Interface Embeddings

src/application/services/
├── chat_service_v2.py                 ✅ Sin violaciones
└── embeddings_service_v2.py           ✅ Sin violaciones

src/adapters/agents/
├── groq_adapter.py                    ✅ Implementa LLMPort
├── gemini_adapter.py                  ✅ Implementa LLMPort
└── gemini_embeddings_adapter.py       ✅ Implementa EmbeddingsPort

src/adapters/db/
└── chat_repository_adapter.py         ✅ Implementa ChatRepositoryPort

src/adapters/
└── dependencies.py                    ✅ DI Factory
```

### **Archivos ANTIGUOS (Todavía en uso por endpoints)** ⏸️

```
src/application/services/
├── chat_service.py                    ⚠️ Usado por endpoints/chat.py
├── embeddings_service.py              ⚠️ Usado por endpoints/files.py, embeddings.py
└── domain_chat_service.py             ⚠️ Usado por endpoints/domain_chat.py

src/adapters/agents/
├── groq_client.py                     ⚠️ Usado por chat_service.py
└── gemini_client.py                   ⚠️ Usado por chat_service.py
```

### **Endpoints que usan código antiguo** ⚠️

```
src/adapters/api/endpoints/
├── chat.py                            ⚠️ Usa ChatService (antiguo)
├── files.py                           ⚠️ Usa EmbeddingsService (antiguo)
├── embeddings.py                      ⚠️ Usa EmbeddingsService (antiguo)
└── domain_chat.py                     ⚠️ Usa ChatApplicationService (antiguo)
```

---

## 🚀 Plan de Migración Final

### **Fase 1: Probar Sistema Actual** (AHORA)

**Objetivo:** Verificar que todo funciona antes de hacer cambios

**Acciones:**
1. ✅ Hacer commit del estado actual
2. ✅ Documentar próximos pasos (este archivo)
3. ⏸️ Hacer Docker build
4. ⏸️ Probar endpoints existentes
5. ⏸️ Verificar que RAG funciona
6. ⏸️ Verificar que chat funciona

**Comandos:**
```bash
# Build de Docker
docker compose build

# Levantar servicios
docker compose up -d

# Probar endpoints
curl http://localhost:8000/api/sessions
curl http://localhost:8000/api/files
```

---

### **Fase 2: Actualizar Endpoints** (FUTURO - ~1h)

**Objetivo:** Migrar endpoints para usar servicios v2

#### **2.1. Actualizar chat.py**

**Cambios necesarios:**

```python
# ANTES (líneas 12-14):
from src.adapters.agents.groq_client import GroqClient
from src.application.services.chat_service import ChatService
from src.adapters.agents.gemini_client import GeminiClient

# DESPUÉS:
from src.adapters.dependencies import get_chat_service_dependency
from src.application.services.chat_service_v2 import ChatServiceV2
```

**Actualizar dependency (líneas 26-33):**

```python
# ANTES:
def get_chat_service(
    session: Session = Depends(get_session),
    client: GroqClient = Depends(get_groq_client),
) -> ChatService:
    repo = ChatRepository(session)
    gemini = GeminiClient(client=httpx.AsyncClient())
    return ChatService(repo, client, gemini)

# DESPUÉS:
# Usar directamente get_chat_service_dependency de dependencies.py
```

**Actualizar endpoint (línea 58):**

```python
# ANTES:
async def handle_chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):

# DESPUÉS:
async def handle_chat(
    request: ChatRequest,
    service: ChatServiceV2 = Depends(get_chat_service_dependency),
):
```

**⚠️ IMPORTANTE:** ChatServiceV2 tiene interfaz diferente:
- Método: `handle_message()` en vez de `handle_chat_message()`
- Parámetros diferentes
- Necesita adaptación

#### **2.2. Actualizar files.py y embeddings.py**

**Cambios necesarios:**

```python
# ANTES:
from src.application.services.embeddings_service import EmbeddingsService

# DESPUÉS:
from src.adapters.dependencies import get_embeddings_service_dependency
from src.application.services.embeddings_service_v2 import EmbeddingsServiceV2
```

**⚠️ IMPORTANTE:** EmbeddingsServiceV2 tiene interfaz diferente:
- Métodos async
- Parámetros diferentes
- Necesita adaptación

#### **2.3. Actualizar domain_chat.py**

**Opción 1:** Actualizar para usar ChatServiceV2  
**Opción 2:** Eliminar si no se usa

---

### **Fase 3: Eliminar Archivos Antiguos** (FUTURO - ~5 min)

**Objetivo:** Limpiar código antiguo después de migrar endpoints

**Archivos a eliminar:**

```bash
# Servicios antiguos
rm src/application/services/chat_service.py
rm src/application/services/embeddings_service.py
rm src/application/services/domain_chat_service.py

# Clientes antiguos
rm src/adapters/agents/groq_client.py
rm src/adapters/agents/gemini_client.py
```

**⚠️ SOLO HACER DESPUÉS de actualizar endpoints**

---

### **Fase 4: Renombrar v2 → Oficial** (FUTURO - ~5 min)

**Objetivo:** Hacer que los servicios v2 sean los oficiales

**Comandos:**

```bash
# Renombrar servicios
mv src/application/services/chat_service_v2.py src/application/services/chat_service.py
mv src/application/services/embeddings_service_v2.py src/application/services/embeddings_service.py

# Actualizar imports en dependencies.py
# Cambiar:
#   from src.application.services.chat_service_v2 import ChatServiceV2
# Por:
#   from src.application.services.chat_service import ChatService
```

---

### **Fase 5: Validación Final** (FUTURO - ~10 min)

**Objetivo:** Verificar 0 violaciones y 100% tests

**Comandos:**

```bash
# Verificar arquitectura
python scripts/analyze_architecture.py

# Ejecutar todos los tests
pytest tests/ -v

# Verificar tipado
mypy src/ --strict

# Build final de Docker
docker compose build
docker compose up -d
```

**Resultado esperado:**
- ✅ 0 violaciones de arquitectura
- ✅ 100% tests pasando
- ✅ mypy --strict: Success
- ✅ Docker funcionando

---

## 📊 Checklist de Migración

### **Antes de empezar:**
- [ ] Hacer backup del código actual
- [ ] Commit de todo el trabajo
- [ ] Documentar estado actual (este archivo)

### **Fase 1: Probar (AHORA)**
- [ ] Docker build exitoso
- [ ] Endpoints funcionando
- [ ] RAG funcionando
- [ ] Chat funcionando

### **Fase 2: Actualizar Endpoints**
- [ ] Actualizar chat.py
- [ ] Actualizar files.py
- [ ] Actualizar embeddings.py
- [ ] Actualizar/eliminar domain_chat.py
- [ ] Probar cada endpoint después de actualizar

### **Fase 3: Cleanup**
- [ ] Eliminar chat_service.py
- [ ] Eliminar embeddings_service.py
- [ ] Eliminar domain_chat_service.py
- [ ] Eliminar groq_client.py
- [ ] Eliminar gemini_client.py

### **Fase 4: Renombrar**
- [ ] Renombrar chat_service_v2.py → chat_service.py
- [ ] Renombrar embeddings_service_v2.py → embeddings_service.py
- [ ] Actualizar imports en dependencies.py
- [ ] Actualizar imports en endpoints

### **Fase 5: Validación**
- [ ] analyze_architecture.py: 0 violaciones
- [ ] pytest: 100% passing
- [ ] mypy --strict: Success
- [ ] Docker build exitoso
- [ ] Sistema funcionando end-to-end

---

## ⚠️ Notas Importantes

### **Por qué NO migrar endpoints ahora:**

1. **Interfaces diferentes:**
   - ChatServiceV2 usa `handle_message()` vs `handle_chat_message()`
   - Parámetros diferentes
   - Necesita adaptación cuidadosa

2. **Riesgo de romper funcionalidad:**
   - Endpoints actuales funcionan
   - Mejor probar primero, migrar después
   - Enfoque conservador y seguro

3. **Tiempo estimado:**
   - Actualizar endpoints: ~1 hora
   - Probar y validar: ~30 min
   - Total: ~1.5 horas adicionales

### **Estrategia Recomendada:**

✅ **AHORA (Día 3 - Completado):**
- Arquitectura hexagonal implementada
- Código nuevo sin violaciones
- Tests pasando
- Documentación completa

✅ **SIGUIENTE SESIÓN (Día 4 - Futuro):**
- Probar Docker build
- Verificar funcionamiento
- Migrar endpoints uno por uno
- Cleanup final
- Validación completa

---

## 🎯 Objetivo Final

**Estado deseado:**
```
✅ 0 violaciones de arquitectura
✅ 100% tests pasando
✅ Código limpio (sin archivos antiguos)
✅ Endpoints usando servicios v2
✅ Docker funcionando
✅ Sistema production-ready
```

**Tiempo estimado total:** ~2 horas adicionales

---

## 📝 Comandos Útiles

### **Verificar qué archivos usan servicios antiguos:**

```bash
# Ver imports de chat_service antiguo
grep -r "from.*chat_service import" src/ --include="*.py"

# Ver imports de embeddings_service antiguo
grep -r "from.*embeddings_service import" src/ --include="*.py"

# Ver imports de clientes antiguos
grep -r "from.*groq_client import\|from.*gemini_client import" src/ --include="*.py"
```

### **Verificar arquitectura:**

```bash
# Analizar violaciones
python scripts/analyze_architecture.py

# Ver solo violaciones críticas
python scripts/analyze_architecture.py | grep "🔴"
```

### **Docker:**

```bash
# Build
docker compose build

# Up
docker compose up -d

# Logs
docker compose logs -f

# Down
docker compose down
```

---

**Documento creado:** 4 de Octubre 2025, 21:15  
**Última actualización:** 4 de Octubre 2025, 21:15  
**Estado:** Documentación de próximos pasos completada
