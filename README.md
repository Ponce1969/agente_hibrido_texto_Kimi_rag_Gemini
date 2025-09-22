# 🤖 Asistente de Aprendizaje de Python con IA

## 📚 **Documentación Principal**
> **🚀 Para información completa y actualizada, consulta la [documentación organizada](./doc/README.md)**

### **📖 Documentación Disponible**
- **[`doc/IMPLEMENTATION.md`](./doc/IMPLEMENTATION.md)** - Estado actual del proyecto
- **[`doc/ROADMAP.md`](./doc/ROADMAP.md)** - Próximos pasos y fases pendientes
- **[`doc/ARCHITECTURE_IMPROVEMENTS.md`](./doc/ARCHITECTURE_IMPROVEMENTS.md)** - Mejoras arquitectónicas
- **[`doc/PROJECT_OVERVIEW.md`](./doc/PROJECT_OVERVIEW.md)** - Introducción para nuevos desarrolladores

---

## 🎯 **Inicio Rápido (Versión Resumida)**

### **Instalación**
```bash
# Instalar dependencias
uv sync

# Lanzar con Docker
docker-compose up --build
```

### **Acceso**
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

### **Configuración**
Crear archivo `.env` con las API keys:
```env
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

---

## 📊 **Estado del Proyecto**

| Categoría | Puntuación | Estado |
|-----------|------------|---------|
| **Funcionalidad** | 85% | ✅ Casi completo |
| **Arquitectura** | 9/10 | ✅ Excelente |
| **Calidad** | 9/10 | ✅ Excelente |
| **Testing** | 2/10 | ❌ Necesario |

**Puntuación Global: 8.3/10** - **Proyecto muy sólido** 🚀

---

## 🚀 **Características Principales**

- 🤖 **5 Agentes IA especializados** en Python
- 📄 **Procesamiento de documentos PDF** con contexto
- 💬 **Chat persistente** con historial completo
- 🏗️ **Arquitectura hexagonal** escalable
- 🐳 **Despliegue Docker** completo

---

## 📝 **Historial del Proyecto**

Este proyecto se ha desarrollado siguiendo un **plan estructurado** documentado en [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).

### **Fases Completadas**
- ✅ **Fases 1-5**: Completamente implementadas (85% del proyecto)
- ✅ **Arquitectura**: Hexagonal bien implementada
- ✅ **Funcionalidades**: Todas las características principales funcionando

### **Próximos Pasos**
- 📋 **Fase 6**: Lanzamiento y pruebas (pendiente)
- 🔮 **Fase 7**: RAG avanzado (planificado)

---

## 🎯 **Para Desarrolladores**

### **Stack Tecnológico**
- **Backend**: FastAPI 0.110+ | **UI**: Streamlit 1.32+
- **Base de Datos**: SQLite + SQLModel | **IA**: Groq + Gemini
- **DevOps**: Docker + uv | **Calidad**: ruff + mypy

### **Comandos de Desarrollo**
```bash
# Dependencias
uv sync --dev

# Testing (próximamente)
pytest

# Calidad de código
ruff check src/
mypy src/

# Lanzamiento
docker-compose up --build
```

---

## 📞 **Soporte y Contribución**

### **Para información detallada:**
- Consulta la **[documentación completa](./doc/README.md)**
- Revisa el **[estado actual](./doc/IMPLEMENTATION.md)**
- Consulta el **[roadmap](./doc/ROADMAP.md)**

### **Contribuciones:**
1. Lee la **[guía de arquitectura](./doc/ARCHITECTURE_IMPROVEMENTS.md)**
2. Sigue las **[convenciones de código](./doc/PROJECT_OVERVIEW.md)**
3. Actualiza la **[documentación](./doc/)** según cambios

---

## 🎉 **Conclusión**

Este proyecto representa un **asistente de IA moderno** para el aprendizaje de Python, con una **base técnica sólida** y **arquitectura escalable**.

**Estado**: Listo para desarrollo activo y pruebas de usuario.

**Documentación**: Completa y organizada en [`./doc/`](./doc/)

---

**🎯 Para información completa, consulta la [documentación principal](./doc/README.md)**

*Este README sirve como punto de entrada. Para información detallada y actualizada, consulta la documentación en `doc/`. Última actualización: Septiembre 2025*
