# 🚀 Resumen: Migración a Gunicorn para Orange Pi 5 Plus

## ✅ Respuesta Directa

**SÍ, debes migrar a Gunicorn + Uvicorn workers para producción.**

Uvicorn solo es excelente para desarrollo, pero Gunicorn te da:
- ✅ Multi-proceso (aprovecha los 8 cores del RK3588)
- ✅ Auto-restart de workers en crashes
- ✅ Graceful reload sin downtime
- ✅ Gestión robusta de procesos

---

## 📦 Archivos Creados

### **Configuración**
- ✅ `gunicorn.conf.py` - Configuración optimizada para Orange Pi
- ✅ `pyproject.toml` - Gunicorn agregado a dependencias

### **Scripts de Inicio**
- ✅ `scripts/start_dev.sh` - Desarrollo (Uvicorn + hot-reload)
- ✅ `scripts/start_prod.sh` - Producción (Gunicorn + 4 workers)
- ✅ `scripts/start_prod_systemd.sh` - Para servicio systemd

### **Deployment**
- ✅ `scripts/agente-hibrido.service` - Servicio systemd
- ✅ `scripts/deploy_orangepi_systemd.sh` - Deploy automático

### **Documentación**
- ✅ `doc/GUNICORN_VS_UVICORN.md` - Comparativa completa
- ✅ `scripts/README.md` - Actualizado con nuevos scripts

---

## 🎯 Configuración Recomendada

```python
# gunicorn.conf.py
workers = 4  # Conservador para tu carga de LLMs
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120  # Importante para LLMs que tardan
max_requests = 1000  # Reciclar workers (evita memory leaks)
preload_app = True  # Ahorra RAM
```

**Justificación:**
- Orange Pi 5 Plus: 8 cores, 16GB RAM
- Carga: Kimi + Gemini + PostgreSQL + pgvector + embeddings
- 4 workers deja recursos para los modelos de IA

---

## 🔧 Pasos para Implementar

### **1. Instalar Gunicorn (Local)**
```bash
cd /home/gonzapython/Documentos/vscode_codigo/agentes_Front_Bac/agentes_Front_Bac
uv sync
```

### **2. Probar Localmente**
```bash
# Desarrollo (como siempre)
./scripts/start_dev.sh

# Producción (probar Gunicorn)
./scripts/start_prod.sh
```

### **3. Verificar Funcionamiento**
```bash
# En otra terminal
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Ver workers activos
ps aux | grep gunicorn
```

### **4. Deploy en Orange Pi**
```bash
# Copiar proyecto a Orange Pi
scp -r . orangepi@<IP>:/home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini

# SSH a Orange Pi
ssh orangepi@<IP>

# Instalar servicio systemd
cd /home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini
sudo cp scripts/agente-hibrido.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable agente-hibrido
sudo systemctl start agente-hibrido

# Verificar
sudo systemctl status agente-hibrido
curl http://localhost:8000/health
```

### **5. Monitorear**
```bash
# Logs en tiempo real
sudo journalctl -u agente-hibrido -f

# Ver workers
ps aux | grep gunicorn

# Uso de recursos
htop
```

---

## 📊 Comparativa Rápida

| Característica | Uvicorn Solo | Gunicorn + Uvicorn |
|----------------|--------------|-------------------|
| Workers | 1 | 4 |
| Cores usados | 1 | 4 |
| Requests/seg | ~1,000 | ~3,500 |
| Auto-restart | ❌ | ✅ |
| Graceful reload | ❌ | ✅ |
| **Uso** | 🔧 Desarrollo | 🚀 Producción |

---

## 🛡️ Ventajas en Producción

### **Resiliencia**
```
Worker crashea → Gunicorn lo reinicia automáticamente
Otros workers siguen funcionando → Sin downtime
```

### **Balanceo de Carga**
```
Request LLM lento → Worker 1 ocupado
Nuevos requests → Workers 2, 3, 4 libres ✅
```

### **Graceful Reload**
```bash
sudo systemctl reload agente-hibrido
# Actualiza código sin perder requests ✅
```

---

## 🚨 Próximos Pasos

### **Inmediato**
1. ✅ Instalar Gunicorn: `uv sync`
2. ✅ Probar localmente: `./scripts/start_prod.sh`
3. ✅ Verificar que funciona: `curl http://localhost:8000/health`

### **Antes del Deploy Final**
4. ⏳ Implementar Rate Limiting (ver `SECURITY_ROADMAP.md`)
5. ⏳ Implementar Argon2 para contraseñas
6. ⏳ Configurar HTTPS con certificado SSL
7. ⏳ Configurar firewall en Orange Pi

### **En Orange Pi**
8. ⏳ Instalar servicio systemd
9. ⏳ Configurar inicio automático
10. ⏳ Monitorear por 24-48h
11. ⏳ Ajustar workers si es necesario

---

## 📚 Documentación

- **Comparativa completa**: `doc/GUNICORN_VS_UVICORN.md`
- **Seguridad**: `doc/SECURITY_ROADMAP.md`
- **Scripts**: `scripts/README.md`

---

## 💡 Comandos Útiles

```bash
# Desarrollo
./scripts/start_dev.sh

# Producción local
./scripts/start_prod.sh

# Deploy en Orange Pi
./scripts/deploy_orangepi_systemd.sh

# Ver logs
sudo journalctl -u agente-hibrido -f

# Ver estado
sudo systemctl status agente-hibrido

# Reiniciar
sudo systemctl restart agente-hibrido
```

---

**Conclusión:** Gunicorn es la opción correcta para producción. Te da robustez, multi-proceso, y gestión profesional de workers sin sacrificar la velocidad de Uvicorn.
