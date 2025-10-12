# 🚀 Gunicorn vs Uvicorn: Guía de Migración

## 📊 Comparativa Técnica

### **Uvicorn Solo (Desarrollo)**
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

| Característica | Estado | Notas |
|----------------|--------|-------|
| Velocidad | ⚡ Excelente | ASGI nativo, muy rápido |
| Multi-core | ❌ No | Single process |
| Auto-restart | ❌ No | Si crashea, se cae |
| Hot-reload | ✅ Sí | Ideal para desarrollo |
| Gestión workers | ❌ No | - |
| Graceful shutdown | ⚠️ Básico | - |
| **Uso recomendado** | 🔧 **Desarrollo** | - |

### **Gunicorn + Uvicorn Workers (Producción)**
```bash
gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

| Característica | Estado | Notas |
|----------------|--------|-------|
| Velocidad | ⚡ Excelente | Mantiene velocidad de Uvicorn |
| Multi-core | ✅ Sí | Aprovecha todos los cores |
| Auto-restart | ✅ Sí | Workers se reinician automáticamente |
| Hot-reload | ❌ No | No necesario en producción |
| Gestión workers | ✅ Sí | Balanceo de carga automático |
| Graceful shutdown | ✅ Sí | Sin pérdida de requests |
| **Uso recomendado** | 🚀 **Producción** | - |

---

## 🍊 Configuración para Orange Pi 5 Plus

### **Hardware**
- **CPU**: RK3588 (4×A76 @ 2.4GHz + 4×A55 @ 1.8GHz) = 8 cores
- **RAM**: 16GB
- **Carga**: 2 LLMs (Kimi + Gemini), PostgreSQL, pgvector, embeddings

### **Workers Recomendados**

```python
# Fórmula estándar: (2 × CPU_cores) + 1
workers = (2 × 8) + 1 = 17  # ❌ Demasiado para tu carga

# Ajustado por recursos limitados:
workers = 4  # ✅ Conservador, deja recursos para LLMs
```

**Justificación:**
- ✅ **4 workers** es suficiente para manejar requests concurrentes
- ✅ Deja RAM y CPU para los modelos de IA
- ✅ Evita context switching excesivo
- ✅ Cada worker puede manejar ~1000 conexiones concurrentes

### **Configuración Óptima**

```python
# gunicorn.conf.py
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120  # Importante para LLMs
max_requests = 1000  # Reciclar workers (evita memory leaks)
preload_app = True  # Ahorra RAM
```

---

## 🔧 Migración Paso a Paso

### **Paso 1: Instalar Gunicorn**

```bash
# Ya agregado en pyproject.toml
uv add gunicorn
```

### **Paso 2: Probar en Desarrollo**

```bash
# Desarrollo (Uvicorn con hot-reload)
./scripts/start_dev.sh

# O manualmente:
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### **Paso 3: Probar Gunicorn Localmente**

```bash
# Producción local (Gunicorn)
./scripts/start_prod.sh

# O manualmente:
uv run gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

### **Paso 4: Configurar Systemd en Orange Pi**

```bash
# 1. Copiar servicio
sudo cp scripts/agente-hibrido.service /etc/systemd/system/

# 2. Editar rutas si es necesario
sudo nano /etc/systemd/system/agente-hibrido.service

# 3. Recargar systemd
sudo systemctl daemon-reload

# 4. Habilitar inicio automático
sudo systemctl enable agente-hibrido

# 5. Iniciar servicio
sudo systemctl start agente-hibrido

# 6. Verificar estado
sudo systemctl status agente-hibrido
```

### **Paso 5: Verificar Funcionamiento**

```bash
# Health check
curl http://localhost:8000/health

# Ver logs
sudo journalctl -u agente-hibrido -f

