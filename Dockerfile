# Etapa 1: Build - Instalar dependencias
FROM python:3.12-slim as builder

# Instalar uv
RUN pip install uv

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instalar dependencias en un venv
RUN uv venv /app/.venv &&     . /app/.venv/bin/activate &&     uv sync

# Etapa 2: Final - Crear la imagen de producción
FROM python:3.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el entorno virtual con las dependencias desde la etapa de build
COPY --from=builder /app/.venv ./.venv

# Activar el venv para los comandos subsiguientes
ENV PATH="/app/.venv/bin:$PATH"

# Copiar el código fuente de la aplicación
COPY src/ ./src
COPY scripts/ ./scripts
COPY gunicorn.conf.py ./
COPY .env ./
COPY .streamlit/ ./.streamlit/

# Exponer los puertos para FastAPI y Streamlit
EXPOSE 8000
EXPOSE 8501

# Por defecto, inicia el backend con Gunicorn (producción)
# El comando puede ser sobreescrito en docker-compose
CMD ["gunicorn", "src.main:app", "--config", "gunicorn.conf.py"]
