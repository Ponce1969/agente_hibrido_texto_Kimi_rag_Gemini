# LLM Gateway - Endpoint Interno para Modelos Locales

## 🎯 **Propósito**

El **LLM Gateway** es un endpoint interno (`/api/internal/llm-gateway`) que permite que los modelos locales (LLaMA 3 8B, Gemma 2B) puedan acceder al sistema RAG y Kimi sin modificar el frontend.

## 🔄 **Flujo de Arquitectura**

```
LLaMA (local) → /api/internal/llm-gateway → Backend → RAG/Kimi → Cache → Respuesta
```

- **Frontend**: Usa `/api/v1/chat` con switch Kimi/RAG
- **Modelos Locales**: Usan `/api/internal/llm-gateway` con routing automático

## 📡 **Endpoints Disponibles**

### 1. Gateway Principal
```
POST /api/internal/llm-gateway
```

**Request:**
```json
{
  "query": "¿Qué es la ortogonalidad?",
  "mode": "auto",      // "auto" | "kimi" | "rag"
  "session_id": 1
}
```

**Response:**
```json
{
  "answer": "Respuesta del sistema...",
  "mode_used": "rag",
  "cached": false,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Estado del Gateway
```
GET /api/internal/llm-gateway/status
```

**Response:**
```json
{
  "status": "operational",
  "cache_stats": {
    "total_cached": 150,
    "active_entries": 142
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🧠 **Modos de Operación**

### **Modo `auto`** (Recomendado)
El gateway decide automáticamente usando heurísticas:

- **RAG** para preguntas técnicas:
  - "qué es", "cómo funciona", "explicar"
  - Consultas > 50 caracteres
  - Referencias a documentos/libros
  
- **Kimi** para conversación:
  - Saludos, preguntas cortas
  - "hola", "gracias", "tiempo"

### **Modo `rag`**
Fuerza el uso del sistema RAG con Gemini + PDFs.

### **Modo `kimi`**
Fuerza el uso de Kimi K2 (sin RAG).

## 💾 **Sistema de Cache**

- **Base de datos**: SQLite (`llm_gateway_cache.db`)
- **TTL**: 24 horas por defecto
- **Hash**: SHA256 de `query + mode`
- **Beneficios**: Respuestas instantáneas para preguntas repetidas

## 🛠 **Uso con Modelos Locales**

### **Opción 1: Script Python**
```bash
# Básico
python src/scripts/local_llm_gateway_client.py "¿Qué es la ortogonalidad?"

# Específico
python src/scripts/local_llm_gateway_client.py "hola" --mode kimi

# Interactivo
python src/scripts/local_llm_gateway_client.py --interactive
```

### **Opción 2: Direct HTTP**
```python
import requests

def ask_backend(query, mode="auto"):
    payload = {"query": query, "mode": mode, "session_id": 1}
    response = requests.post(
        "http://localhost:8000/api/internal/llm-gateway",
        json=payload
    )
    return response.json()

# Uso
result = ask_backend("explicar Python")
print(result['answer'])
```

### **Opción 3: Desde Ollama**
```bash
# Template para Ollama
curl -X POST http://localhost:8000/api/internal/llm-gateway \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué es DRY?", "mode": "auto", "session_id": 1}'
```

## 🎯 **Casos de Uso Típicos**

### **LLaMA 3 8B (Modelo Principal)**
```python
# Para preguntas complejas
response = ask_backend("explicar arquitectura microservicios", mode="rag")

# Para conversación
response = ask_backend("hola, cómo estás?", mode="kimi")

# Automático (recomendado)
response = ask_backend("¿Qué significa ser pragmático?")
```

### **Gemma 2B (Modelo Ligero)**
```python
# Delega trabajo pesado al RAG
response = ask_backend("documentación Python requests", mode="rag")

# Consultas rápidas
response = ask_backend("weather today", mode="kimi")
```

## 📊 **Ventajas del Sistema**

### **✅ Sin Modificar Frontend**
- Usuarios no ven cambios
- Switch original intacto
- Experiencia consistente

### **✅ Cache Inteligente**
- Respuestas instantáneas repetidas
- Reducción de costos API
- Mejor rendimiento

### **✅ Routing Automático**
- Heurísticas inteligentes
- Balance RAG/Kimi óptimo
- Transparencia para usuario

### **✅ Extensible**
- Fácil agregar nuevos modelos
- Modular y mantenible
- Métricas integradas

## 🔧 **Configuración y Monitoreo**

### **Ver Estado**
```bash
curl http://localhost:8000/api/internal/llm-gateway/status
```

### **Limpiar Cache**
```bash
# Opción futura: DELETE /api/internal/llm-gateway/cache
```

### **Logs**
```bash
# Los logs del gateway aparecen en:
# - Consola del backend
# - Archivos de log configurados
```

## 🚀 **Ejemplo Completo**

```python
#!/usr/bin/env python3
"""Ejemplo: LLaMA local usando el gateway."""

import requests
import json

def smart_assistant(query):
    """Asistente inteligente que delega al backend."""
    
    # Consultar al gateway
    response = requests.post(
        "http://localhost:8000/api/internal/llm-gateway",
        json={"query": query, "mode": "auto", "session_id": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # LLaMA procesa la respuesta del backend
        backend_answer = data['answer']
        mode_used = data['mode_used']
        
        # LLaMA genera respuesta final
        final_response = f"Según {'RAG' if mode_used == 'rag' else 'Kimi'}: {backend_answer}"
        
        return final_response
    else:
        return "Error al consultar el backend"

# Uso
print(smart_assistant("¿Qué es la ortogonalidad?"))
print(smart_assistant("hola, cómo estás?"))
```

## 🎉 **Resumen**

El **LLM Gateway** permite que tus modelos locales:
- ✅ Accedan al RAG mejorado con Gemini
- ✅ Usen Kimi para conversación
- ✅ Disfruten de cache inteligente
- ✅ Operen sin modificar el frontend
- ✅ Se integren fácilmente con Ollama

**¡Listo para usar! Los modelos locales ahora pueden aprovechar todo el poder del backend** 🚀
