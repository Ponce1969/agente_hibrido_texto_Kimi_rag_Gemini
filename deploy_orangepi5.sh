#!/bin/bash
# Script de despliegue para Orange Pi 5 Plus
# Uso: ./deploy_orangepi5.sh

set -e

echo "🚀 Desplegando RAG con LLM Gateway en Orange Pi 5 Plus..."
echo "=================================================="

# 1. Verificar arquitectura ARM64
echo "📋 Verificando arquitectura..."
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    echo "⚠️  Advertencia: Este script está optimizado para ARM64 (Orange Pi 5 Plus)"
    echo "   Arquitectura detectada: $ARCH"
fi

# 2. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 3. Instalar dependencias del sistema
echo "🔧 Instalando dependencias del sistema..."
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    git \
    curl \
    wget \
    build-essential \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    supervisor

# 4. Instalar UV (gestor de paquetes Python rápido)
echo "⚡ Instalando UV..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 5. Clonar o actualizar repositorio
echo "📥 Clonando/actualizando repositorio..."
if [ -d "ragGemikimi" ]; then
    cd ragGemikimi
    git pull origin main
else
    git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git ragGemikimi
    cd ragGemikimi
fi

# 6. Crear entorno virtual con UV
echo "🐍 Creando entorno virtual..."
uv venv --python 3.12

# 7. Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
uv pip install -e .

# 8. Configurar variables de entorno
echo "⚙️  Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.template .env
    echo "📝 Por favor, edita el archivo .env con tus API keys y configuración:"
    echo "   - GROQ_API_KEY"
    echo "   - GEMINI_API_KEY"
    echo "   - BEAR_API_KEY"
    echo "   - JWT_SECRET_KEY"
    read -p "Presiona Enter cuando hayas configurado .env..."
fi

# 9. Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p data logs uploads

# 10. Inicializar base de datos
echo "🗄️  Inicializando base de datos..."
uv run python src/scripts/init_db.py

# 11. Instalar y configurar Ollama (modelos locales)
echo "🤖 Instalando Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# 12. Descargar modelos locales
echo "📥 Descargando modelos locales..."
ollama pull llama3.1:8b
ollama pull gemma:2b

# 13. Configurar servicio systemd para la API
echo "🔧 Configurando servicio de la API..."
sudo tee /etc/systemd/system/rag-api.service > /dev/null <<EOF
[Unit]
Description=RAG API con LLM Gateway
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/.venv/bin
ExecStart=$(which uv) run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 14. Configurar servicio systemd para Ollama
echo "🔧 Configurando servicio de Ollama..."
sudo systemctl enable ollama
sudo systemctl start ollama

# 15. Iniciar y habilitar servicios
echo "🚀 Iniciando servicios..."
sudo systemctl daemon-reload
sudo systemctl enable rag-api
sudo systemctl start rag-api

# 16. Configurar Nginx (opcional, para producción)
echo "🌐 Configurando Nginx..."
sudo tee /etc/nginx/sites-available/rag-api > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/rag-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 17. Verificar que todo esté funcionando
echo "🔍 Verificando servicios..."
sleep 5

# Verificar API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API funcionando correctamente"
else
    echo "❌ Error: API no responde"
    exit 1
fi

# Verificar Ollama
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama funcionando correctamente"
else
    echo "❌ Error: Ollama no responde"
    exit 1
fi

# 18. Probar LLM Gateway
echo "🧪 Probando LLM Gateway..."
curl -X POST http://localhost:8000/api/internal/llm-gateway \
    -H "Content-Type: application/json" \
    -d '{"query": "¿Qué es Python?", "mode": "rag", "session_id": 1}' \
    > /tmp/gateway_test.json

if [ $? -eq 0 ]; then
    echo "✅ LLM Gateway funcionando correctamente"
else
    echo "❌ Error: LLM Gateway no responde"
fi

# 19. Mostrar información de despliegue
echo ""
echo "🎉 ¡Despliegue completado!"
echo "============================"
echo "📍 API URL: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo "📍 LLM Gateway: http://localhost:8000/api/internal/llm-gateway"
echo "📍 Streamlit: http://localhost:8501 (iniciar con: uv run streamlit run src/adapters/streamlit/app.py)"
echo ""
echo "📊 Estado de servicios:"
echo "   API: $(systemctl is-active rag-api)"
echo "   Ollama: $(systemctl is-active ollama)"
echo "   Nginx: $(systemctl is-active nginx)"
echo ""
echo "📝 Logs:"
echo "   API: sudo journalctl -u rag-api -f"
echo "   Ollama: sudo journalctl -u ollama -f"
echo ""
echo "🔧 Comandos útiles:"
echo "   Reiniciar API: sudo systemctl restart rag-api"
echo "   Ver logs API: sudo journalctl -u rag-api -f"
echo "   Subir PDFs: http://localhost:8000/docs#/Files/upload_file_files_post"
echo ""
echo "🚀 ¡Listo para usar los modelos locales con el RAG!"
