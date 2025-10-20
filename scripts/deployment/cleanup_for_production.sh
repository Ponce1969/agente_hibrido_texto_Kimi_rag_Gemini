#!/bin/bash
# Script de limpieza para preparar el proyecto para producción

set -e  # Salir si hay error

echo "🧹 Iniciando limpieza del proyecto para producción..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para preguntar confirmación
confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

echo "📦 Paso 1: Limpiando cachés de Python..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
find . -type d -name '.ruff_cache' -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
echo -e "${GREEN}✅ Cachés eliminados${NC}"
echo ""

echo "📝 Paso 2: Organizando archivos de desarrollo..."

# Crear carpeta scripts/dev si no existe
mkdir -p scripts/dev

# Mover scripts de desarrollo
if [ -f "activate.sh" ]; then
    mv activate.sh scripts/dev/
    echo -e "${GREEN}✅ Movido activate.sh a scripts/dev/${NC}"
fi

if [ -f "check_dependencies.py" ]; then
    mv check_dependencies.py scripts/dev/
    echo -e "${GREEN}✅ Movido check_dependencies.py a scripts/dev/${NC}"
fi

if [ -f "verify_deployment.py" ]; then
    mv verify_deployment.py scripts/dev/
    echo -e "${GREEN}✅ Movido verify_deployment.py a scripts/dev/${NC}"
fi

echo ""

echo "📄 Paso 3: Organizando documentación..."

# Mover documentación de desarrollo a doc/
if [ -f "IMPLEMENTATION_PLAN.md" ]; then
    mv IMPLEMENTATION_PLAN.md doc/
    echo -e "${GREEN}✅ Movido IMPLEMENTATION_PLAN.md a doc/${NC}"
fi

if [ -f "REFACTORING_COMPLETE.md" ]; then
    mv REFACTORING_COMPLETE.md doc/
    echo -e "${GREEN}✅ Movido REFACTORING_COMPLETE.md a doc/${NC}"
fi

if [ -f "TESTING_SUMMARY.md" ]; then
    mv TESTING_SUMMARY.md doc/
    echo -e "${GREEN}✅ Movido TESTING_SUMMARY.md a doc/${NC}"
fi

echo ""

echo "🗑️  Paso 4: Revisando backups obsoletos..."
if [ -d "backup_obsoletos_20251006_224158" ]; then
    echo -e "${YELLOW}⚠️  Encontrado backup obsoleto: backup_obsoletos_20251006_224158/${NC}"
    if confirm "¿Deseas eliminar este backup?"; then
        rm -rf backup_obsoletos_20251006_224158
        echo -e "${GREEN}✅ Backup eliminado${NC}"
    else
        echo -e "${YELLOW}⏭️  Backup mantenido${NC}"
    fi
fi

echo ""

echo "📁 Paso 5: Verificando carpetas vacías..."

# Verificar uploads/
if [ -d "uploads" ]; then
    UPLOAD_COUNT=$(find uploads -type f | wc -l)
    if [ "$UPLOAD_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}ℹ️  uploads/ está vacío${NC}"
    else
        echo -e "${GREEN}✅ uploads/ contiene $UPLOAD_COUNT archivo(s)${NC}"
    fi
fi

# Verificar data/
if [ -d "data" ]; then
    DATA_COUNT=$(find data -type f | wc -l)
    if [ "$DATA_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}ℹ️  data/ está vacío${NC}"
    else
        echo -e "${GREEN}✅ data/ contiene $DATA_COUNT archivo(s)${NC}"
    fi
fi

echo ""

echo "🔍 Paso 6: Verificando .gitignore..."
if [ -f ".gitignore" ]; then
    # Verificar que .env está en .gitignore
    if grep -q "^\.env$" .gitignore; then
        echo -e "${GREEN}✅ .env está en .gitignore${NC}"
    else
        echo -e "${RED}❌ .env NO está en .gitignore${NC}"
        echo -e "${YELLOW}⚠️  Agrega '.env' a .gitignore para evitar subir credenciales${NC}"
    fi
    
    # Verificar que .venv está en .gitignore
    if grep -q "^\.venv" .gitignore; then
        echo -e "${GREEN}✅ .venv está en .gitignore${NC}"
    else
        echo -e "${YELLOW}⚠️  .venv debería estar en .gitignore${NC}"
    fi
else
    echo -e "${RED}❌ No se encontró .gitignore${NC}"
fi

echo ""

echo "🔒 Paso 7: Verificando seguridad..."

# Verificar que .env no está en Git
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo -e "${RED}❌ ¡PELIGRO! .env está trackeado en Git${NC}"
    echo -e "${YELLOW}⚠️  Ejecuta: git rm --cached .env${NC}"
else
    echo -e "${GREEN}✅ .env NO está en Git${NC}"
fi

echo ""

echo "="*80
echo -e "${GREEN}🎉 Limpieza completada!${NC}"
echo "="*80
echo ""

echo "📋 Resumen de la limpieza:"
echo "  ✅ Cachés de Python eliminados"
echo "  ✅ Scripts de desarrollo organizados"
echo "  ✅ Documentación organizada"
echo "  ✅ Verificaciones de seguridad completadas"
echo ""

echo "🚀 Próximos pasos:"
echo "  1. Revisar doc/CLEANUP_PRODUCTION.md para más detalles"
echo "  2. Ejecutar tests: uv run pytest -v"
echo "  3. Verificar arquitectura: uv run python scripts/check_hexagonal_architecture.py"
echo "  4. Build Docker: docker compose build"
echo "  5. Deployment: docker compose up -d"
echo ""

echo -e "${YELLOW}⚠️  Recuerda hacer backup antes de deployment a producción${NC}"
