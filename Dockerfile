# Etapa 1: Build - Instalar dependencias
FROM python:3.12-slim as builder

# Variables de optimización para build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar uv sin cache
RUN pip install --no-cache-dir uv

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instalar SOLO dependencias de producción (sin dev) y limpiar
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv sync --no-dev && \
    # Limpiar caches para reducir tamaño
    rm -rf /root/.cache /tmp/* /var/tmp/*

# Etapa 2: Final - Crear la imagen de producción
FROM python:3.12-slim

# Variables de optimización para runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2 \
    PATH="/app/.venv/bin:$PATH" \
    # Optimizaciones de memoria para ML/transformers
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=2

# Instalar curl para health checks y limpiar en una sola capa
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el entorno virtual con las dependencias desde la etapa de build
COPY --from=builder /app/.venv ./.venv

# Copiar SOLO el código fuente necesario (sin .env, se pasa por docker-compose)
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY gunicorn.conf.py ./
COPY .streamlit/ ./.streamlit/

# Crear directorio de datos
RUN mkdir -p /app/data

# Exponer los puertos para FastAPI y Streamlit
EXPOSE 8000
EXPOSE 8501

# Por defecto, inicia el backend con Gunicorn (producción)
# El comando puede ser sobreescrito en docker-compose
CMD ["gunicorn", "src.main:app", "--config", "gunicorn.conf.py"]
