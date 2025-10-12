# 🍊 Guía de Deploy Manual en Orange Pi 5 Plus

Guía simple para deploy manual sin automatización, CI/CD ni systemd.

---

## 📋 Requisitos Previos

- ✅ Orange Pi 5 Plus con Ubuntu/Debian
- ✅ Python 3.12 instalado
- ✅ uv instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- ✅ Git instalado
- ✅ Cloudflare Tunnel configurado (ya lo tienes)

---

## 🚀 Primera Instalación en Orange Pi

### **1. Clonar el Repositorio**

```bash
# Conectar por SSH a Orange Pi
ssh orangepi@<tu-ip>

# Ir a tu carpeta de proyectos
cd ~  # o donde tengas tus proyectos

# Clonar
git clone <tu-repo-url> agente_hibrido
cd agente_hibrido
```

### **2. Configurar Variables de Entorno**

```bash
# Crear archivo .env
nano .env
```

Copiar y pegar tus credenciales:
```env
# PostgreSQL
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_password
POSTGRES_DB=agentes_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Gemini
GEMINI_API_KEY=tu_api_key_gemini

# Kimi
KIMI_API_KEY=tu_api_key_kimi

# Bear (opcional)
BEAR_API_KEY=tu_api_key_bear

# Otros...
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

### **3. Instalar Dependencias**

```bash
# Instalar todas las dependencias (incluye Gunicorn)
uv sync
```

### **4. Iniciar el Servidor**

```bash
# Iniciar en modo producción (Gunicorn + 4 workers)
./scripts/start_prod.sh
```

**¡Listo!** Tu servidor está corriendo con Gunicorn.

---

## 🔄 Actualizar Código (Cuando Hagas Push a GitHub)

### **Proceso Manual Simple**

```bash
# 1. Conectar por SSH a Orange Pi
ssh orangepi@<tu-ip>

# 2. Ir a la carpeta del proyecto
cd ~/agente_hibrido

# 3. Detener el servidor (Ctrl+C en la terminal donde corre)
# O si corre en background:
pkill -f gunicorn

# 4. Descargar cambios de GitHub
git pull origin main  # o tu rama

# 5. Actualizar dependencias (por si agregaste algo)
uv sync

# 6. Reiniciar el servidor
./scripts/start_prod.sh
```

**Tiempo total:** ~30 segundos

---

## 🛠️ Comandos Útiles

### **Ver si el Servidor Está Corriendo**

```bash
# Ver procesos de Gunicorn
ps aux | grep gunicorn

# Deberías ver algo como:
# orangepi  1234  0.5  2.0  gunicorn: master
# orangepi  1235  5.0  8.0  gunicorn: worker 1
# orangepi  1236  4.8  7.9  gunicorn: worker 2
# orangepi  1237  5.2  8.1  gunicorn: worker 3
# orangepi  1238  4.9  8.0  gunicorn: worker 4
```

### **Detener el Servidor**

```bash
# Si está en primer plano
Ctrl+C

# Si está en background
pkill -f gunicorn

# O más específico
kill $(pgrep -f "gunicorn src.main:app")
```

### **Ver Logs en Tiempo Real**

```bash
# Los logs aparecen en la terminal donde iniciaste el servidor
# Si quieres guardarlos en un archivo:
./scripts/start_prod.sh > logs.txt 2>&1
```

### **Verificar que Funciona**

```bash
# Health check
curl http://localhost:8000/health

# Debería responder:
# {"status":"healthy","service":"Asistente IA con RAG"}
```

### **Ver Uso de Recursos**

```bash
# CPU y RAM
htop

# Presionar F5 para ver árbol de procesos
# Buscar "gunicorn" para ver los workers
```

---

## 🔧 Correr en Background (Opcional)

Si quieres que el servidor siga corriendo después de cerrar SSH:

### **Opción 1: nohup (Simple)**

```bash
# Iniciar en background
nohup ./scripts/start_prod.sh > logs.txt 2>&1 &

# Ver el proceso
ps aux | grep gunicorn

# Detener
pkill -f gunicorn
```

### **Opción 2: screen (Recomendado)**

```bash
# Instalar screen (si no lo tienes)
sudo apt install screen

# Crear sesión
screen -S agente

# Iniciar servidor
./scripts/start_prod.sh

# Desconectar (servidor sigue corriendo)
Ctrl+A, luego D

# Reconectar después
screen -r agente

# Listar sesiones
screen -ls
```

### **Opción 3: tmux (Alternativa a screen)**

```bash
# Instalar tmux
sudo apt install tmux

