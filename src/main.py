from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.adapters.api.endpoints import chat
from src.adapters.api.endpoints import files
from src.adapters.api.endpoints import pg
from src.adapters.api.endpoints import embeddings
from src.adapters.api.endpoints import chat_bear
from src.adapters.api.endpoints import metrics
from src.adapters.api.endpoints import auth
from src.adapters.api.endpoints import guardian
from src.adapters.db.database import create_db_and_tables
from src.adapters.api.middleware.guardian_middleware import GuardianMiddleware
from src.adapters.dependencies import get_guardian_service_for_middleware
from src.adapters.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al iniciar la aplicación
    print("Iniciando aplicación y creando tablas de la base de datos...")
    create_db_and_tables()
    
    # Crear tabla de embeddings (pgvector)
    try:
        from src.adapters.db.embeddings_repository import EmbeddingsRepository
        embeddings_repo = EmbeddingsRepository()
        embeddings_repo.ensure_schema()
        print("✅ Tabla document_chunks creada/verificada con pgvector")
    except Exception as e:
        print(f"⚠️ No se pudo crear tabla de embeddings: {e}")
    
    yield
    # Al apagar la aplicación (si se necesita limpieza)
    print("Apagando aplicación...")


# Configurar Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Asistente de Aprendizaje de Python con IA",
    description="Una API para interactuar con un agente de IA especializado en Python.",
    version="0.1.0",
    lifespan=lifespan,
)

# Agregar Rate Limiter al estado de la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 🛡️ Agregar Guardian Middleware (ANTES de CORS)
if settings.guardian_enabled:
    print("🛡️ Guardian de seguridad activado")
    app.add_middleware(
        GuardianMiddleware,
        guardian_service=get_guardian_service_for_middleware(),
        enabled=settings.guardian_enabled
    )
else:
    print("⚠️ Guardian de seguridad desactivado")

# Configurar CORS mejorado
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit local (desarrollo)
        "http://localhost:3000",  # React local (si aplica)
        "https://app3.loquinto.com",  # Frontend Streamlit en producción (Cloudflare Tunnel)
        "https://api3.loquinto.com",  # Backend FastAPI en producción (Cloudflare Tunnel)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Incluir los routers de los endpoints
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])
app.include_router(pg.router, prefix="/api/v1", tags=["PostgreSQL"]) 
app.include_router(embeddings.router, prefix="/api/v1", tags=["Embeddings"])
app.include_router(chat_bear.router, prefix="/api/v1")  # Bear Search (tag definido en el router)
app.include_router(metrics.router, prefix="/api/v1")  # Métricas de tokens (tag definido en el router)
app.include_router(guardian.router, prefix="/api/v1")  # Guardian de seguridad 

# Endpoint de health check
@app.get("/health", tags=["Monitoring"])
def health_check():
    """Endpoint para verificar que la API está funcionando."""
    return {"status": "healthy", "service": "Asistente IA con RAG"}
