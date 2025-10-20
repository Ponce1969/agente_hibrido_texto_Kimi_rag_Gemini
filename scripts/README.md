# 🛠️ Scripts de Utilidad

> **Colección organizada de scripts para desarrollo, testing, deployment y mantenimiento del proyecto.**

---

## 📂 **Estructura**

```
scripts/
├── deployment/      # 🚀 Scripts de deployment y producción
├── database/        # 💾 Scripts de base de datos
├── development/     # 🏗️ Scripts de desarrollo
├── testing/         # 🧪 Scripts de testing
└── utils/           # 🔧 Utilidades generales
```

---

## 🚀 **Deployment**

### **`deployment/start_dev.sh`**
Inicia el servidor en modo desarrollo con hot-reload.

```bash
./scripts/deployment/start_dev.sh
```

**Características:**
- Uvicorn con hot-reload
- 1 worker (single process)
- Ideal para desarrollo local
- Recarga automática al cambiar código

---

### **`deployment/start_prod.sh`**
Inicia el servidor en modo producción con Gunicorn.

```bash
./scripts/deployment/start_prod.sh
```

**Características:**
- Gunicorn + Uvicorn workers
- 4 workers (multi-process)
- Gestión robusta de procesos
- Auto-restart en crashes

---

### **`deployment/cleanup_for_production.sh`**
Limpia el proyecto antes de deployment a producción.

```bash
bash scripts/deployment/cleanup_for_production.sh
```

**Acciones:**
- Elimina cachés de Python (`__pycache__`, `.pytest_cache`)
- Organiza archivos de desarrollo
- Verifica configuración de seguridad
- Muestra resumen de limpieza

---

## 💾 **Base de Datos**

### **`database/check_db_tables.sh`**
Verifica las tablas de la base de datos.

```bash
bash scripts/database/check_db_tables.sh
```

**Verifica:**
- Tablas existentes
- Estructura de columnas
- Índices
- Relaciones

---

### **`database/verify_tables.sql`**
Script SQL para verificar la estructura de tablas.

```bash
psql -U user -d db -f scripts/database/verify_tables.sql
```

---

### **`database/clean_empty_sessions.py`**
Limpia sesiones vacías de la base de datos.

```bash
uv run python scripts/database/clean_empty_sessions.py
```

**Acciones:**
- Elimina sesiones sin mensajes
- Libera espacio en BD
- Mantiene integridad referencial

---

### **`database/clear_error_message.py`**
Limpia mensajes de error en archivos indexados.

```bash
uv run python scripts/database/clear_error_message.py
```

**Uso:**
- Limpia error_message de archivos con status "ready" o "indexed"
- Actualiza timestamp de modificación

---

### **`database/migrate_embeddings_dimension.py`**
Migra embeddings de una dimensión a otra.

```bash
uv run python scripts/database/migrate_embeddings_dimension.py
```

**Casos de uso:**
- Cambiar de modelo de embeddings
- Actualizar dimensiones (384 → 768)
- Reindexar documentos

---

## 🏗️ **Desarrollo**

### **`development/check_hexagonal_architecture.py`**
Verifica que el proyecto respete los principios de arquitectura hexagonal.

```bash
uv run python scripts/development/check_hexagonal_architecture.py
```

**Verifica:**
- ✅ Pureza del dominio (no importa adapters)
- ✅ Dirección de dependencias correcta
- ✅ Ubicación de puertos en `domain/ports/`
- ✅ Fuga de frameworks (FastAPI, SQLModel solo en adapters)

**Salida:**
- ❌ Errores críticos (deben corregirse)
- ⚠️ Advertencias (mejoras recomendadas)
- ℹ️ Información (sugerencias menores)

---

### **`development/analyze_architecture.py`**
Analiza la arquitectura del proyecto y genera reportes.

```bash
uv run python scripts/development/analyze_architecture.py
```

**Genera:**
- Métricas de complejidad
- Dependencias entre módulos
- Violaciones de SOLID
- Recomendaciones de refactoring

---

### **`development/cleanup_project.py`**
Analiza el proyecto buscando archivos a limpiar.

```bash
uv run python scripts/development/cleanup_project.py
```

**Identifica:**
- Archivos de caché
- Archivos de desarrollo mal ubicados
- Backups obsoletos
- Carpetas vacías
- Archivos temporales

---

### **`development/find_duplicates.py`**
Encuentra archivos duplicados por contenido y nombres similares.

```bash
uv run python scripts/development/find_duplicates.py
```

**Detecta:**
- Archivos duplicados por contenido (mismo hash MD5)
- Archivos con nombres similares
- Calcula espacio desperdiciado
- Sugiere qué archivos revisar/eliminar

---

### **`development/check_dependencies.py`**
Verifica las dependencias del proyecto.

```bash
uv run python scripts/development/check_dependencies.py
```

