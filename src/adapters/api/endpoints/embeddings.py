"""
Embeddings endpoints:
 - init: asegura tablas e índices (pgvector)
 - index: indexa un file_id previamente procesado en secciones (SQLite) y guarda embeddings en Postgres
 - search: búsqueda top-k por similitud (cosine) opcionalmente filtrada por file_id
"""
from fastapi import APIRouter, HTTPException, Query

from src.adapters.db.embeddings_repository import EmbeddingsRepository
from src.adapters.db.pg_engine import get_pg_engine
from src.adapters.dependencies import get_embeddings_service

router = APIRouter()


@router.get("/embeddings/health", tags=["Embeddings"], summary="Verifica el estado del sistema de embeddings")
def embeddings_health():
    """Verifica la conexión a PostgreSQL y el estado del sistema de embeddings."""
    engine = get_pg_engine()
    if engine is None:
        return {
            "configured": False,
            "message": "DATABASE_URL_PG no configurado",
            "embedding_model": "Gemini text-embedding-004",
            "embedding_dim": 768
        }
    
    try:
        repo = EmbeddingsRepository()
        # Verificar que podemos conectar y contar
        total_chunks = repo.count_chunks(None)  # Contar todos los chunks
        
        return {
            "configured": True,
            "connected": True,
            "embedding_model": "Gemini text-embedding-004",
            "embedding_dim": 768,
            "total_chunks_indexed": total_chunks,
            "message": "Sistema de embeddings funcionando correctamente"
        }
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "error": str(e),
            "message": f"Error en sistema de embeddings: {e}"
        }


@router.post("/embeddings/init", tags=["Embeddings"], summary="Crea tablas e índices de embeddings en PostgreSQL")
def embeddings_init():
    engine = get_pg_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="DATABASE_URL_PG no configurado")
    try:
        repo = EmbeddingsRepository()
        repo.ensure_schema()
        return {"status": "ok", "message": "Schema de embeddings asegurado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando esquema: {e}")


@router.post("/embeddings/index/{file_id}", tags=["Embeddings"], summary="Indexa (chunking + embeddings) un PDF ya procesado en secciones")
async def embeddings_index(file_id: int):
    engine = get_pg_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="DATABASE_URL_PG no configurado")
    try:
        # Usar servicio NUEVO con Gemini embeddings (768 dims)
        from sqlmodel import Session as SQLSession, select
        from src.adapters.db.database import engine as sqlite_engine
        from src.adapters.db.file_models import FileUpload, FileSection
        from src.domain.models.file_models import FileDocument, FileSection as DomainSection, FileStatus as DomainStatus
        
        svc = get_embeddings_service()
        
        # 1. Obtener file desde SQLite
        with SQLSession(sqlite_engine) as session:
            fu = session.get(FileUpload, file_id)
            if not fu:
                raise HTTPException(status_code=404, detail="Archivo no encontrado")
            
            # 2. Extraer texto del PDF con PyPDF
            try:
                from pypdf import PdfReader
                import io
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"PyPDF no disponible: {e}")
            
            with open(fu.path, "rb") as f:
                raw = f.read()
            reader = PdfReader(io.BytesIO(raw))
            
            if getattr(reader, "is_encrypted", False):
                try:
                    reader.decrypt("")
                except Exception:
                    raise HTTPException(status_code=400, detail="PDF cifrado y no pudo ser leído")
            
            # 3. Obtener secciones desde SQLite
            sections = session.exec(select(FileSection).where(FileSection.file_id == file_id).order_by(FileSection.start_page)).all()
            
            if not sections:
                raise HTTPException(status_code=400, detail="Archivo sin secciones procesadas")
            
            # 4. Extraer texto de cada sección y crear modelos de dominio
            domain_sections = []
            for sec in sections:
                # Extraer texto de las páginas de esta sección
                text_parts = []
                for page_idx in range(sec.start_page, sec.end_page + 1):
                    try:
                        page_text = reader.pages[page_idx].extract_text() or ""
                        text_parts.append(page_text)
                    except Exception as e:
                        print(f"⚠️ Error extrayendo página {page_idx}: {e}")
                
                section_text = "\n".join(text_parts).strip()
                if section_text:
                    domain_sections.append(
                        DomainSection(
                            id=sec.id,
                            file_id=str(sec.file_id),
                            text=section_text,
                            page_number=sec.start_page,
                            chunk_index=0,
                        )
                    )
            
            if not domain_sections:
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")
            
            # 5. Crear FileDocument
            file_doc = FileDocument(
                id=str(fu.id),
                filename=fu.filename_original,
                file_path=fu.path,
                status=DomainStatus.INDEXED,
                created_at=fu.created_at,
            )
        
        # 6. Indexar con Gemini embeddings (768 dims)
        inserted = await svc.index_document(file_doc, domain_sections)
        return {"status": "ok", "file_id": file_id, "inserted_chunks": inserted}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error indexando archivo: {e}\n{tb}")


@router.get("/embeddings/search", tags=["Embeddings"], summary="Búsqueda top-k por similitud en embeddings")
async def embeddings_search(q: str = Query(..., description="Consulta de texto"), file_id: int | None = Query(None), top_k: int = Query(5, ge=1, le=50)):
    engine = get_pg_engine()
    if engine is None:
        raise HTTPException(status_code=400, detail="DATABASE_URL_PG no configurado")
    try:
        # Usar servicio nuevo con Gemini embeddings
        svc = get_embeddings_service()
        
        # Buscar chunks similares
        results = await svc.search_similar(
            query=q,
            file_id=str(file_id) if file_id else None,
            top_k=top_k
        )
        
        return {
            "query": q,
            "file_id": file_id,
            "top_k": top_k,
            "results": results,  # EmbeddingsServiceV2 ya retorna dict
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {e}\n{tb}")
