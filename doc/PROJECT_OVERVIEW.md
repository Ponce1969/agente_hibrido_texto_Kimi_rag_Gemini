# 📖 Descripción General del Proyecto

## 🎯 ¿Qué es este proyecto?

**Asistente de Aprendizaje de Python con IA** es una aplicación web moderna que utiliza inteligencia artificial para ayudar a desarrolladores y estudiantes de Python en su proceso de aprendizaje y desarrollo.

### **Características Principales**
- 🤖 **5 Agentes IA Especializados** en diferentes áreas de Python
- 📄 **Procesamiento de Documentos PDF** con integración contextual
- 💬 **Chat Persistente** con historial de conversaciones
- 🚀 **Arquitectura Escalable** lista para crecimiento
- 🐳 **Despliegue en Docker** completo y optimizado

---

## 🚀 **Inicio Rápido**

### **1. Instalación y Configuración**
```bash
# Clonar el proyecto
git clone <repository-url>
cd agentes_Front_Bac

# Instalar dependencias con uv
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### **2. Variables de Entorno Requeridas**
```env
# API Keys para IA
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Configuración de Base de Datos
DB_BACKEND=sqlite

# Configuración de Archivos
FILE_CONTEXT_MAX_CHARS=6000
MESSAGES_MAX_CHARS=10000
```

### **3. Lanzar la Aplicación**
```bash
# Con Docker (recomendado)
docker-compose up --build

# Sin Docker (desarrollo)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
streamlit run src/adapters/streamlit/app.py
```

### **4. Acceder a la Aplicación**
- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

---

## 🏗️ **Arquitectura del Proyecto**

### **Patrón Arquitectónico: Hexagonal**
```
src/
├── domain/          # Reglas de negocio puras
├── application/     # Casos de uso y lógica de aplicación
└── adapters/        # Interfaces externas (API, DB, UI, IA)
```

### **Componentes Principales**

#### **1. Backend (FastAPI)**
- **Framework**: FastAPI 0.110+
- **Endpoints**: REST API moderna y tipada
- **Middleware**: Errores, CORS, autenticación futura
- **Documentación**: OpenAPI automática

#### **2. Base de Datos (SQLite)**
- **ORM**: SQLModel (SQLAlchemy 2.0)
- **Modelos**: Sesiones, Mensajes, Archivos
- **Persistencia**: Historial completo de chats
- **Índices**: Optimizados para consultas frecuentes

#### **3. Agentes de IA**
- **Proveedor Principal**: Groq (kimi-k2-instruct)
- **Fallback**: Google Gemini (gemini-2.5-flash)
- **Especializaciones**: 5 roles técnicos diferentes

#### **4. Interfaz de Usuario (Streamlit)**
- **Framework**: Streamlit 1.32+
- **Características**: Chat, subida de archivos, navegación
- **Responsive**: Funciona en desktop y mobile

---

## 🤖 **Los 5 Agentes Especializados**

### **1. Arquitecto Python Senior**
```
"Arquitecto de software senior especializado en Python 3.12+,
con más de 15 años de experiencia en arquitectura de software."
```
- **Enfoque**: Clean Architecture, SOLID, DDD
- **Stack**: FastAPI, SQLAlchemy, patrones avanzados

### **2. Ingeniero de Código**
```
"Ingeniero de código cualificado, especializado en generar
soluciones Python modernas y eficientes."
```
- **Enfoque**: Código limpio, moderno, eficiente
- **Stack**: FastAPI, Pydantic, async/await

### **3. Auditor de Seguridad**
```
"Auditor de seguridad senior especializado en la identificación
y mitigación de vulnerabilidades en aplicaciones Python."
```
- **Enfoque**: OWASP Top 10, vulnerabilidades comunes
- **Stack**: Análisis de seguridad, mejores prácticas

### **4. Especialista en Bases de Datos**
```
"Especialista en bases de datos con experiencia en diseño,
optimización y mantenimiento de sistemas de datos."
```
- **Enfoque**: SQL, optimización, modelado de datos
- **Stack**: SQLAlchemy, PostgreSQL, SQLite

### **5. Ingeniero de Refactoring**
```
"Ingeniero especializado en mejorar código existente mediante
refactoring y optimización de rendimiento."
```
- **Enfoque**: Código legacy, optimización, mantenibilidad
- **Stack**: Análisis estático, patrones de diseño

---

## 📄 **Procesamiento de Documentos**

### **Funcionalidad**
- 📤 **Subida de PDFs** con validación de tamaño y tipo
- ✂️ **Segmentación Automática** por secciones y páginas
- 🧠 **Integración Contextual** en las conversaciones
- 💾 **Persistencia** de metadatos y estructura

### **Flujo de Trabajo**
1. Usuario sube un PDF
2. Sistema procesa y segmenta el documento
3. Extrae texto de cada sección
4. Almacena metadatos en base de datos
5. Integra contexto en respuestas de IA

---

## 🔧 **Tecnologías Utilizadas**

### **Core Stack**
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.12+ | Lenguaje principal |
| FastAPI | 0.110+ | API Backend |
| Streamlit | 1.32+ | UI Frontend |
| SQLModel | 0.0.24 | ORM y modelos |

### **IA y Machine Learning**
| Servicio | Modelo | Uso |
|----------|---------|-----|
| Groq | kimi-k2-instruct | Agente principal |
| Google Gemini | gemini-2.5-flash | Fallback y PDFs |
| PyPDF | 4.2.0 | Procesamiento PDF |

### **DevOps y Herramientas**
| Herramienta | Propósito |
|-------------|-----------|
| uv | Gestión de dependencias |
| Docker | Contenerización |
| ruff | Linting y formateo |
| mypy | Type checking |

---

## 📊 **Estado del Proyecto**

### **Funcionalidades Implementadas (85%)**
- ✅ **Sistema de chat multi-agente** completo
- ✅ **Procesamiento de documentos PDF** funcional
- ✅ **API REST completa** con validación
- ✅ **Interfaz web moderna** y responsive
- ✅ **Arquitectura hexagonal** bien estructurada
- ✅ **Despliegue Docker** optimizado

### **Pendiente para Versión 1.0**
- ⚠️ **Sistema de testing** robusto
- ⚠️ **Documentación API** completa
- ⚠️ **Domain layer** completo
- 📋 **RAG avanzado** (PostgreSQL + embeddings)

---

## 🎯 **Casos de Uso Principales**

### **1. Aprendizaje de Python**
- Consultas sobre sintaxis y mejores prácticas
- Explicación de conceptos avanzados
- Revisión de código y sugerencias

### **2. Desarrollo de Proyectos**
- Generación de código boilerplate
- Arquitectura y diseño de sistemas
- Debugging y troubleshooting

### **3. Análisis de Documentos**
- Consultas sobre PDFs técnicos
- Extracción de información específica
- Síntesis de contenido largo

### **4. Revisión de Código**
- Análisis de seguridad
- Optimización de performance
- Mejores prácticas de refactoring

---

## 🚀 **Cómo Contribuir**

### **1. Entender la Arquitectura**
```bash
# Revisar la documentación
cat doc/IMPLEMENTATION.md    # Estado actual
cat doc/ROADMAP.md          # Próximos pasos
cat doc/ARCHITECTURE_IMPROVEMENTS.md  # Mejoras pendientes
```

### **2. Configurar Entorno de Desarrollo**
```bash
# Instalar dependencias
uv sync --dev

