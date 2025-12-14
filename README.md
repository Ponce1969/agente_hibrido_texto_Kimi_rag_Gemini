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

- 🤖 **3 Agentes IA:** Kimi-K2, Gemini 2.5 Flash, Guardian Qwen2.5-1.5B
- 📚 **RAG con pgvector:** Consulta PDFs con búsqueda semántica
- 🌐 **Brave Search:** Búsquedas Python especializadas
- 🛡️ **Guardian de Seguridad:** Protección contra prompt injection y jailbreak
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

## 🤖 **Agentes**

| Agente | Modelo | Uso |
|--------|--------|-----|
| **Kimi-K2** | `moonshotai/kimi-k2-instruct-0905` | Chat general + Brave Search |
| **Gemini 2.5 Flash** | `gemini-2.5-flash` | RAG con PDFs |
| **Guardian** | `Qwen/Qwen2.5-1.5B-Instruct` | Seguridad |

**+ 5 Agentes de Rol:**
- Arquitecto Python Senior
- Ingeniero de Código
- Auditor de Seguridad
- Especialista en Bases de Datos
- Ingeniero de Refactoring

---

## 🛠️ **Tecnologías**

- **Backend:** FastAPI, SQLModel, PostgreSQL, pgvector
- **Frontend:** Streamlit, Plotly
- **IA:** Groq API (Kimi), Google Gemini API, HuggingFace/SiliconFlow
- **Infraestructura:** Docker, Gunicorn, Uvicorn

---

## 📊 **Estado del Proyecto**

✅ **Arquitectura Hexagonal** - Código limpio y mantenible  
✅ **RAG con pgvector** - Búsqueda semántica en PDFs  
✅ **Brave Search** - Búsquedas Python especializadas  
✅ **Guardian de Seguridad** - Protección contra ataques  
✅ **Métricas Completas** - Tokens, costos, performance  
✅ **Documentación Profesional** - README completo  

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