# Crear sesión
tmux new -s agente

# Iniciar servidor
./scripts/start_prod.sh

# Desconectar
Ctrl+B, luego D

# Reconectar
tmux attach -t agente
```

---

## 🐛 Troubleshooting

### **Error: "Address already in use"**

```bash
# Ver qué está usando el puerto 8000
sudo lsof -i :8000

# Matar el proceso
kill <PID>

# O matar todos los gunicorn
pkill -f gunicorn
```

### **Error: "ModuleNotFoundError"**

```bash
# Reinstalar dependencias
uv sync

# Verificar que estás en la carpeta correcta
pwd  # Debe mostrar la ruta del proyecto
```

### **Error: "Permission denied"**

```bash
# Dar permisos a los scripts
chmod +x scripts/*.sh
```

### **El Servidor se Cae**

```bash
# Ver logs para identificar el error
./scripts/start_prod.sh

# O guardar logs
./scripts/start_prod.sh > logs.txt 2>&1

# Ver el archivo de logs
cat logs.txt
```

### **Alto Uso de RAM**

```bash
# Reducir workers en gunicorn.conf.py
nano gunicorn.conf.py

# Cambiar:
workers = 2  # En vez de 4

# Reiniciar
pkill -f gunicorn
./scripts/start_prod.sh
```

---

## 📊 Diferencias: Desarrollo vs Producción

| Aspecto | Desarrollo | Producción |
|---------|-----------|------------|
| Script | `./scripts/start_dev.sh` | `./scripts/start_prod.sh` |
| Servidor | Uvicorn | Gunicorn + Uvicorn |
| Workers | 1 | 4 |
| Hot-reload | ✅ Sí | ❌ No |
| Velocidad | Normal | 3-4x más rápido |
| Uso | PC local | Orange Pi |

---

## 🎯 Workflow Típico

### **En tu PC (Desarrollo)**

```bash
# 1. Hacer cambios en el código
nano src/main.py

# 2. Probar localmente
./scripts/start_dev.sh

# 3. Verificar que funciona
curl http://localhost:8000/health

# 4. Subir a GitHub
git add .
git commit -m "Mejora en endpoint X"
git push origin main
```

### **En Orange Pi (Producción)**

```bash
# 1. Conectar por SSH
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

---

## 💡 Tips

### **Automatizar con un Script Simple**

Puedes crear un script de actualización rápida:

```bash
# Crear archivo
nano update.sh
```

Contenido:
```bash
#!/bin/bash
echo "🔄 Actualizando proyecto..."
pkill -f gunicorn
git pull origin main
uv sync
./scripts/start_prod.sh
```

Uso:
```bash
chmod +x update.sh
./update.sh
```

### **Monitorear Logs**

```bash
# Guardar logs con timestamp
./scripts/start_prod.sh 2>&1 | tee -a logs/$(date +%Y%m%d).log
```

### **Backup del .env**

```bash
# Antes de actualizar, hacer backup
cp .env .env.backup.$(date +%Y%m%d)
```

---

## 🔗 Cloudflare Tunnel

Tu configuración actual con Cloudflare Tunnel está perfecta:
- ✅ No necesitas abrir puertos
- ✅ HTTPS automático
- ✅ Protección DDoS
- ✅ El servidor escucha en `localhost:8000`
- ✅ Cloudflare hace el proxy

**No cambies nada de tu configuración de Cloudflare**, solo:
1. Asegúrate que el tunnel apunte a `localhost:8000`
2. Gunicorn escucha en `0.0.0.0:8000` (ya configurado)

---

## ✅ Checklist de Primera Instalación

- [ ] Clonar repo en Orange Pi
- [ ] Crear archivo `.env` con credenciales
- [ ] Ejecutar `uv sync`
- [ ] Probar con `./scripts/start_prod.sh`
- [ ] Verificar con `curl http://localhost:8000/health`
- [ ] Verificar workers con `ps aux | grep gunicorn`
- [ ] Configurar screen/tmux para background
- [ ] Verificar que Cloudflare Tunnel funciona

---

## ✅ Checklist de Actualización

- [ ] Conectar por SSH
- [ ] `cd ~/agente_hibrido`
- [ ] `pkill -f gunicorn`
- [ ] `git pull origin main`
- [ ] `uv sync` (si hay nuevas dependencias)
- [ ] `./scripts/start_prod.sh`
- [ ] Verificar con `curl http://localhost:8000/health`

---

**¡Eso es todo!** Sin CI/CD, sin systemd, sin complicaciones. Solo comandos manuales simples que ya conoces.
