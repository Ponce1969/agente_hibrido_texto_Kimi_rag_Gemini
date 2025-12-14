# 📦 Archivos para Subir a GitHub - Checklist

## ✅ ARCHIVOS QUE DEBES SUBIR

### Configuración Docker (OPTIMIZADOS)
- [x] `Dockerfile` - **OPTIMIZADO** para producción (1.5GB vs 4.2GB)
- [x] `docker-compose.yml` - **CON LÍMITES** de recursos (2.3GB RAM máx)
- [x] `.dockerignore` - **NUEVO** - Reduce contexto de build

### Código Fuente
- [x] `src/` - Todo el código de la aplicación
- [x] `scripts/` - Scripts de utilidad
- [x] `.streamlit/` - Configuración de Streamlit

### Configuración
- [x] `gunicorn.conf.py` - Configuración del servidor
- [x] `pyproject.toml` - Dependencias Python
- [x] `uv.lock` - Lock file de dependencias
- [x] `.env.example` - **PLANTILLA** de variables de entorno (sin secretos)

### Documentación
- [x] `README.md` - Documentación principal
- [x] `DEPLOYMENT.md` - **NUEVO** - Guía de deployment
- [x] `ARCHIVOS_PARA_GITHUB.md` - Este archivo
- [x] `docs/` - Documentación adicional

### Scripts de Deployment
- [x] `deploy_orangepi5.sh` - Script de deployment (si aplica)

---

## ❌ ARCHIVOS QUE **NO** DEBES SUBIR

### Secretos y Configuración Local
- [ ] ~~`.env`~~ - **NUNCA** subir (contiene API keys y passwords)
- [ ] ~~`.env.local`~~ - Configuración local
- [ ] ~~`.env.*.local`~~ - Variantes locales

### Archivos Temporales y Cache
- [ ] ~~`.venv/`~~ - Entorno virtual local
- [ ] ~~`__pycache__/`~~ - Cache de Python
- [ ] ~~`.mypy_cache/`~~ - Cache de mypy
- [ ] ~~`.ruff_cache/`~~ - Cache de ruff
- [ ] ~~`.pytest_cache/`~~ - Cache de pytest
- [ ] ~~`*.pyc`, `*.pyo`, `*.pyd`~~ - Archivos compilados

### Datos y Uploads
- [ ] ~~`data/`~~ - Datos locales (se usan volúmenes Docker)
- [ ] ~~`uploads/`~~ - Archivos subidos por usuarios
- [ ] ~~`*.db`, `*.sqlite`~~ - Bases de datos locales
- [ ] ~~`test_llm_gateway_cache.db`~~ - Cache de tests

### Archivos Obsoletos
- [ ] ~~`Dockerfile.prod`~~ - Ya no se usa (optimizamos el principal)
- [ ] ~~`docker-compose.prod.yml`~~ - Ya no se usa (optimizamos el principal)

### IDEs y Editores
- [ ] ~~`.vscode/`~~ - Configuración de VS Code
- [ ] ~~`.idea/`~~ - Configuración de PyCharm
- [ ] ~~`*.swp`, `*.swo`~~ - Archivos temporales de vim

---

## 🔍 Verificar antes de hacer commit

```bash
# Ver qué archivos se van a subir
git status

# Ver qué archivos están siendo ignorados
git status --ignored

# Verificar que .env NO esté en la lista
git ls-files | grep .env
# Debe mostrar solo: .env.example

# Verificar que .dockerignore existe
ls -la .dockerignore
```

---

## 📋 Comandos Git Recomendados

### Primera vez (nuevo repositorio)

```bash
# Inicializar git (si no está inicializado)
git init

# Agregar archivos
git add .

# Verificar qué se va a subir
git status

# Hacer commit
git commit -m "Optimización Docker para producción - Reducción de 64% en tamaño"

# Agregar remote (reemplaza con tu URL)
git remote add origin https://github.com/tu-usuario/tu-repo.git

# Subir a GitHub
git push -u origin main
```

### Actualización (repositorio existente)

```bash
# Ver cambios
git status

# Agregar archivos modificados
git add Dockerfile docker-compose.yml .dockerignore DEPLOYMENT.md

# Commit con mensaje descriptivo
git commit -m "feat: Optimizar Docker para producción

- Reducir tamaño de imágenes de 4.2GB a ~1.5GB (-64%)
- Agregar límites de recursos (2.3GB RAM máx)
- Implementar .dockerignore
- Documentar proceso de deployment
- Optimizar configuración de PostgreSQL"

# Subir cambios
git push origin main
```

---

## 🎯 Optimizaciones Implementadas

### Dockerfile
✅ Multi-stage build optimizado
✅ Solo dependencias de producción (`--no-dev`)
✅ Limpieza agresiva de caches
✅ Variables de optimización Python
✅ Optimizaciones de ML/transformers

### docker-compose.yml
✅ Límites de CPU y RAM configurados
✅ Health checks optimizados
✅ Dependencias entre servicios
✅ PostgreSQL optimizado
✅ Sin volúmenes de código en producción

### .dockerignore
✅ Excluye archivos innecesarios
✅ Reduce contexto de build
✅ Acelera construcción de imágenes

---

## 📊 Resultados Esperados

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Tamaño Backend | 4.2GB | ~1.5GB | **-64%** |
| Tamaño Frontend | 4.2GB | ~1.5GB | **-64%** |
| RAM Total | Ilimitado | 2.3GB máx | **Control** |
| Tiempo Build | ~30 min | ~15 min | **-50%** |
| Costo Servidor | $X/mes | ~$X/2 mes | **~-50%** |

---

## 🚀 Siguiente Paso: Deployment

Después de subir a GitHub:

1. **SSH al servidor**
   ```bash
   ssh usuario@servidor.com
   ```

2. **Clonar/Actualizar repositorio**
   ```bash
   git clone https://github.com/tu-usuario/tu-repo.git
   # o si ya existe:
   cd tu-repo && git pull
   ```

3. **Configurar .env**
   ```bash
   cp .env.example .env
   nano .env  # Agregar API keys reales
   ```

4. **Construir y levantar**
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

5. **Verificar**
   ```bash
   docker compose ps
   docker stats
   ```

Ver `DEPLOYMENT.md` para más detalles.

---

**Última actualización**: 14 de Diciembre, 2025 - 17:20
