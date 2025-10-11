# 🍊 Deployment en Orange Pi 5 Plus

Guía completa para configurar auto-deployment desde GitHub a tu Orange Pi 5 Plus.

---

## 🎯 Objetivo

Cuando hagas `git push` a GitHub → Automáticamente se actualiza en Orange Pi → Servicios se reinician.

---

## 📋 Requisitos Previos

### En tu Orange Pi:
- ✅ Docker y Docker Compose instalados
- ✅ Git instalado
- ✅ SSH habilitado
- ✅ Proyecto clonado en `/home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini`

### En GitHub:
- ✅ Repositorio creado
- ✅ Acceso a Settings → Secrets

---

## 🚀 Opción 1: Auto-Deployment con GitHub Actions (Recomendado)

### **Paso 1: Generar SSH Key en tu PC**

```bash
# Generar nueva SSH key (si no tienes una)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/orangepi_deploy

# Esto crea dos archivos:
# - orangepi_deploy (clave privada) → Para GitHub Secrets
# - orangepi_deploy.pub (clave pública) → Para Orange Pi
```

### **Paso 2: Configurar Orange Pi**

```bash
# Conectarte a Orange Pi
ssh orangepi@<IP_DE_TU_ORANGEPI>

# Agregar la clave pública a authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys << 'EOF'
# Pegar aquí el contenido de orangepi_deploy.pub
EOF
chmod 600 ~/.ssh/authorized_keys

# Clonar el proyecto (si no lo hiciste)
cd ~
git clone https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini.git
cd agente_hibrido_texto_Kimi_rag_Gemini

# Crear .env con tus configuraciones
cp .env.example .env
nano .env  # Editar con tus API keys

# Primera ejecución
docker compose up -d --build
```

### **Paso 3: Configurar GitHub Secrets**

Ve a tu repositorio en GitHub:
```
Settings → Secrets and variables → Actions → New repository secret
```

Agrega estos secrets:

| Secret Name | Valor | Descripción |
|-------------|-------|-------------|
| `ORANGEPI_HOST` | `<IP_DE_TU_ORANGEPI>` | IP pública o dominio |
| `ORANGEPI_USER` | `orangepi` | Usuario SSH |
| `ORANGEPI_SSH_KEY` | `<contenido de orangepi_deploy>` | Clave privada SSH |
| `ORANGEPI_PORT` | `22` | Puerto SSH (default 22) |
| `ORANGEPI_PROJECT_PATH` | `/home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini` | Ruta del proyecto |

**Importante:** Para `ORANGEPI_SSH_KEY`, copia TODO el contenido del archivo `orangepi_deploy`, incluyendo:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

### **Paso 4: Probar el Deployment**

```bash
# En tu PC, hacer un cambio pequeño
echo "# Test deployment" >> README.md
git add README.md
git commit -m "test: Probar auto-deployment"
git push origin main

# Ir a GitHub → Actions → Ver el workflow ejecutándose
# Si todo está bien, verás ✅ en cada paso
```

---

## 🔧 Opción 2: Deployment Manual desde Orange Pi

Si prefieres actualizar manualmente desde Orange Pi:

```bash
# Conectarte a Orange Pi
ssh orangepi@<IP_DE_TU_ORANGEPI>

# Ir al proyecto
cd ~/agente_hibrido_texto_Kimi_rag_Gemini

# Ejecutar script de deployment
bash scripts/deploy_orangepi.sh
```

El script automáticamente:
1. ✅ Hace backup de `.env`
2. ✅ Descarga cambios de GitHub
3. ✅ Reinicia servicios Docker
4. ✅ Verifica que todo funcione
5. ✅ Limpia imágenes antiguas

---

## 🔄 Opción 3: Cron Job (Auto-pull cada X minutos)

Si quieres que Orange Pi verifique cambios automáticamente:

```bash
# En Orange Pi, editar crontab
crontab -e

# Agregar esta línea (verifica cada 5 minutos)
*/5 * * * * cd /home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini && bash scripts/deploy_orangepi.sh >> /tmp/deploy.log 2>&1
```

---

## 🌐 Configurar Acceso Externo (Opcional)

### **Opción A: Usar tu IP Pública**

Si tu Orange Pi tiene IP pública:
```bash
# Configurar firewall
sudo ufw allow 8501/tcp  # Streamlit
sudo ufw allow 8000/tcp  # FastAPI
sudo ufw enable
```

### **Opción B: Usar Cloudflare Tunnel (Gratis)**

Para compartir sin IP pública:

```bash
# Instalar cloudflared en Orange Pi
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# Crear túnel
cloudflared tunnel --url http://localhost:8501

# Te dará una URL pública: https://random-name.trycloudflare.com
```

### **Opción C: Usar Tailscale (VPN)**

Para acceso privado entre tus dispositivos:

```bash
# Instalar Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Ahora puedes acceder desde cualquier dispositivo con Tailscale
# usando la IP de Tailscale (100.x.x.x)
```

---

## 🐛 Troubleshooting

### **Error: Permission denied (publickey)**
```bash
# Verificar que la clave SSH esté correcta
ssh -i ~/.ssh/orangepi_deploy orangepi@<IP_ORANGEPI>

# Si funciona, el problema está en GitHub Secrets
```

### **Error: docker compose command not found**
```bash
# En Orange Pi, instalar Docker Compose
sudo apt update
sudo apt install docker-compose-plugin
```

### **Error: Port already in use**
```bash
# En Orange Pi, ver qué está usando el puerto
sudo lsof -i :8501
sudo lsof -i :8000

# Detener servicios antiguos
docker compose down
```

### **Ver logs de deployment**
```bash
# En GitHub: Actions → Click en el workflow → Ver logs

# En Orange Pi:
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 📊 Monitoreo

### **Ver estado de servicios**
```bash
# En Orange Pi
docker compose ps
docker stats
```

### **Ver logs en tiempo real**
```bash
docker compose logs -f
```

### **Verificar health**
```bash
curl http://localhost:8000/health
```

---

## 🔒 Seguridad

### **Recomendaciones:**
1. ✅ Cambiar puerto SSH del default 22
2. ✅ Usar fail2ban para proteger SSH
3. ✅ Mantener `.env` fuera de Git (ya está en .gitignore)
4. ✅ Usar HTTPS con Nginx + Let's Encrypt
5. ✅ Configurar firewall (ufw)

### **Configurar fail2ban:**
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 🎉 Workflow Completo

```mermaid
graph LR
    A[Hacer cambios] --> B[git commit]
    B --> C[git push]
    C --> D[GitHub Actions]
    D --> E[SSH a Orange Pi]
    E --> F[git pull]
    F --> G[docker compose up]
    G --> H[✅ Proyecto actualizado]
```

---

## 📝 Notas

- El archivo `.env` NO se sube a GitHub (está en .gitignore)
- El script hace backup de `.env` antes de cada deployment
- Los servicios se reinician automáticamente
- Las imágenes antiguas se limpian para ahorrar espacio

---

**Última actualización:** Octubre 2025  
**Mantenedor:** Equipo de desarrollo
