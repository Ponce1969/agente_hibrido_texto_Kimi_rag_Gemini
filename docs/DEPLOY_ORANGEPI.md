# 🍊 Deploy en OrangePi - Guía Completa

## 📋 Requisitos del Servidor

### Hardware Mínimo
- **RAM**: 4 GB (recomendado 8 GB)
- **Almacenamiento**: 20 GB libres
- **CPU**: ARM64 o x86_64

### Software Requerido
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Conexión a internet

---

## 🚀 Instalación Paso a Paso

### 1. Preparar el Servidor OrangePi

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker (si no está instalado)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Instalar Docker Compose
sudo apt install docker-compose-plugin -y

# Verificar instalación
docker --version
docker compose version
```

---

### 2. Clonar el Repositorio

```bash
# Navegar al directorio de proyectos
cd ~
mkdir -p proyectos
cd proyectos

# Clonar repositorio
git clone https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini.git
cd agente_hibrido_texto_Kimi_rag_Gemini
```

---

### 3. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con nano o vim
nano .env
```

**Variables OBLIGATORIAS:**
```env
# APIs (REQUERIDAS)
GEMINI_API_KEY=tu_api_key_de_gemini_aqui
KIMI_API_KEY=tu_api_key_de_kimi_aqui

# PostgreSQL
POSTGRES_DB=rag_database
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=tu_password_seguro_aqui
POSTGRES_PORT_EXTERNAL=5432

# Puertos
BACKEND_PORT=8000
FRONTEND_PORT=8501

# URLs
BACKEND_URL=http://backend:8000/api/v1
```

**Guardar**: `Ctrl+O`, `Enter`, `Ctrl+X`

---

### 4. Construir e Iniciar Servicios

```bash
# Habilitar BuildKit para builds optimizados
export DOCKER_BUILDKIT=1

# Build (primera vez: 5-10 min)
docker compose build

# Iniciar servicios en background
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Detener logs: Ctrl+C
```

---

### 5. Verificar que Todo Funciona

```bash
# Ver contenedores corriendo
docker ps

# Deberías ver 3 contenedores:
# - agente_hibrido_texto_kimi_rag_gemini-backend-1
# - agente_hibrido_texto_kimi_rag_gemini-frontend-1
# - agente_hibrido_texto_kimi_rag_gemini-postgres-1

# Ver consumo de recursos
docker stats

# Ver logs de cada servicio
docker logs agente_hibrido_texto_kimi_rag_gemini-backend-1
docker logs agente_hibrido_texto_kimi_rag_gemini-frontend-1
docker logs agente_hibrido_texto_kimi_rag_gemini-postgres-1
```

---

### 6. Acceder a la Aplicación

**Desde el mismo servidor:**
```bash
# Frontend
http://localhost:8501

# Backend API
http://localhost:8000/docs
```

**Desde otra computadora en la red:**
```bash
# Reemplaza IP_DEL_ORANGEPI con la IP real
http://IP_DEL_ORANGEPI:8501      # Frontend
http://IP_DEL_ORANGEPI:8000/docs # Backend API
```

**Obtener IP del OrangePi:**
```bash
hostname -I
# O
ip addr show
```

---

## 🔄 Actualizar desde GitHub

```bash
# Detener servicios
docker compose down

# Actualizar código
git pull origin main

# Rebuild solo si cambiaron dependencias
docker compose build

# Iniciar servicios
docker compose up -d

# Verificar
docker ps
docker logs -f agente_hibrido_texto_kimi_rag_gemini-backend-1
```

---

## 📊 Monitoreo y Mantenimiento

### Ver Consumo de Recursos
```bash
# Consumo en tiempo real
docker stats

# Uso de disco
docker system df

# Límites configurados:
# Backend:  1 GB RAM máx
# Frontend: 768 MB RAM máx
# Postgres: 512 MB RAM máx
# TOTAL:    2.3 GB RAM máx
```

### Limpiar Recursos
```bash
# Limpiar imágenes no usadas
docker image prune -a -f

# Limpiar todo (cuidado con volúmenes)
docker system prune -a --volumes -f

# Ver logs
docker compose logs --tail=100 -f
```

### Reiniciar Servicios
```bash
# Reiniciar todo
docker compose restart

# Reiniciar solo un servicio
docker compose restart backend
docker compose restart frontend
docker compose restart postgres
```

---

## 🐛 Troubleshooting

