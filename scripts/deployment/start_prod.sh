#!/bin/bash

# 🚀 PRODUCCIÓN: Gunicorn + Uvicorn workers (4 workers)

echo "🚀 Iniciando servidor de producción..."
echo "   Server: Gunicorn + Uvicorn workers"
echo "   Workers: 4"
echo ""

uv run gunicorn src.main:app \
    --config gunicorn.conf.py
