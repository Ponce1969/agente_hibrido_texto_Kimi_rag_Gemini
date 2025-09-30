from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.adapters.api.endpoints import chat
from src.adapters.api.endpoints import files
from src.adapters.api.endpoints import pg
from src.adapters.api.endpoints import embeddings
from src.adapters.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al iniciar la aplicación
    print("Iniciando aplicación y creando tablas de la base de datos...")
    create_db_and_tables()
    yield
    # Al apagar la aplicación (si se necesita limpieza)
    print("Apagando aplicación...")


app = FastAPI(
    title="Asistente de Aprendizaje de Python con IA",
    description="Una API para interactuar con un agente de IA especializado en Python.",
    version="0.1.0",
    lifespan=lifespan,
)

# Incluir los routers de los endpoints
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])
app.include_router(pg.router, prefix="/api/v1", tags=["PostgreSQL"]) 
app.include_router(embeddings.router, prefix="/api/v1", tags=["Embeddings"]) 

# Endpoint de health check
@app.get("/health", tags=["Monitoring"])
def health_check():
    """Endpoint para verificar que la API está funcionando."""
    return {"status": "healthy", "service": "Asistente IA con RAG"}
