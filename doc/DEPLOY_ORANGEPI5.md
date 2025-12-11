# Guía de Despliegue en Orange Pi 5 Plus

## 🎯 **Respuesta Directa a tu Pregunta**

**Sí, en principio debería funcionar con `git pull`, pero necesitas hacer algunos pasos adicionales** para que todo esté listo en producción.

---

## 📋 **¿Qué funciona automáticamente con `git pull`?**

✅ **Código del LLM Gateway** - Endpoint interno `/api/internal/llm-gateway`
✅ **Lógica de cache SQLite** - Para respuestas repetidas
✅ **Heurísticas automáticas** - RAG vs Kimi inteligente
✅ **Scripts de prueba** - Validación de conexión
✅ **Documentación** - Guías y ejemplos

---

## ⚠️ **¿Qué necesitas configurar manualmente?**

### **1. Variables de Entorno (.env)**
```bash
# Copiar template
cp .env.template .env

# Editar con tus valores:
GROQ_API_KEY=tu_key_aqui
GEMINI_API_KEY=tu_key_aqui  
BEAR_API_KEY=tu_key_aqui
JWT_SECRET_KEY=tu_secreto_aqui
```

### **2. Dependencias del Sistema**
```bash
# Python 3.12, PostgreSQL, Redis, Nginx
sudo apt update
sudo apt install python3.12 postgresql redis-server nginx
```

### **3. Modelos Locales (Ollama)**
```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelos
ollama pull llama3.1:8b
ollama pull gemma:2b
```

### **4. Base de Datos con 10 PDFs**
```bash
# Inicializar DB
uv run python src/scripts/init_db.py

# Subir tus 10 PDFs de Python por la UI o API
# http://localhost:8000/docs
```

---

## 🚀 **Pasos Completos para Orange Pi 5 Plus**

### **Opción A: Manual (Recomendado para prueba)**
```bash
# 1. Pull del código
git pull origin main

# 2. Instalar dependencias
uv venv --python 3.12
uv pip install -e .

# 3. Configurar .env
cp .env.template .env
# Editar .env con tus API keys

# 4. Inicializar DB
uv run python src/scripts/init_db.py

# 5. Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
ollama pull gemma:2b

# 6. Iniciar servicios
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
ollama serve &

# 7. Probar
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

### **Opción B: Automático (Script completo)**
```bash
# Descargar y ejecutar script de despliegue
wget https://raw.githubusercontent.com/TU_REPO/deploy_orangepi5.sh
chmod +x deploy_orangepi5.sh
./deploy_orangepi5.sh
```

---

## 🔧 **Configuración Específica para 10 PDFs de Python**

### **Ajustes recomendados en `.env`:**
```env
# Para 10 PDFs grandes de Python
FILE_MAX_PDF_PAGES=50          # Permitir más páginas
FILE_CONTEXT_MAX_CHARS=8000    # Más contexto
RAG_NORMAL_TOP_K=15           # Más chunks para búsqueda
EMBEDDING_BATCH_SIZE=1        # Conservar RAM en Orange Pi
```

### **Optimizaciones para Orange Pi 5 Plus:**
```env
# ARM64 optimización
EMBEDDING_BATCH_SIZE=2
WORKERS=2                     # 2 cores para API
MAX_TOKENS=4096               # Reducir si hay lentitud
```

---

## 🧪 **Pruebas de Validación**

### **1. Verificar API**
```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"Asistente IA con RAG"}
```

### **2. Verificar Ollama**
```bash
curl http://localhost:11434/api/tags
# Debe mostrar llama3.1:8b y gemma:2b
```

### **3. Probar LLM Gateway**
```bash
curl -X POST http://localhost:8000/api/internal/llm-gateway \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué es Python?", "mode": "rag", "session_id": 1}'
```

### **4. Probar con Modelos Locales**
```bash
# Usar script de prueba
uv run python src/scripts/test_llm_gateway_direct.py
```

---

## 🎯 **Flujo Completo de Despliegue**

```
1. git pull origin main           # ↓ Código actualizado
2. cp .env.template .env          # ↓ Configurar API keys  
3. uv pip install -e .            # ↓ Dependencias Python
4. uv run python init_db.py       # ↓ Base de datos
5. ollama pull llama3.1:8b         # ↓ Modelos locales
6. uvicorn src.main:app           # ↓ Iniciar API
7. Subir 10 PDFs de Python        # ↓ Cargar documentos
8. Probar LLM Gateway             # ↓ Validar conexión
```

---

## ✅ **¿Qué obtienes al final?**

- ✅ **Frontend Streamlit**: http://localhost:8501
- ✅ **API Backend**: http://localhost:8000  
- ✅ **LLM Gateway**: http://localhost:8000/api/internal/llm-gateway
- ✅ **Modelos locales**: LLaMA 3 8B + Gemma 2B
- ✅ **RAG con 10 PDFs**: Gemini + búsqueda precisa
- ✅ **Cache inteligente**: SQLite 24h TTL

---

## 🚨 **Posibles Problemas y Soluciones**

### **Problema: "Import error en ARM64"**
```bash
# Solución: Reinstalar dependencias específicas ARM64
uv pip install --force-reinstall --no-cache-dir sentence-transformers
```

### **Problema: "Ollama no responde"**
```bash
# Solución: Verificar servicio
sudo systemctl status ollama
sudo systemctl restart ollama
```

### **Problema: "Memoria insuficiente"**
```bash
# Solución: Reducir batch size
EMBEDDING_BATCH_SIZE=1 en .env
```

---

## 🎉 **Resumen**

**Con `git pull` + configuración manual (~15 min) tienes todo funcionando.**

El **LLM Gateway interno** estará disponible y los modelos locales (LLaMA 3 8B, Gemma 2B) podrán consultar tus 10 PDFs de Python con el RAG mejorado de Gemini.

**¿Listo para desplegar en tu Orange Pi 5 Plus?** 🚀
