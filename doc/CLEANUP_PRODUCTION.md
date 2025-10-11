# 🧹 Plan de Limpieza para Producción

**Fecha:** 2025-10-10  
**Proyecto:** Agentes Front-Back (Sistema RAG Híbrido)

---

## 📋 Resumen

Este documento detalla los archivos y carpetas que deben limpiarse antes de llevar el proyecto a producción.

---

## 🗑️ Archivos a Eliminar (Prioridad Alta)

### 1. Cachés de Python
```bash
# Eliminar todos los cachés
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null
find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null
find . -type d -name '.ruff_cache' -exec rm -rf {} + 2>/dev/null
find . -type f -name '*.pyc' -delete
```

### 2. Archivos compilados
```bash
find . -type f -name '*.pyo' -delete
find . -type f -name '*.pyd' -delete
```

---

## 📦 Archivos a Revisar (Prioridad Media)

### 1. Scripts de desarrollo en raíz

**Archivos:**
- `activate.sh` - Script de activación del entorno
- `check_dependencies.py` - Verificación de dependencias
- `verify_deployment.py` - Verificación de deployment

**Acción recomendada:** Mover a `scripts/` o eliminar si ya no se usan

```bash
# Mover a scripts/
mv activate.sh scripts/
mv check_dependencies.py scripts/
mv verify_deployment.py scripts/
```

### 2. Documentación de desarrollo en raíz

**Archivos:**
- `IMPLEMENTATION_PLAN.md`
- `REFACTORING_COMPLETE.md`
- `TESTING_SUMMARY.md`

**Acción recomendada:** Mover a `doc/`

```bash
# Mover a doc/
mv IMPLEMENTATION_PLAN.md doc/
mv REFACTORING_COMPLETE.md doc/
mv TESTING_SUMMARY.md doc/
```

### 3. Backup obsoleto

**Carpeta:** `backup_obsoletos_20251006_224158/`

**Acción recomendada:** Eliminar si ya no es necesario

```bash
# Revisar contenido primero
ls -la backup_obsoletos_20251006_224158/

# Si no es necesario, eliminar
rm -rf backup_obsoletos_20251006_224158/
```

### 4. Carpetas vacías

**Carpetas:**
- `uploads/` - Puede estar vacía
- `data/` - Puede contener solo archivos de desarrollo

**Acción recomendada:** Verificar contenido

```bash
# Verificar uploads/
ls -la uploads/

# Verificar data/
ls -la data/
```

---

## 📝 Archivos a Mantener

### ✅ Archivos esenciales en raíz

- `README.md` - Documentación principal
- `.env` - Configuración (NO subir a Git)
- `.gitignore` - Control de versiones
- `docker-compose.yml` - Orquestación
- `Dockerfile` - Imagen Docker
- `pyproject.toml` - Configuración del proyecto
- `uv.lock` - Lock de dependencias
- `pytest.ini` - Configuración de tests

### ✅ Carpetas esenciales

- `src/` - Código fuente
- `tests/` - Tests
- `scripts/` - Scripts de utilidad
- `doc/` - Documentación
- `pages/` - Páginas de Streamlit
- `.venv/` - Entorno virtual (NO subir a Git)
- `.git/` - Control de versiones

---

## 🔧 Comandos de Limpieza Completa

```bash
# 1. Limpiar cachés de Python
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null
find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null
find . -type f -name '*.pyc' -delete

# 2. Mover scripts de desarrollo
mkdir -p scripts/dev
mv activate.sh scripts/dev/ 2>/dev/null
mv check_dependencies.py scripts/dev/ 2>/dev/null
mv verify_deployment.py scripts/dev/ 2>/dev/null

# 3. Mover documentación de desarrollo
mv IMPLEMENTATION_PLAN.md doc/ 2>/dev/null
mv REFACTORING_COMPLETE.md doc/ 2>/dev/null
mv TESTING_SUMMARY.md doc/ 2>/dev/null

# 4. Eliminar backup obsoleto (después de revisar)
# rm -rf backup_obsoletos_20251006_224158/

# 5. Verificar .gitignore
cat .gitignore
```

---

## 📊 Estructura Final Recomendada

```
agentes_Front_Bac/
├── .env                    # Configuración (NO en Git)
├── .gitignore
├── README.md
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── pytest.ini
├── src/                    # Código fuente
│   ├── adapters/
│   ├── application/
│   └── domain/
├── tests/                  # Tests
├── scripts/                # Scripts de utilidad
│   ├── dev/               # Scripts de desarrollo
│   ├── cleanup_project.py
│   ├── check_hexagonal_architecture.py
│   └── clear_error_message.py
├── doc/                    # Documentación
│   ├── ARQUITECTURE_VIOLATIONS_REPORT.md
│   ├── CLEANUP_PRODUCTION.md
│   └── ... (otros docs)
├── pages/                  # Streamlit pages
├── data/                   # Datos (SQLite, etc.)
└── uploads/                # Archivos subidos
```

---

## ✅ Checklist Pre-Producción

### Código

- [ ] Eliminar cachés de Python
- [ ] Eliminar archivos compilados
- [ ] Mover scripts de desarrollo a `scripts/dev/`
- [ ] Mover documentación de desarrollo a `doc/`
- [ ] Eliminar backups obsoletos
- [ ] Verificar que no hay archivos temporales

### Configuración

- [ ] Verificar `.env` (NO debe estar en Git)
- [ ] Actualizar `.gitignore`
- [ ] Verificar `docker-compose.yml` para producción
- [ ] Verificar variables de entorno en producción

### Seguridad

- [ ] Eliminar API keys de prueba
- [ ] Verificar que `.env` no está en Git
- [ ] Revisar logs para información sensible
- [ ] Actualizar contraseñas de producción

### Documentación

- [ ] Actualizar `README.md`
- [ ] Documentar variables de entorno requeridas
- [ ] Documentar proceso de deployment
- [ ] Crear guía de troubleshooting

### Testing

- [ ] Ejecutar todos los tests: `uv run pytest`
- [ ] Verificar arquitectura: `uv run python scripts/check_hexagonal_architecture.py`
- [ ] Probar endpoints críticos
- [ ] Verificar RAG con PDFs

### Docker

- [ ] Build de imágenes: `docker compose build`
- [ ] Verificar volúmenes persistentes
- [ ] Verificar networking entre contenedores
- [ ] Probar restart automático

---

## 🚀 Comandos de Deployment

```bash
# 1. Limpieza completa
bash scripts/cleanup_for_production.sh

# 2. Verificar tests
uv run pytest -v

# 3. Verificar arquitectura
uv run python scripts/check_hexagonal_architecture.py

# 4. Build Docker
docker compose build

# 5. Levantar servicios
docker compose up -d

# 6. Verificar logs
docker compose logs -f backend
docker compose logs -f frontend

# 7. Health check
curl http://localhost:8000/health
curl http://localhost:8501
```

---

## ⚠️ Advertencias

1. **Backup antes de eliminar**: Siempre haz backup antes de eliminar archivos
2. **Revisar .env**: Asegúrate de que las variables de entorno están correctas
3. **No eliminar .venv**: Es necesario para desarrollo local
4. **Verificar Git**: Usa `git status` para ver qué archivos están trackeados

---

## 📞 Soporte

Si tienes dudas sobre qué eliminar:
1. Revisa el contenido del archivo/carpeta
2. Verifica si está en `.gitignore`
3. Haz backup si no estás seguro
4. Consulta la documentación en `doc/`

---

**Última actualización:** 2025-10-10  
**Responsable:** Script de limpieza automática
