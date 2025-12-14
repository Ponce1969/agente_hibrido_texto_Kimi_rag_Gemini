# 🚀 Guía de Deployment a Producción

## 📦 Archivos que DEBES subir a GitHub

### ✅ Archivos Esenciales para Producción

```
proyecto/
├── src/                          # ✅ TODO el código fuente
├── scripts/                      # ✅ Scripts de utilidad
├── .streamlit/                   # ✅ Configuración de Streamlit
├── Dockerfile                    # ✅ Dockerfile OPTIMIZADO (ya actualizado)
├── docker-compose.yml            # ✅ Compose para producción
├── gunicorn.conf.py             # ✅ Configuración de Gunicorn
├── pyproject.toml               # ✅ Dependencias Python
├── uv.lock                      # ✅ Lock file de dependencias
├── .dockerignore                # ✅ Excluir archivos del build
├── .env.example                 # ✅ Ejemplo de variables de entorno
├── README.md                    # ✅ Documentación
└── deploy_orangepi5.sh          # ✅ Script de deployment (si aplica)
```

### ❌ Archivos que NO debes subir a GitHub

```
❌ .env                          # Contiene secretos (API keys, passwords)
❌ .venv/                        # Entorno virtual local
❌ __pycache__/                  # Cache de Python
❌ *.pyc, *.pyo                  # Archivos compilados
❌ data/                         # Datos locales
❌ uploads/                      # Archivos subidos por usuarios
❌ *.db, *.sqlite                # Bases de datos locales
❌ .mypy_cache/                  # Cache de mypy
❌ .ruff_cache/                  # Cache de ruff
❌ Dockerfile.prod               # Ya no se usa (optimizamos Dockerfile principal)
❌ docker-compose.prod.yml       # Ya no se usa (optimizamos docker-compose.yml principal)
```

---

## 🔧 Proceso de Deployment en el Servidor

### Paso 1: Clonar el repositorio en el servidor

```bash
# SSH al servidor
ssh usuario@tu-servidor.com

# Clonar el repositorio
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo
```

### Paso 2: Configurar variables de entorno

```bash
# Copiar el ejemplo y editarlo con tus valores reales
cp .env.example .env
nano .env  # o vim .env

# Asegúrate de configurar:
# - POSTGRES_PASSWORD
# - GEMINI_API_KEY
# - KIMI_API_KEY
# - Etc.
```

### Paso 3: Construir y levantar los contenedores

```bash
# Construir las imágenes (primera vez o después de cambios)
docker compose build --no-cache

# Levantar los contenedores en modo detached
docker compose up -d

# Ver logs para verificar que todo está bien
docker compose logs -f
```

### Paso 4: Verificar que todo funciona

```bash
# Ver estado de los contenedores
docker compose ps

# Todos deben mostrar "healthy" después de ~60 segundos
# Verificar health checks
docker ps

# Probar endpoints
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

---

## 🔄 Actualizar la aplicación en producción

```bash
# 1. Ir al directorio del proyecto
cd /ruta/a/tu-repo

# 2. Hacer pull de los últimos cambios
git pull origin main

# 3. Reconstruir las imágenes (solo si hubo cambios en dependencias o Dockerfile)
docker compose build

# 4. Reiniciar los contenedores
docker compose down
docker compose up -d