### Backend no inicia
```bash
# Ver logs detallados
docker logs agente_hibrido_texto_kimi_rag_gemini-backend-1

# Verificar variables de entorno
docker exec agente_hibrido_texto_kimi_rag_gemini-backend-1 env | grep API

# Verificar que Gemini API key está configurada
docker exec agente_hibrido_texto_kimi_rag_gemini-backend-1 env | grep GEMINI
```

### Frontend no carga
```bash
# Ver logs
docker logs agente_hibrido_texto_kimi_rag_gemini-frontend-1

# Verificar que backend está healthy
docker ps

# Reiniciar frontend
docker compose restart frontend
```

### PostgreSQL no conecta
```bash
# Ver logs
docker logs agente_hibrido_texto_kimi_rag_gemini-postgres-1

# Verificar que está healthy
docker ps

# Conectar manualmente para probar
docker exec -it agente_hibrido_texto_kimi_rag_gemini-postgres-1 psql -U rag_user -d rag_database
```

### Poco espacio en disco
```bash
# Ver uso de disco
df -h

# Limpiar Docker
docker system prune -a -f

# Limpiar logs del sistema
sudo journalctl --vacuum-time=7d
```

### Consumo alto de RAM
```bash
# Ver consumo actual
docker stats --no-stream

# Si algún contenedor excede límites, reiniciar
docker compose restart

# Verificar límites en docker-compose.yml
grep -A 5 "resources:" docker-compose.yml
```

---

## 🔒 Seguridad

### Firewall (Opcional pero Recomendado)
```bash
# Instalar UFW
sudo apt install ufw -y

# Permitir SSH (IMPORTANTE antes de habilitar)
sudo ufw allow 22/tcp

# Permitir puertos de la aplicación
sudo ufw allow 8000/tcp  # Backend
sudo ufw allow 8501/tcp  # Frontend

# Habilitar firewall
sudo ufw enable

# Ver estado
sudo ufw status
```

### Actualizar Contraseñas
```bash
# Cambiar password de PostgreSQL en .env
nano .env

# Recrear contenedor de Postgres
docker compose down postgres
docker compose up -d postgres
```

---

## 📈 Optimización para Producción

### Habilitar Logs Persistentes
```bash
# Crear directorio de logs
mkdir -p ~/logs

# Agregar en docker-compose.yml (opcional)
# logging:
#   driver: "json-file"
#   options:
#     max-size: "10m"
#     max-file: "3"
```

### Backup de Base de Datos
```bash
# Backup manual
docker exec agente_hibrido_texto_kimi_rag_gemini-postgres-1 \
  pg_dump -U rag_user rag_database > backup_$(date +%Y%m%d).sql

# Restaurar backup
cat backup_20251215.sql | docker exec -i \
  agente_hibrido_texto_kimi_rag_gemini-postgres-1 \
  psql -U rag_user -d rag_database
```

### Auto-inicio en Boot
```bash
# Habilitar Docker en boot
sudo systemctl enable docker

# Los contenedores se reinician automáticamente
# gracias a "restart: unless-stopped" en docker-compose.yml
```

---

## 📝 Comandos Útiles Rápidos

```bash
# Ver todo
docker compose ps

# Logs en vivo
docker compose logs -f

# Detener todo
docker compose down

# Iniciar todo
docker compose up -d

# Rebuild y reiniciar
docker compose up -d --build

# Ver consumo
docker stats

# Limpiar
docker system prune -a -f

# Actualizar desde GitHub
git pull && docker compose up -d --build
```

---

## 🎯 Checklist de Deploy

- [ ] Docker y Docker Compose instalados
- [ ] Repositorio clonado
- [ ] `.env` configurado con API keys
- [ ] `docker compose build` ejecutado exitosamente
- [ ] `docker compose up -d` ejecutado
- [ ] 3 contenedores corriendo (backend, frontend, postgres)
- [ ] Frontend accesible en puerto 8501
- [ ] Backend accesible en puerto 8000
- [ ] Consumo de RAM < 2.3 GB
- [ ] Firewall configurado (opcional)
- [ ] Backup configurado (opcional)

---

## 📞 Soporte

**Logs para debugging:**
```bash
# Guardar logs para análisis
docker compose logs > logs_completos.txt

# Enviar logs específicos
docker logs agente_hibrido_texto_kimi_rag_gemini-backend-1 > backend_error.txt
```

**Información del sistema:**
```bash
# Info del servidor
uname -a
docker --version
docker compose version
free -h
df -h
```

---

**Fecha**: 15 de Diciembre, 2025  
**Versión**: 1.0 - Optimizada sin modelos ML locales  
**Arquitectura**: Gemini API + Kimi API + PostgreSQL + FastAPI + Streamlit
