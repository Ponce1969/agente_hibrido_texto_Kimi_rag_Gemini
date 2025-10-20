#!/bin/bash

# 🔧 DESARROLLO: Uvicorn con hot-reload (1 worker)

echo "🔧 Iniciando servidor de desarrollo..."
echo "   Hot-reload: ✅"
echo "   Workers: 1"
echo ""

uv run uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir src