**Verifica:**
- Dependencias instaladas
- Versiones compatibles
- Dependencias faltantes
- Dependencias obsoletas

---

## 🧪 **Testing**

### **`testing/test_rag.py`**
Prueba el sistema RAG con consultas de ejemplo.

```bash
uv run python scripts/testing/test_rag.py
```

**Prueba:**
- Indexación de documentos
- Búsqueda semántica
- Generación de respuestas
- Performance de embeddings

---

### **`testing/debug_rag_flow.py`**
Debuggea el flujo completo del sistema RAG.

```bash
uv run python scripts/testing/debug_rag_flow.py
```

**Muestra:**
- Paso a paso del flujo RAG
- Embeddings generados
- Chunks recuperados
- Contexto enviado al LLM
- Respuesta final

---

### **`testing/demo_token_savings.py`**
Demuestra el ahorro de tokens con el sistema de caché.

```bash
uv run python scripts/testing/demo_token_savings.py
```

**Compara:**
- Consultas sin caché
- Consultas con caché
- Ahorro de tokens
- Ahorro de costos

---

## 🔧 **Utilidades**

### **`utils/generate_secret_key.py`**
Genera una clave secreta segura para JWT.

```bash
uv run python scripts/utils/generate_secret_key.py
```

**Genera:**
- Clave secreta de 32 bytes
- Codificada en base64
- Lista para usar en `.env`

---

### **`utils/verify_deployment.py`**
Verifica que el deployment esté funcionando correctamente.

```bash
uv run python scripts/utils/verify_deployment.py
```

**Verifica:**
- Backend respondiendo
- Frontend accesible
- Base de datos conectada
- Servicios externos (APIs)
- Health checks

---

## 📊 **Integración con CI/CD**

### **GitHub Actions**

Ejemplo de workflow para verificar arquitectura:

```yaml
# .github/workflows/architecture-check.yml
name: Architecture Check

on: [push, pull_request]

jobs:
  check-architecture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Check Architecture
        run: uv run python scripts/development/check_hexagonal_architecture.py
```

---

## 🔒 **Seguridad**

**IMPORTANTE:** Estos scripts NO contienen credenciales ni información sensible.

- ✅ Seguros para subir a GitHub
- ✅ No acceden a `.env` directamente
- ✅ Solo leen código fuente y estructura
- ✅ No exponen datos sensibles en logs

---

## 🚀 **Uso Rápido**

### **Desarrollo**
```bash
# Iniciar en modo desarrollo
./scripts/deployment/start_dev.sh

# Verificar arquitectura
uv run python scripts/development/check_hexagonal_architecture.py

# Encontrar duplicados
uv run python scripts/development/find_duplicates.py
```

### **Testing**
```bash
# Probar RAG
uv run python scripts/testing/test_rag.py

# Debug RAG flow
uv run python scripts/testing/debug_rag_flow.py
```

### **Producción**
```bash
# Limpiar proyecto
bash scripts/deployment/cleanup_for_production.sh

# Iniciar en producción
./scripts/deployment/start_prod.sh

# Verificar deployment
uv run python scripts/utils/verify_deployment.py
```

### **Base de Datos**
```bash
# Limpiar sesiones vacías
uv run python scripts/database/clean_empty_sessions.py

# Verificar tablas
bash scripts/database/check_db_tables.sh
```

---

## 📝 **Contribuir**

Si creas un nuevo script:

1. **Colócalo en la carpeta apropiada:**
   - `deployment/` - Scripts de deployment
   - `database/` - Scripts de BD
   - `development/` - Scripts de desarrollo
   - `testing/` - Scripts de testing
   - `utils/` - Utilidades generales

2. **Documenta su propósito:**
   - Agrega una sección en este README
   - Incluye ejemplos de uso
   - Indica requisitos especiales

3. **Sigue las convenciones:**
   - Nombres descriptivos en snake_case
   - Shebang apropiado (`#!/usr/bin/env python3` o `#!/bin/bash`)
   - Comentarios claros en el código

---

## 🆘 **Soporte**

Si tienes problemas con algún script:

1. Verifica que estás en el directorio raíz del proyecto
2. Asegúrate de tener las dependencias instaladas (`uv sync`)
3. Revisa la documentación en `doc/`
4. Consulta los logs de error
5. Verifica permisos de ejecución (`chmod +x script.sh`)

---

## 📚 **Documentación Relacionada**

- **[doc/README.md](../doc/README.md)** - Documentación completa del proyecto
- **[doc/GUIA_RAPIDA.md](../doc/GUIA_RAPIDA.md)** - Inicio rápido
- **[doc/DEPLOY_MANUAL.md](../doc/DEPLOY_MANUAL.md)** - Guía de deployment

---

**Última actualización:** 2025-10-19  
**Mantenedor:** Gonzalo Ponce
