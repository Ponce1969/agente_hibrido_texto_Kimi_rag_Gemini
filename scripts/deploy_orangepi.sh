#!/bin/bash

# 🍊 Script de Deployment para Orange Pi 5 Plus
# Este script actualiza el proyecto desde GitHub y reinicia los servicios

set -e  # Salir si hay error

echo "🍊 ====================================="
echo "   Deployment en Orange Pi 5 Plus"
echo "====================================="

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio del proyecto (ajustar según tu configuración)
PROJECT_DIR="${PROJECT_DIR:-/home/orangepi/agente_hibrido_texto_Kimi_rag_Gemini}"

echo -e "${YELLOW}📂 Directorio del proyecto: $PROJECT_DIR${NC}"

# Ir al directorio del proyecto
cd "$PROJECT_DIR" || exit 1

# Verificar que estamos en un repo git
if [ ! -d .git ]; then
    echo -e "${RED}❌ Error: No es un repositorio Git${NC}"
    exit 1
fi

# Backup del .env
echo -e "${YELLOW}💾 Haciendo backup de .env...${NC}"
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup creado${NC}"
fi

# Obtener rama actual
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${YELLOW}🌿 Rama actual: $CURRENT_BRANCH${NC}"

# Hacer stash de cambios locales (por si acaso)
echo -e "${YELLOW}📦 Guardando cambios locales...${NC}"
git stash

# Pull de GitHub
echo -e "${YELLOW}⬇️  Descargando cambios desde GitHub...${NC}"
git pull origin "$CURRENT_BRANCH"

# Aplicar stash si había cambios
if git stash list | grep -q "stash@{0}"; then
    echo -e "${YELLOW}📤 Restaurando cambios locales...${NC}"
    git stash pop || echo -e "${YELLOW}⚠️  No se pudieron aplicar cambios locales${NC}"
fi

# Verificar si hay docker-compose
if [ ! -f docker-compose.yml ]; then
    echo -e "${RED}❌ Error: No se encontró docker-compose.yml${NC}"
    exit 1
fi

# Detener servicios
echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
docker compose down

# Reconstruir y levantar servicios
echo -e "${YELLOW}🔨 Reconstruyendo servicios...${NC}"
docker compose up -d --build

# Esperar a que los servicios estén listos
echo -e "${YELLOW}⏳ Esperando que los servicios estén listos...${NC}"
sleep 10

# Verificar estado de los servicios
echo -e "${YELLOW}📊 Estado de los servicios:${NC}"
docker compose ps

# Limpiar imágenes antiguas
echo -e "${YELLOW}🧹 Limpiando imágenes antiguas...${NC}"
docker image prune -f

# Verificar health del backend
echo -e "${YELLOW}🏥 Verificando health del backend...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend está funcionando correctamente${NC}"
else
    echo -e "${RED}⚠️  Backend no responde en el health check${NC}"
fi

# Mostrar logs recientes
echo -e "${YELLOW}📋 Últimos logs del backend:${NC}"
docker compose logs --tail=20 backend

echo ""
echo -e "${GREEN}🎉 ====================================="
echo -e "   Deployment Completado!"
echo -e "=====================================${NC}"
echo ""
echo -e "${GREEN}✅ Frontend: http://localhost:8501${NC}"
echo -e "${GREEN}✅ Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}✅ API Docs: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}💡 Para ver logs en tiempo real:${NC}"
echo -e "   docker compose logs -f backend"
echo ""
