# 🔧 Configuración del Entorno de Desarrollo

## 🎯 Entorno Virtual con uv

Este proyecto utiliza **uv** como gestor de dependencias y entornos virtuales. uv es una herramienta moderna, rápida y compatible con pip.

### **Activación del Entorno Virtual**

#### **Método Rápido (Recomendado)**
```bash
# Usar el script de activación automática
source activate.sh
```

#### **Método Manual**
```bash
# Activar el entorno virtual
source .venv/bin/activate

# Verificar que está activado
which python  # Debe mostrar: /ruta/al/proyecto/.venv/bin/python
python --version  # Debe mostrar la versión de Python del proyecto
```

### **Recreación del Entorno Virtual**

Si el entorno virtual se pierde o tiene problemas:

```bash
# Recrear el entorno virtual e instalar dependencias
uv sync

# Activar el nuevo entorno
source .venv/bin/activate
```

### **Comandos Útiles de uv**

```bash
# Instalar nuevas dependencias
uv add nombre_del_paquete

# Actualizar dependencias
uv sync --upgrade

# Ver packages instalados
uv pip list

# Exportar requirements.txt (si es necesario)
uv export --format requirements-txt > requirements.txt
```

### **Verificación del Entorno**

Una vez activado, verifica que todo funciona:

```bash
# Verificar Python
python --version

# Verificar que las dependencias están instaladas
python -c "import fastapi, streamlit, groq; print('✅ Todas las dependencias instaladas')"

# Verificar que el proyecto funciona
python -m pytest --version  # Para testing
```

### **Desactivación**

```bash
# Desactivar el entorno virtual
deactivate
```

### **Solución de Problemas**

#### **Problema: "No existe el archivo o directorio .venv/bin/activate"**
**Solución:**
```bash
# Recrear el entorno virtual
uv sync

# Luego activar
source .venv/bin/activate
```

#### **Problema: "uv command not found"**
**Solución:** Instalar uv
```bash
# En Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# En Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Luego reiniciar la terminal
```

#### **Problema: Permisos en Linux/macOS**
**Solución:**
```bash
# Hacer el script ejecutable
chmod +x activate.sh

# O activar directamente
source .venv/bin/activate
```

---

## 🐳 Docker (Alternativa)

Si prefieres usar Docker sin entorno virtual:

```bash
# Lanzar todo con Docker
docker-compose up --build

# Acceso:
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000
# - Documentación: http://localhost:8000/docs
```


## 🔐 Variables de Entorno (.env)

Asegúrate de crear un archivo `.env` en la raíz del proyecto con tus credenciales y configuración. Ejemplo:

```env
# API Keys para IA
GROQ_API_KEY=tu_api_key_groq
GEMINI_API_KEY=tu_api_key_gemini

# Backend URL para Streamlit (en Docker, el frontend habla a "backend")
BACKEND_URL=http://backend:8000/api/v1

# Control de contexto
FILE_CONTEXT_MAX_CHARS=6000
MESSAGES_MAX_CHARS=10000

# Base de datos SQLite (historial de chat y metadatos de PDFs)
# DATABASE_URL por defecto: sqlite:///./data/chat_history.db (no es necesario declararla)

# PostgreSQL + pgvector (opcional para embeddings)
POSTGRES_DB=pg_data
POSTGRES_USER=agentehibrido
POSTGRES_PASSWORD=tu_password
DATABASE_URL_PG=postgresql+psycopg2://agentehibrido:tu_password@postgres:5432/pg_data
```

Notas:
- Dentro de Docker, el host para Postgres es `postgres` (nombre del servicio en docker-compose).
- Si usas caracteres especiales en la contraseña, URL-encódelos (por ejemplo `@` -> `%40`).
- El archivo `.env` está en `.gitignore` y no se sube al repositorio.


## 🧪 Verificación de PostgreSQL + pgvector

Después de levantar Docker, valida la conexión y la extensión `vector` con el endpoint de salud del backend:

```bash
curl http://localhost:8000/api/v1/pg/health
# Debe responder algo como:
{"configured":true,"connected":true,"pgvector_installed":true}
```

Si `configured` es `false`, revisa que `DATABASE_URL_PG` esté presente en `.env` y reinicia el backend.


## 📝 Exportación de Chat (PDF/Markdown)

La UI de Streamlit permite descargar el chat como Markdown (sin dependencias extra) y como PDF (requiere `reportlab`).
Si el botón de PDF aparece deshabilitado tras levantar, reconstruye las imágenes para asegurar la instalación de dependencias:

```bash
docker-compose build
docker-compose up
```

---

## 📝 Notas Importantes

1. **El directorio `.venv` está en `.gitignore`** - No se sube a Git
2. **Usa siempre el entorno virtual** - Evita conflictos de dependencias
3. **El script `activate.sh` es automático** - Detecta y recrea el entorno si es necesario
4. **uv es compatible con pip** - Puedes usar comandos pip dentro del entorno uv

---

**💡 Consejo:** Usa `source activate.sh` para la activación más fácil y confiable.
