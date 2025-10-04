"""
Script de migración para actualizar dimensión de embeddings.

Migra de 384 dimensiones (all-MiniLM-L6-v2) a 768 dimensiones (Gemini).

IMPORTANTE: Este script eliminará los embeddings existentes porque
no es posible convertir vectores de 384 a 768 dimensiones.
"""

from __future__ import annotations

from sqlalchemy import text

from src.adapters.db.pg_engine import get_pg_engine


OLD_DIMENSION = 384
NEW_DIMENSION = 768
TABLE_NAME = "document_chunks"


def migrate_embedding_dimension() -> None:
    """
    Migra la dimensión de embeddings de 384 a 768.
    
    Pasos:
    1. Elimina la tabla existente (con embeddings de 384 dims)
    2. Crea nueva tabla con 768 dims
    3. Crea índices optimizados
    """
    engine = get_pg_engine()
    
    if not engine:
        raise RuntimeError("PostgreSQL no configurado")
    
    print(f"🔄 Migrando embeddings de {OLD_DIMENSION} a {NEW_DIMENSION} dimensiones...")
    
    with engine.begin() as conn:
        # 1. Eliminar tabla existente
        print(f"📦 Eliminando tabla {TABLE_NAME} existente...")
        conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE"))
        
        # 2. Crear nueva tabla con 768 dimensiones
        print(f"✨ Creando tabla {TABLE_NAME} con {NEW_DIMENSION} dimensiones...")
        ddl = f"""
        CREATE TABLE {TABLE_NAME} (
            id BIGSERIAL PRIMARY KEY,
            file_id INTEGER NOT NULL,
            section_id INTEGER,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector({NEW_DIMENSION}) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
        """
        conn.execute(text(ddl))
        
        # 3. Crear índices
        print("🔍 Creando índices...")
        
        # Índice para file_id
        conn.execute(text(
            f"CREATE INDEX idx_{TABLE_NAME}_file_id ON {TABLE_NAME}(file_id)"
        ))
        
        # Índice para section_id
        conn.execute(text(
            f"CREATE INDEX idx_{TABLE_NAME}_section_id ON {TABLE_NAME}(section_id)"
        ))
        
        # Índice vectorial (IVFFlat para búsqueda rápida)
        conn.execute(text(
            f"CREATE INDEX idx_{TABLE_NAME}_embedding "
            f"ON {TABLE_NAME} USING ivfflat (embedding vector_cosine_ops)"
        ))
        
        print("✅ Migración completada exitosamente!")
        print(f"📊 Nueva dimensión: {NEW_DIMENSION}")
        print("⚠️  Nota: Los embeddings existentes fueron eliminados.")
        print("   Deberás re-indexar tus documentos con el nuevo modelo.")


if __name__ == "__main__":
    migrate_embedding_dimension()
