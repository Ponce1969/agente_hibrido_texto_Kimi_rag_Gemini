# 🚀 Guía Rápida para Desarrolladores Junior

**Última actualización:** 29 de Septiembre 2025  
**Nivel:** Principiante/Intermedio  
**Tiempo de lectura:** 10 minutos

---

## 👋 ¡Bienvenido al Proyecto!

Este es un **asistente de IA para aprendizaje de Python** con capacidades avanzadas de procesamiento de documentos PDF. El proyecto está **100% completado** y listo para usar.

---

## 🎯 ¿Qué Hace Este Proyecto?

### **Funcionalidad Principal**
Imagina que tienes un libro de Python en PDF y quieres hacerle preguntas específicas. Este sistema:

1. **Lee el PDF** y lo divide en pequeños fragmentos (chunks)
2. **Indexa el contenido** en una base de datos vectorial
3. **Busca información relevante** cuando haces una pregunta
4. **Responde con precisión** usando IA (Gemini 2.5)

### **Dos Modos de Uso**

```
┌─────────────────────────────────────────────┐
│  💬 Modo Chat Normal (Kimi-K2)             │
│  • Conversación general sobre Python       │
│  • Sin necesidad de PDF                    │
│  • Respuestas rápidas                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔍 Modo RAG (Gemini + PDF)                │
│  • Consultas específicas sobre el PDF      │
│  • Búsqueda semántica inteligente          │
│  • Respuestas basadas en el documento      │
└─────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura Simplificada

```
┌──────────────┐
│   USUARIO    │
│  (Navegador) │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│  FRONTEND (Streamlit)        │
│  • Interfaz web bonita       │
│  • Selector de PDFs          │
│  • Chat interactivo          │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  BACKEND (FastAPI)           │
│  • Procesa las peticiones    │
│  • Busca en la base de datos │
│  • Llama a las IAs           │
└──────┬───────────────────────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ SQLite   │  │PostgreSQL│  │   IAs    │
│ (Chat)   │  │ (Vectors)│  │ Kimi/Gem │
└──────────┘  └──────────┘  └──────────┘
```

---

## 🚀 Cómo Empezar (Paso a Paso)

### **Paso 1: Clonar el Proyecto**
```bash
cd /home/gonzapython/Documentos/vscode_codigo/agentes_Front_Bac/agentes_Front_Bac
```

### **Paso 2: Configurar Variables de Entorno**
Crea un archivo `.env` con tus API keys:
```env
GROQ_API_KEY=tu_key_de_groq
GEMINI_API_KEY=tu_key_de_gemini
```

**¿Dónde conseguir las keys?**
- **Groq**: https://console.groq.com/
- **Gemini**: https://makersuite.google.com/app/apikey

### **Paso 3: Iniciar con Docker**
```bash
docker compose up -d
```

**¿Qué hace este comando?**
- Levanta 3 contenedores: Frontend, Backend y PostgreSQL
- Instala todas las dependencias automáticamente
- Configura las bases de datos

### **Paso 4: Acceder a la Aplicación**
Abre tu navegador en: **http://localhost:8501**

---

## 📖 Cómo Usar la Aplicación

### **Opción A: Chat Normal (Sin PDF)**

1. Abre http://localhost:8501
2. En el sidebar, selecciona un agente (ej: "Arquitecto Python Senior")
3. **NO actives** el toggle "Activar Búsqueda Inteligente en PDF"
4. Escribe tu pregunta: "¿Qué es una función en Python?"
5. ¡Recibe tu respuesta!

### **Opción B: Consultar el PDF (Con RAG)**

1. Ve a la pestaña **"📂 Usar Existente"**
2. Verás el PDF "Fluent Python" ya indexado
3. Click en **"📌 Seleccionar"**
4. **Activa** el toggle "Activar Búsqueda Inteligente en PDF"
5. Pregunta: "¿Qué dice el PDF sobre funciones de primera clase?"
6. ¡Recibe una respuesta basada en el PDF!

---

## 🧪 Probar que Todo Funciona

### **Test Rápido**
```bash
python3 scripts/test_rag.py
```

**Resultado esperado:**
```
✅ PASS - Health Check
✅ PASS - Listar Archivos
✅ PASS - Chat sin RAG
✅ PASS - Chat con RAG

