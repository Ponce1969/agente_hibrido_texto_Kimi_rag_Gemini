# 🐻 Integración Bear API con Kimi-K2 - Guía Completa

## 📋 Resumen
Esta guía te llevará paso a paso para integrar Bear API con Kimi-K2, permitiendo búsqueda web en tiempo real durante las conversaciones.

## 🎯 Objetivo Final
Kimi-K2 podrá realizar búsquedas web cuando detecte que necesita información actualizada o contexto adicional.

---

## 🚀 PASOS A SEGUIR MAÑANA

### **PASO 1: Configuración Inicial (5 minutos)**

#### 1.1 Agregar API Key al .env
```bash
# Agregar a tu .env existente
BEAR_API_KEY=tu_clave_de_bear_aqui
BEAR_BASE_URL=https://api.bear.dev/v1
BEAR_SEARCH_ENABLED=true
BEAR_CACHE_TTL=3600
```

#### 1.2 Instalar dependencia (si es necesaria)
```bash
# Si Bear requiere alguna librería específica
uv add httpx  # Ya debería estar instalado
```

---

### **PASO 2: Crear el Adaptador Bear (15 minutos)**

#### 2.1 Crear archivo: `src/adapters/agents/bear_search_adapter.py`
```python
"""
Adaptador para integración con Bear API.
Parte de la arquitectura hexagonal - puerto de búsqueda web.
"""

import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
from datetime import datetime

class SearchResult(BaseModel):
    """Modelo para resultados de búsqueda."""
    title: str
    url: str
    snippet: str
    score: float
    source: str

class BearSearchAdapter:
    """Adaptador para búsqueda web con Bear API."""
    
    def __init__(self):
        self.api_key = os.getenv("BEAR_API_KEY")
        self.base_url = os.getenv("BEAR_BASE_URL", "https://api.bear.dev/v1")
        self.enabled = os.getenv("BEAR_SEARCH_ENABLED", "true").lower() == "true"
        
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Realiza búsqueda web con Bear API.
        
        Args:
            query: Término de búsqueda
            max_results: Número máximo de resultados
            
        Returns:
            Lista de resultados de búsqueda
        """
        if not self.enabled or not self.api_key:
            return []
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "query": query,
                        "max_results": max_results,
                        "include_snippets": True
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                return [
                    SearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        snippet=result.get("snippet", ""),
                        score=result.get("score", 0.0),
                        source="bear"
                    )
                    for result in data.get("results", [])
                ]
            except Exception as e:
                print(f"Error en búsqueda Bear: {e}")
                return []
    
    def should_search(self, prompt: str) -> bool:
        """
        Detecta si el prompt necesita búsqueda web.
        
        Args:
            prompt: El prompt del usuario
            
        Returns:
            True si debería buscar
        """
        search_keywords = [
            "actualidad", "última", "reciente", "2024", "2025",
            "noticias", "actualizado", "información reciente",
            "qué es", "cómo funciona", "definición"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in search_keywords)
```

---

### **PASO 3: Crear el Puerto (Interface) (5 minutos)**

#### 3.1 Crear archivo: `src/domain/ports/search_port.py`
```python
"""
Puerto (interface) para servicios de búsqueda web.
Parte de la arquitectura hexagonal.
"""

from abc import ABC, abstractmethod
from typing import List
from src.adapters.agents.bear_search_adapter import SearchResult

class SearchPort(ABC):
    """Interface para servicios de búsqueda web."""
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Realiza búsqueda web."""
        pass
    
    @abstractmethod
    def should_search(self, prompt: str) -> bool:
        """Determina si se necesita búsqueda."""
        pass
```

---

### **PASO 4: Modificar Kimi-K2 para usar búsqueda (20 minutos)**