# Configurar pre-commit hooks
pre-commit install

# Ejecutar tests (cuando estén implementados)
pytest
```

### **3. Estructura para Nuevas Features**
```python
# 1. Domain layer (lógica pura)
src/domain/services/nueva_feature_service.py

# 2. Application layer (orquestación)
src/application/services/nueva_feature_service.py

# 3. Adapters (interfaces externas)
src/adapters/api/endpoints/nueva_feature.py
src/adapters/db/nueva_feature_repository.py
```

### **4. Convenciones de Código**
- **Type hints** obligatorios (mypy strict)
- **Docstrings** para todas las funciones públicas
- **Testing** para lógica de negocio
- **Logging** estructurado para debugging

---

## 📚 **Recursos y Documentación**

### **Documentación Interna**
- 📄 `doc/IMPLEMENTATION.md` - Estado actual del proyecto
- 🗺️ `doc/ROADMAP.md` - Plan de desarrollo y fases
- 🏗️ `doc/ARCHITECTURE_IMPROVEMENTS.md` - Mejoras pendientes
- 📋 `IMPLEMENTATION_PLAN.md` - Plan original de implementación

### **Documentación Externa**
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Streamlit Docs**: https://docs.streamlit.io/
- **Groq API**: https://console.groq.com/docs
- **Gemini API**: https://ai.google.dev/docs

---

## 🤝 **Soporte y Contacto**

### **Issues y Bugs**
- Reportar bugs en el issue tracker
- Incluir logs y pasos para reproducir
- Especificar versión y entorno

### **Feature Requests**
- Crear issue con etiqueta "enhancement"
- Describir caso de uso y valor esperado
- Incluir ejemplos si es posible

### **Contribuciones**
- Fork el proyecto
- Crear branch para nueva feature
- Seguir convenciones de código
- Abrir Pull Request con descripción detallada

---

## 📈 **Métricas y Analytics**

### **Métricas Técnicas**
- **Tiempo de respuesta**: <2s para respuestas de IA
- **Uptime**: 99.5% objetivo
- **Throughput**: 100 requests/minuto
- **Error rate**: <1%

### **Métricas de Uso**
- **Sesiones activas**: Tracking de usuarios
- **Mensajes por sesión**: Análisis de engagement
- **Archivos procesados**: Métricas de documentos
- **Uso de agentes**: Popularidad por especialización

---

## 🎉 **Conclusión**

Este proyecto representa un **asistente de IA moderno y bien arquitecturado** para el aprendizaje de Python. Combina **tecnología de vanguardia** con **buenas prácticas de desarrollo** y una **arquitectura escalable**.

**Estado actual**: Listo para desarrollo activo y pruebas de usuario.

**Próximos pasos**: Completar testing, mejorar documentación, y avanzar hacia RAG avanzado.

---

**¡Bienvenido al proyecto! 🚀**

*Este documento se actualiza regularmente. Última revisión: Septiembre 2025*
