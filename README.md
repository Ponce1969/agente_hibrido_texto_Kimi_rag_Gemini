# 🤖 Asistente IA con RAG - Sistema Multi-Agente

> **Sistema de asistencia inteligente con arquitectura hexagonal, múltiples agentes especializados, RAG y seguridad avanzada.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)

---

## ⚡ **Inicio Rápido**

```bash
# 1. Clonar el repositorio
git clone https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini.git
cd agente_hibrido_texto_Kimi_rag_Gemini

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Iniciar con Docker
docker compose up -d --build

# 4. Acceder
# Frontend: http://localhost:8501
# Backend API: http://localhost:8000/docs
```

---

## 🎯 **Características Principales**

- 🤖 **Routing LLM configurable:** DeepSeek, Groq (Kimi-K2), Gemini — cambiar desde .env sin código
- 📚 **RAG con pgvector:** Consulta PDFs con búsqueda semántica
- 🌐 **Brave Search:** Búsquedas Python especializadas
- 🛡️ **Guardian de Seguridad:** Protección contra prompt injection y jailbreak
- 🔐 **JWT Auth:** Endpoints protegidos con autenticación
- 🏗️ **Arquitectura Hexagonal:** Código limpio y mantenible
- 📊 **Métricas Completas:** Tokens, costos, performance

---

## 📚 **Documentación**

### **🚀 Deployment y Producción**
- **[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)** - 🔥 Guía completa de deployment
- **[docs/ARCHIVOS_PARA_GITHUB.md](./docs/ARCHIVOS_PARA_GITHUB.md)** - Checklist de archivos
- **[docs/RESUMEN_LIMPIEZA.md](./docs/RESUMEN_LIMPIEZA.md)** - Optimizaciones realizadas
- **[docs/OPTIMIZACION_DOCKER_PRODUCCION.md](./docs/OPTIMIZACION_DOCKER_PRODUCCION.md)** - Plan de optimización

### **📖 Documentación Técnica**
- **[docs/RAG_ADAPTATIVO_GEMINI.md](./docs/RAG_ADAPTATIVO_GEMINI.md)** - Sistema RAG con Gemini
- **[docs/LLM_GATEWAY.md](./docs/LLM_GATEWAY.md)** - Gateway de modelos LLM
- **[docs/MEJORAS_HIBRIDO.md](./docs/MEJORAS_HIBRIDO.md)** - Sistema híbrido mejorado

### **🔧 Guías Adicionales**
- **[docs/GUIA_RAPIDA.md](./docs/GUIA_RAPIDA.md)** - Inicio rápido
- **[docs/APRENDIZAJE_GIT_DOCKER.md](./docs/APRENDIZAJE_GIT_DOCKER.md)** - Tutorial Git y Docker
- **[docs/DEPLOYMENT_SECURITY.md](./docs/DEPLOYMENT_SECURITY.md)** - Seguridad en producción

---

## 🏗️ **Arquitectura**

### **Arquitectura Hexagonal (Ports & Adapters)**

```
src/
├── domain/          # Lógica de negocio pura
├── application/     # Casos de uso
└── adapters/        # Implementaciones
    ├── api/        # FastAPI endpoints
    ├── db/         # Repositorios
    ├── agents/     # Clientes LLM
    ├── tools/      # Herramientas (Brave, Guardian)
    └── streamlit/  # Frontend
```

---

## 🤖 **Agentes y Routing LLM**

El sistema usa **routing configurable** — cambiás de proveedor desde el `.env` sin tocar código.

### **Proveedores disponibles**

| Proveedor | Variable | Modelos | Costo approx. |
|-----------|----------|---------|---------------|
| **Groq** (Kimi-K2) | `CHAT_PROVIDER=groq` | `moonshotai/kimi-k2-instruct-0905` | Gratis (rate limited) |
| **DeepSeek** | `CHAT_PROVIDER=deepseek` | `deepseek-chat`, `deepseek-reasoner` | $0.28/M input |
| **Gemini** | `CHAT_PROVIDER=gemini` | `gemini-2.5-flash` | Gratis (rate limited) |

### **Configuración de routing (.env)**

```env
# --- Routing LLM: cambiar proveedor sin código ---
CHAT_PROVIDER=deepseek          # Chat general: groq | deepseek | gemini
CHAT_MODEL=deepseek-chat       # Modelo para chat
RAG_PROVIDER=gemini             # RAG/PDFs: gemini | deepseek | groq
RAG_MODEL=gemini-2.5-flash     # Modelo para RAG
FALLBACK_PROVIDER=gemini       # Fallback si el principal falla: gemini | deepseek | groq | none
FALLBACK_MODEL=gemini-2.5-flash # Modelo de fallback

# --- API Keys (solo los providers que uses) ---
GROQ_API_KEY=gsk_xxx           # Obligatorio si CHAT_PROVIDER=groq
DEEPSEEK_API_KEY=sk-xxx        # Obligatorio si CHAT_PROVIDER=deepseek
GEMINI_API_KEY=AIzaxxx         # Obligatorio si RAG_PROVIDER=gemini o FALLBACK_PROVIDER=gemini
```

### **Ejemplos de routing**

| Configuración | Resultado |
|--------------|----------|
| `CHAT_PROVIDER=groq` + `RAG_PROVIDER=gemini` | Chat con Kimi-K2, PDFs con Gemini (config por defecto) |
| `CHAT_PROVIDER=deepseek` + `RAG_PROVIDER=gemini` | Chat con DeepSeek, PDFs con Gemini |
| `CHAT_PROVIDER=deepseek` + `FALLBACK_PROVIDER=deepseek` | DeepSeek para todo, DeepSeek como fallback |
| `FALLBACK_PROVIDER=none` | Sin fallback, error si el proveedor principal falla |

### **Costo estimado: DeepSeek como cache HIT**

Con `CHAT_PROVIDER=deepseek` + `FALLBACK_PROVIDER=gemini`:
- Respuestas cacheadas: ~$0.028/M tokens (prácticamente gratis)
- Respuestas nuevas: ~$0.28/M input, ~$0.88/M output
- Si DeepSeek falla: Gemini toma el relevo automáticamente

---

## 🛠️ **Tecnologías**

- **Backend:** FastAPI, SQLModel, PostgreSQL, pgvector
- **Frontend:** Streamlit, Plotly
- **IA:** Groq API (Kimi), Google Gemini API, DeepSeek API, HuggingFace/SiliconFlow
- **Infraestructura:** Docker, Gunicorn, Uvicorn

---

## 📊 **Estado del Proyecto**

✅ **Arquitectura Hexagonal** - Código limpio y mantenible
✅ **RAG con pgvector** - Búsqueda semántica en PDFs
✅ **Routing LLM Configurable** - DeepSeek, Groq, Gemini desde .env
✅ **JWT Auth** - Endpoints protegidos con autenticación
✅ **Brave Search** - Búsquedas Python especializadas
✅ **Guardian de Seguridad** - Protección contra ataques
✅ **Métricas Completas** - Tokens, costos, performance  

**Estado:** 🚀 **PRODUCTION READY**

---

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📝 **Licencia**

Este proyecto está bajo la licencia MIT.

---

## 👨‍💻 **Autor**

**Gonzalo Ponce**
- GitHub: [@Ponce1969](https://github.com/Ponce1969)
- Proyecto: [agente_hibrido_texto_Kimi_rag_Gemini](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini)

---

**⭐ Si te gusta este proyecto, dale una estrella en GitHub!**