#### 4.1 Actualizar `src/adapters/agents/groq_adapter.py`
```python
# Agregar al inicio del archivo
from src.adapters.agents.bear_search_adapter import BearSearchAdapter

# Agregar al constructor
class GroqAdapter:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.bear_search = BearSearchAdapter()
    
    async def generate_response(self, prompt: str, context: str = "") -> str:
        # Detectar si necesita búsqueda
        if self.bear_search.should_search(prompt):
            search_results = await self.bear_search.search(prompt)
            if search_results:
                search_context = self._format_search_results(search_results)
                prompt = f"{search_context}\n
Pregunta del usuario: {prompt}"
        
        # Resto del código existente...
    
    def _format_search_results(self, results: List[SearchResult]) -> str:
        """Formatea resultados de búsqueda para el contexto."""
        if not results:
            return ""
            
        formatted = "Información web relevante:\n"
        for i, result in enumerate(results[:3], 1):
            formatted += f"{i}. {result.title}\n"
            formatted += f"   {result.snippet}\n"
            formatted += f"   Fuente: {result.url}\n\n"
        return formatted
```

---

### **PASO 5: Agregar Toggle en Frontend (10 minutos)**

#### 5.1 Actualizar configuración en Streamlit
```python
# En src/adapters/streamlit/config.py o similar
import streamlit as st

# Agregar en la configuración
def get_bear_config():
    return {
        "enabled": st.sidebar.checkbox("Activar búsqueda web", value=True),
        "max_results": st.sidebar.slider("Máx. resultados búsqueda", 1, 10, 5)
    }
```

---

### **PASO 6: Tests de Integración (10 minutos)**

#### 6.1 Crear test: `tests/test_bear_integration.py`
```python
import pytest
from src.adapters.agents.bear_search_adapter import BearSearchAdapter

@pytest.mark.asyncio
async def test_bear_search_basic():
    """Test básico de búsqueda con Bear."""
    adapter = BearSearchAdapter()
    
    # Test sin API key
    os.environ["BEAR_API_KEY"] = ""
    results = await adapter.search("python async")
    assert results == []
    
    # Test de detección de búsqueda
    assert adapter.should_search("qué es FastAPI") == True
    assert adapter.should_search("hola mundo") == False
```

---

### **PASO 7: Documentación de Uso (2 minutos)**

#### 7.1 Ejemplos de uso en el chat:
```
Usuario: "¿Qué es FastAPI en 2024?"
Sistema: [Detecta necesidad de búsqueda] → Bear API → 
Respuesta: "FastAPI es un framework web moderno... [con info actualizada]"

Usuario: "últimas noticias de Python"
Sistema: [Busca en Bear] → Resultados web → 
Respuesta: "Las últimas noticias sobre Python incluyen..."
```

---

## 🧪 COMANDOS PARA PROBAR MAÑANA

### **Test rápido:**
```bash
# 1. Verificar configuración
uv run python -c "
from src.adapters.agents.bear_search_adapter import BearSearchAdapter
import asyncio

async def test():
    adapter = BearSearchAdapter()
    print('Bear configurado:', adapter.enabled)
    
asyncio.run(test())
"

# 2. Test de búsqueda
uv run python -c "
import asyncio
from src.adapters.agents.bear_search_adapter import BearSearchAdapter

async def test_search():
    adapter = BearSearchAdapter()
    results = await adapter.search('python 3.12 features')
    print(f'Resultados: {len(results)}')
    for r in results[:2]:
        print(f'- {r.title}')

asyncio.run(test_search())
"
```

### **Verificación completa:**
```bash
# 3. Test de integración
uv run pytest tests/test_bear_integration.py -v

# 4. Test end-to-end
python scripts/test_bear_integration.py
```

---

## 📝 CHECKLIST MAÑANA

- [ ] ✅ Agregar BEAR_API_KEY al .env
- [ ] ✅ Crear `bear_search_adapter.py`
- [ ] ✅ Crear `search_port.py`
- [ ] ✅ Modificar `groq_adapter.py`
- [ ] ✅ Agregar toggle en Streamlit
- [ ] ✅ Probar con prompts de búsqueda
- [ ] ✅ Ejecutar tests de integración

---

## 🎯 RESULTADO ESPERADO

Después de implementar esto, Kimi-K2 podrá responder:
- "¿Cuáles son las últimas features de Python 3.12?"
- "Noticias recientes sobre IA"
- "Información actualizada sobre FastAPI"

**Todo sin romper la arquitectura hexagonal existente.**

---

**Nota:** Si no tienes API key de Bear aún, puedes usar un mock para probar la arquitectura y luego reemplazar con la key real.