🎯 Total: 4/4 tests pasados
```

---

## 📂 Estructura del Proyecto (Simplificada)

```
agentes_Front_Bac/
├── src/
│   ├── adapters/
│   │   ├── api/              # Endpoints del backend
│   │   ├── db/               # Conexión a bases de datos
│   │   ├── agents/           # Integración con IAs
│   │   └── streamlit/        # Interfaz web
│   ├── application/
│   │   └── services/         # Lógica de negocio
│   └── domain/               # Modelos y reglas
├── scripts/
│   └── test_rag.py          # Tests automatizados
├── doc/                      # Documentación (estás aquí)
├── docker-compose.yml        # Configuración de Docker
└── .env                      # Variables de entorno (crear)
```

---

## 🔧 Comandos Útiles

### **Ver Logs**
```bash
# Ver logs del backend
docker compose logs backend --tail 50

# Ver logs del frontend
docker compose logs frontend --tail 50

# Ver todos los logs
docker compose logs --tail 100
```

### **Reiniciar Servicios**
```bash
# Reiniciar todo
docker compose restart

# Reiniciar solo el backend
docker compose restart backend

# Reiniciar solo el frontend
docker compose restart frontend
```

### **Detener Todo**
```bash
docker compose down
```

### **Ver Estado**
```bash
docker compose ps
```

---

## 🐛 Solución de Problemas Comunes

### **Problema 1: "No puedo acceder a http://localhost:8501"**
**Solución:**
```bash
# Verifica que los contenedores estén corriendo
docker compose ps

# Si no están corriendo, inícialo
docker compose up -d
```

### **Problema 2: "Error de API Key"**
**Solución:**
1. Verifica que el archivo `.env` existe
2. Verifica que las keys son correctas
3. Reinicia los contenedores: `docker compose restart`

### **Problema 3: "El RAG no funciona"**
**Solución:**
```bash
# Ejecuta el script de prueba
python3 scripts/test_rag.py

# Verifica que PostgreSQL esté corriendo
docker compose ps postgres
```

---

## 📚 Conceptos Clave para Entender

### **¿Qué es RAG?**
**RAG** = Retrieval-Augmented Generation

Es una técnica que combina:
1. **Búsqueda** (Retrieval): Encuentra información relevante en documentos
2. **Generación** (Generation): La IA usa esa información para responder

**Analogía:** Es como tener un asistente que:
- Lee el libro antes de responder (Retrieval)
- Formula una respuesta basada en lo que leyó (Generation)

### **¿Qué son los Embeddings?**
Son representaciones numéricas de texto que permiten comparar similitud.

**Ejemplo:**
```
"función en Python" → [0.23, 0.45, 0.12, ...]
"método de Python"  → [0.25, 0.43, 0.15, ...]
                      ↑ Vectores similares = conceptos similares
```

### **¿Qué es pgvector?**
Es una extensión de PostgreSQL que permite buscar vectores similares de forma eficiente.

---

## 🎓 Próximos Pasos para Aprender

### **Nivel 1: Explorar**
1. ✅ Usa la aplicación (chat normal y RAG)
2. ✅ Lee `doc/RAG_SYSTEM_COMPLETE.md`
3. ✅ Ejecuta los tests

### **Nivel 2: Entender**
1. Lee `doc/IMPLEMENTATION.md`
2. Revisa el código de `src/adapters/streamlit/app.py`
3. Mira cómo funciona `src/application/services/chat_service.py`

### **Nivel 3: Modificar**
1. Cambia el prompt de un agente en `src/adapters/agents/prompts.py`
2. Agrega un nuevo agente
3. Modifica la interfaz en `src/adapters/streamlit/components/`

### **Nivel 4: Extender**
1. Agrega soporte para más tipos de documentos
2. Implementa caché de embeddings
3. Agrega métricas de uso

---

## 🤝 ¿Necesitas Ayuda?

### **Documentación Adicional**
- **Sistema RAG completo**: `doc/RAG_SYSTEM_COMPLETE.md`
- **Estado del proyecto**: `doc/IMPLEMENTATION.md`
- **Arquitectura**: `doc/ARCHITECTURE_IMPROVEMENTS.md`

### **Recursos Externos**
- **FastAPI**: https://fastapi.tiangolo.com/
- **Streamlit**: https://docs.streamlit.io/
- **pgvector**: https://github.com/pgvector/pgvector

---

## 🎉 ¡Felicitaciones!

Si llegaste hasta aquí, ya sabes:
- ✅ Qué hace el proyecto
- ✅ Cómo iniciar la aplicación
- ✅ Cómo usar ambos modos (chat y RAG)
- ✅ Cómo solucionar problemas comunes
- ✅ Conceptos clave del sistema

**¡Ahora estás listo para explorar el código!** 🚀

---

*Documento creado: 29 de Septiembre 2025*  
*Para desarrolladores junior que se unen al proyecto*  
*Versión: 1.0.0*