# 5. Verificar logs
docker compose logs -f backend
```

---

## 📊 Optimizaciones Implementadas

### Dockerfile Optimizado

✅ **Multi-stage build** - Separa build de runtime
✅ **Solo dependencias de producción** - `uv sync --no-dev`
✅ **Limpieza de caches** - Reduce tamaño de imagen
✅ **Variables de optimización** - `PYTHONOPTIMIZE=2`, `PYTHONDONTWRITEBYTECODE=1`
✅ **Optimizaciones de ML** - `TOKENIZERS_PARALLELISM=false`, `OMP_NUM_THREADS=2`

### Reducción de Tamaño Esperada

| Componente | Antes | Después | Reducción |
|------------|-------|---------|-----------|
| Backend    | 4.2GB | ~1.5GB  | -64%      |
| Frontend   | 4.2GB | ~1.5GB  | -64%      |
| **Total**  | 8.4GB | ~3GB    | -64%      |

### Límites de Recursos (docker-compose.yml)

```yaml
Backend:  Máx 1GB RAM, 2 CPUs
Frontend: Máx 768MB RAM, 1 CPU
Postgres: Máx 512MB RAM, 1 CPU
Total:    ~2.3GB RAM máximo
```

---

## 🛡️ Seguridad en Producción

### Variables de Entorno

**NUNCA** subas `.env` a GitHub. Siempre usa `.env.example` como plantilla.

En el servidor, crea tu `.env` con valores reales:

```bash
# .env en el servidor
POSTGRES_PASSWORD=tu_password_seguro_aqui
GEMINI_API_KEY=tu_api_key_aqui
KIMI_API_KEY=tu_api_key_aqui
```

### Permisos de Archivos

```bash
# Asegurar que .env solo sea legible por el usuario
chmod 600 .env

# Verificar permisos
ls -la .env
# Debe mostrar: -rw------- (600)
```

---

## 📝 Checklist de Deployment

Antes de hacer `docker compose up -d` en producción:

- [ ] `.env` configurado con valores correctos
- [ ] `.env` tiene permisos 600
- [ ] Puerto 8000 (backend) disponible
- [ ] Puerto 8501 (frontend) disponible
- [ ] Puerto 5432 (postgres) disponible
- [ ] Suficiente espacio en disco (mínimo 10GB libres)
- [ ] Suficiente RAM (mínimo 3GB libres)
- [ ] Firewall configurado (si aplica)
- [ ] Backup de base de datos anterior (si es actualización)

---

## 🔍 Monitoreo y Logs

### Ver logs en tiempo real

```bash
# Todos los servicios
docker compose logs -f

# Solo backend
docker compose logs -f backend

# Solo frontend
docker compose logs -f frontend

# Solo postgres
docker compose logs -f postgres
```

### Ver uso de recursos

```bash
# Monitoreo en tiempo real
docker stats

# Ver estado de contenedores
docker compose ps
```

### Verificar health checks

```bash
# Ver detalles de health check
docker inspect agente_hibrido_texto_kimi_rag_gemini-backend-1 | grep -A 20 Health
```

---

## 🆘 Troubleshooting

### Contenedor no inicia

```bash
# Ver logs detallados
docker compose logs backend

# Ver eventos del contenedor
docker events --filter container=nombre_contenedor
```

### Contenedor "unhealthy"

```bash
# Verificar que curl esté instalado
docker exec nombre_contenedor curl --version

# Probar health check manualmente
docker exec nombre_contenedor curl -f http://localhost:8000/health
```

### Out of Memory (OOM)

```bash
# Ver uso de memoria
docker stats --no-stream

# Ajustar límites en docker-compose.yml si es necesario
# Aumentar memory limits si la aplicación lo requiere
```

### Problemas de permisos

```bash
# Verificar permisos de volúmenes
docker compose down
sudo chown -R $USER:$USER ./data
docker compose up -d
```

---

## 🔄 Backup y Restore

### Backup de PostgreSQL

```bash
# Crear backup
docker exec agente_hibrido_texto_kimi_rag_gemini-postgres-1 \
  pg_dump -U postgres nombre_db > backup_$(date +%Y%m%d).sql

# Comprimir backup
gzip backup_$(date +%Y%m%d).sql
```

### Restore de PostgreSQL

```bash
# Restaurar desde backup
docker exec -i agente_hibrido_texto_kimi_rag_gemini-postgres-1 \
  psql -U postgres nombre_db < backup_20241214.sql
```

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs: `docker compose logs -f`
2. Verifica health checks: `docker compose ps`
3. Revisa el uso de recursos: `docker stats`
4. Consulta este documento
5. Revisa la documentación en `docs/`

---

**Última actualización**: 14 de Diciembre, 2025