# Ver workers activos
ps aux | grep gunicorn
```

---

## 📈 Benchmarks Esperados

### **Uvicorn Solo (1 worker)**
- Requests/seg: ~1,000
- Latencia p50: ~50ms
- Latencia p99: ~200ms
- CPU usage: 1 core al 100%

### **Gunicorn + 4 Uvicorn Workers**
- Requests/seg: ~3,500 (3.5x mejor)
- Latencia p50: ~50ms (igual)
- Latencia p99: ~150ms (mejor)
- CPU usage: 4 cores distribuidos

---

## 🛡️ Ventajas de Gunicorn en Producción

### **1. Resiliencia**
```
Worker 1 crashea → Gunicorn lo reinicia automáticamente
Otros 3 workers siguen funcionando → Sin downtime
```

### **2. Balanceo de Carga**
```
Request 1 → Worker 1 (ocupado con LLM)
Request 2 → Worker 2 (libre) ✅
Request 3 → Worker 3 (libre) ✅
```

### **3. Graceful Reload**
```bash
# Actualizar código sin downtime
sudo systemctl reload agente-hibrido

# Gunicorn:
# 1. Inicia nuevos workers con código nuevo
# 2. Espera que los viejos terminen requests
# 3. Mata los viejos workers
# 4. Sin pérdida de requests ✅
```

### **4. Gestión de Recursos**
```python
# Reciclar workers después de N requests
max_requests = 1000
max_requests_jitter = 50

# Evita memory leaks de modelos de IA
# Worker procesa 1000 requests → se reinicia → RAM liberada
```

---

## 🔍 Monitoreo

### **Ver Workers Activos**
```bash
# Procesos
ps aux | grep gunicorn

# Salida esperada:
# orangepi  1234  0.5  2.0  master process
# orangepi  1235  5.0  8.0  worker 1
# orangepi  1236  4.8  7.9  worker 2
# orangepi  1237  5.2  8.1  worker 3
# orangepi  1238  4.9  8.0  worker 4
```

### **Ver Logs**
```bash
# Tiempo real
sudo journalctl -u agente-hibrido -f

# Últimas 100 líneas
sudo journalctl -u agente-hibrido -n 100

# Filtrar errores
sudo journalctl -u agente-hibrido -p err
```

### **Métricas de Sistema**
```bash
# CPU y RAM
htop

# Conexiones de red
ss -tunap | grep :8000

# Requests por segundo (con ab)
ab -n 1000 -c 10 http://localhost:8000/health
```

---

## 🚨 Troubleshooting

### **Workers se reinician constantemente**
```bash
# Aumentar timeout (LLMs tardan)
timeout = 180  # 3 minutos

# Ver logs para identificar el problema
sudo journalctl -u agente-hibrido -n 100
```

### **Alto uso de RAM**
```bash
# Reducir workers
workers = 2

# Reducir max_requests (reciclar más seguido)
max_requests = 500
```

### **Latencia alta**
```bash
# Aumentar workers (si hay CPU disponible)
workers = 6

# Aumentar worker_connections
worker_connections = 2000
```

### **Servicio no inicia**
```bash
# Ver error específico
sudo systemctl status agente-hibrido

# Ver logs completos
sudo journalctl -u agente-hibrido -xe

# Verificar permisos
ls -la /home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini

# Probar manualmente
cd /home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini
./scripts/start_prod.sh
```

---

## 📋 Checklist de Migración

### Desarrollo
- [x] Instalar Gunicorn en `pyproject.toml`
- [x] Crear `gunicorn.conf.py`
- [x] Crear `scripts/start_dev.sh` (Uvicorn)
- [x] Crear `scripts/start_prod.sh` (Gunicorn)
- [ ] Probar localmente con Gunicorn
- [ ] Verificar que todos los endpoints funcionan
- [ ] Hacer load testing básico

### Producción (Orange Pi)
- [ ] Copiar archivos al servidor
- [ ] Instalar dependencias con `uv sync`
- [ ] Configurar `agente-hibrido.service`
- [ ] Instalar servicio systemd
- [ ] Iniciar servicio
- [ ] Verificar health check
- [ ] Monitorear logs por 24h
- [ ] Ajustar workers si es necesario

---

## 🔗 Referencias

- [Gunicorn Docs](https://docs.gunicorn.org/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/server-workers/)
- [Systemd Service Guide](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

**Documento creado:** 2025-10-12  
**Hardware target:** Orange Pi 5 Plus (RK3588, 16GB RAM)  
**Configuración recomendada:** 4 workers, timeout 120s
