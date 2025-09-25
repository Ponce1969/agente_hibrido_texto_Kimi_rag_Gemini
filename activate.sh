#!/bin/bash
# Script para activar el entorno virtual de uv
# Uso: source activate.sh

echo "🔧 Activando entorno virtual con uv..."

# Verificar si existe el entorno virtual
if [ ! -f ".venv/bin/activate" ]; then
    echo "⚠️  Entorno virtual no encontrado. Recreando..."
    uv sync
    echo "✅ Entorno virtual recreado"
fi

# Activar el entorno virtual
source .venv/bin/activate
echo "✅ Entorno virtual activado correctamente"
echo "🐍 Python: $(which python)"
echo "📦 Ubicación: $(python -c 'import sys; print(sys.prefix)')"

# Mostrar comandos útiles
echo ""
echo "💡 Comandos útiles:"
echo "   • Desactivar: deactivate"
echo "   • Ver packages: uv pip list"
echo "   • Lanzar app: docker-compose up --build"
echo "   • Ver estado: git status"
