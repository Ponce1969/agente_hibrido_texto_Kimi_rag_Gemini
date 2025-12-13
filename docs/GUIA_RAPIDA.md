# ⚡ Guía Rápida: Inicio del Proyecto

## 🎯 Configuración Inicial

### **1. Configurar Variables de Entorno**

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar con tus credenciales
nano .env
```

**Variables importantes:**
- `GEMINI_API_KEY` - Para RAG y embeddings
- `GROQ_API_KEY` - Para Kimi-K2
- `POSTGRES_PASSWORD` - Contraseña segura para PostgreSQL

---

## 🚀 Iniciar el Proyecto

### **Opción 1: Con Docker (Recomendado)**

```bash
# Iniciar todos los servicios (Backend + Frontend + PostgreSQL)
docker compose up --build

# Acceder:
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

### **Opción 2: Sin Docker (Manual)**

```bash
# 1. Instalar dependencias
uv sync

# 2. Iniciar PostgreSQL (debe estar corriendo)

# 3. Desarrollo (Uvicorn + hot-reload)
./scripts/start_dev.sh

# 4. Producción (Gunicorn + 4 workers)
./scripts/start_prod.sh
```

---

## ✅ Verificar que Funciona

```bash
# Health check
curl http://localhost:8000/health

# Ver workers de Gunicorn (Docker)
docker compose exec backend ps aux | grep gunicorn

# Ver workers de Gunicorn (sin Docker)
ps aux | grep gunicorn

# Deberías ver 5 procesos:
# - 1 master process
# - 4 worker processes
```

---

## 🍊 Para Actualizar en Orange Pi (Manual)

### **Cada vez que hagas push a GitHub:**

```bash
# 1. SSH a Orange Pi
ssh orangepi@<tu-ip>

# 2. Ir al proyecto
cd ~/agente_hibrido

# 3. Detener servidor
pkill -f gunicorn

# 4. Actualizar código
git pull origin main

# 5. Reiniciar servidor
./scripts/start_prod.sh
```

**Tiempo:** 30 segundos

---

## 🔧 Comandos Útiles

### **Docker**
```bash
# Iniciar
docker compose up --build

# Detener
docker compose down

# Ver logs
docker compose logs -f backend

# Rebuild solo backend
docker compose up -d --build --no-deps backend
```

### **Sin Docker**
```bash
# Desarrollo (hot-reload)
./scripts/start_dev.sh

# Producción (Gunicorn)
./scripts/start_prod.sh

# Detener
pkill -f gunicorn
```

---

## 📚 Documentación

- **`README.md`** - Información completa del proyecto
- **`DEPLOY_MANUAL.md`** - Deploy manual en Orange Pi
- **`doc/GUNICORN_VS_UVICORN.md`** - Comparativa técnica
- **`doc/SECURITY_ROADMAP.md`** - Próximos pasos de seguridad

---

## 🎯 Configuración de Gunicorn

El proyecto usa **Gunicorn + 4 workers** en producción:
- Configuración en `gunicorn.conf.py`
- Workers configurables con `GUNICORN_WORKERS` en `.env`
- Timeout configurable con `GUNICORN_TIMEOUT` en `.env`
