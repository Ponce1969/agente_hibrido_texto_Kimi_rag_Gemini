# 📊 Reporte de Violaciones de Arquitectura Hexagonal

**Fecha:** 2025-10-10  
**Proyecto:** Agentes Front-Back (Sistema RAG Híbrido)

---

## 📈 Resumen Ejecutivo

- ❌ **Errores Críticos:** 2
- ⚠️ **Advertencias:** 1
- ℹ️ **Información:** 1

**Estado General:** ⚠️ Requiere atención - Arquitectura mayormente limpia con 2 violaciones críticas

---

## ❌ Errores Críticos (Prioridad Alta)

### 1. Application importa Adapters (DEPENDENCY_INVERSION)

**Archivo:** `application/services/file_processing_service.py:16`

**Problema:**
```python
from src.adapters.config.settings import settings
```

**Impacto:** La capa de aplicación está acoplada directamente a la configuración de adapters, violando el principio de inversión de dependencias.

**Solución:**
```python
# Opción 1: Inyectar settings como dependencia
class FileProcessingService:
    def __init__(
        self, 
        file_repo: FileRepositoryPort,
        embeddings_service: EmbeddingsServiceV2,
        max_chunk_size: int = 600,  # Inyectar valores específicos
        chunk_overlap: int = 100,
    ):
        ...

# Opción 2: Crear un puerto de configuración en domain
# domain/ports/config_port.py
from abc import ABC, abstractmethod

class ConfigPort(ABC):
    @abstractmethod
    def get_chunk_size(self) -> int: ...
    
    @abstractmethod
    def get_chunk_overlap(self) -> int: ...

# Luego inyectar ConfigPort en el servicio
```

---

### 2. Uso directo de FastAPI en Application (FRAMEWORK_LEAKAGE)

**Archivo:** `application/services/chat_service.py:0`

**Problema:** El servicio de aplicación usa directamente tipos o decoradores de FastAPI.

**Impacto:** La lógica de negocio está acoplada al framework web, dificultando testing y portabilidad.

**Solución:**
```python
# ❌ MAL - No usar tipos de FastAPI en application
from fastapi import UploadFile

async def process_file(self, file: UploadFile):
    ...

# ✅ BIEN - Usar tipos genéricos o del dominio
from typing import BinaryIO

async def process_file(self, file: BinaryIO, filename: str, size: int):
    ...
```

**Recomendación:** Crear DTOs en `domain/models` para representar datos de entrada/salida sin acoplar a FastAPI.

---

## ⚠️ Advertencias (Prioridad Media)

### 3. Puerto definido fuera de domain/ports (PORT_LOCATION)

**Archivo:** `domain/repositories/chat_repository.py:0`

**Problema:** Hay un puerto (ABC con @abstractmethod) definido en `domain/repositories/` en lugar de `domain/ports/`.

**Impacto:** Organización inconsistente del código, dificulta encontrar puertos.

**Solución:**
```bash
# Mover el archivo
mv src/domain/repositories/chat_repository.py src/domain/ports/chat_repository_port.py

# Actualizar imports en todos los archivos que lo usen
# Buscar: from src.domain.repositories.chat_repository import ...
# Reemplazar: from src.domain.ports.chat_repository_port import ...
```

---

## ℹ️ Información (Prioridad Baja)

### 4. Modelo de dominio fuera de domain/models (MODEL_LOCATION)

**Archivo:** `domain/ports/python_search_port.py:0`

**Problema:** Hay un `@dataclass` definido en el archivo de puerto en lugar de `domain/models/`.

**Impacto:** Menor - Solo afecta organización del código.

**Solución:**
```python
# domain/ports/python_search_port.py
# Mover PythonSource a domain/models/python_models.py

# domain/models/python_models.py
from dataclasses import dataclass

@dataclass
class PythonSource:
    url: str
    title: str
    snippet: str
    source_type: str
    reliability: int

# domain/ports/python_search_port.py
from abc import ABC, abstractmethod
from src.domain.models.python_models import PythonSource

class PythonSearchPort(ABC):
    @abstractmethod
    async def search_python_bug(self, error_message: str) -> List[PythonSource]:
        ...
```

---

## 🎯 Plan de Acción Recomendado

### Fase 1: Correcciones Críticas (Inmediato)

1. **Eliminar import de settings en application**
   - Inyectar valores de configuración como parámetros
   - O crear un ConfigPort en domain

2. **Eliminar uso de FastAPI en application**
   - Reemplazar tipos de FastAPI por tipos genéricos
   - Crear DTOs en domain para datos de entrada/salida

### Fase 2: Mejoras de Organización (Corto plazo)

3. **Mover puerto de chat_repository**
   - De `domain/repositories/` a `domain/ports/`
   - Actualizar imports

4. **Reorganizar modelos**
   - Mover dataclasses de ports a models
   - Mantener ports solo con interfaces

---

## 📚 Principios de Arquitectura Hexagonal

### ✅ Reglas de Oro

1. **Domain es el núcleo:**
   - No depende de nada externo
   - Solo tipos de Python estándar
   - Define puertos (interfaces)

2. **Application orquesta:**
   - Depende solo de Domain
   - Implementa casos de uso
   - No conoce frameworks

3. **Adapters implementa:**
   - Depende de Domain y Application
   - Implementa puertos
   - Contiene detalles de frameworks

### 🔄 Flujo de Dependencias

```
Adapters (FastAPI, SQLModel, Streamlit)
    ↓ depende de
Application (Services, Use Cases)
    ↓ depende de
Domain (Ports, Models, Entities)
```

---

## 🛠️ Uso del Script de Verificación

```bash
# Ejecutar análisis
python3 scripts/check_hexagonal_architecture.py

# Integrar en CI/CD
# .github/workflows/architecture-check.yml
- name: Check Architecture
  run: python3 scripts/check_hexagonal_architecture.py
```

---

## 📊 Estado Actual vs. Ideal

| Aspecto | Estado Actual | Estado Ideal |
|---------|---------------|--------------|
| Pureza del Domain | ✅ Bueno | ✅ Perfecto |
| Inversión de Dependencias | ⚠️ 1 violación | ✅ Sin violaciones |
| Separación de Frameworks | ⚠️ 1 violación | ✅ Sin violaciones |
| Organización de Código | ℹ️ 2 mejoras menores | ✅ Perfecta |

---

## 🎉 Aspectos Positivos

✅ Domain no importa adapters  
✅ No hay frameworks en domain  
✅ Puertos bien definidos (mayoría)  
✅ Separación clara de capas  
✅ Uso correcto de dependency injection  

---

## 📝 Notas

- El proyecto tiene una arquitectura **muy sólida** en general
- Las violaciones encontradas son **menores y fáciles de corregir**
- La mayoría del código respeta los principios hexagonales
- El sistema es **testeable y mantenible**

---

**Generado por:** `scripts/check_hexagonal_architecture.py`  
**Versión:** 1.0.0
