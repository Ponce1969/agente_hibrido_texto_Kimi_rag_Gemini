#!/usr/bin/env python3
"""
Script de migración para agregar columnas de metadatos a la tabla document_chunks.

Este script agrega las siguientes columnas:
- page_number: INTEGER
- section_type: VARCHAR(100)
- file_name: VARCHAR(500)

Y crea índices para mejorar el rendimiento de búsquedas filtradas.

Uso:
    python scripts/migrate_embeddings_add_metadata.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.adapters.db.pg_engine import get_pg_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TABLE_NAME = "document_chunks"


def migrate_add_metadata_columns() -> None:
    """Agrega columnas de metadatos a la tabla document_chunks."""
    
    engine = get_pg_engine()
    if engine is None:
        logger.error("❌ DATABASE_URL_PG no configurada. No se puede ejecutar la migración.")
        sys.exit(1)
    
    logger.info(f"🔄 Iniciando migración de {TABLE_NAME}...")
    
    try:
        with engine.begin() as conn:
            # Verificar si las columnas ya existen
            check_sql = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{TABLE_NAME}' 
                AND column_name IN ('page_number', 'section_type', 'file_name')
            """)
            
            existing_columns = {row[0] for row in conn.execute(check_sql)}
            
            if len(existing_columns) == 3:
                logger.info("✅ Las columnas de metadatos ya existen. No es necesario migrar.")
                return
            
            # Agregar columnas si no existen
            if 'page_number' not in existing_columns:
                logger.info("➕ Agregando columna page_number...")
                conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN page_number INTEGER"))
            
            if 'section_type' not in existing_columns:
                logger.info("➕ Agregando columna section_type...")
                conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN section_type VARCHAR(100)"))
            
            if 'file_name' not in existing_columns:
                logger.info("➕ Agregando columna file_name...")
                conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN file_name VARCHAR(500)"))
            
            # Crear índices para mejorar rendimiento
            logger.info("📊 Creando índices...")
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_page_number 
                ON {TABLE_NAME}(page_number)
            """))
            
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_section_type 
                ON {TABLE_NAME}(section_type)
            """))
            
            logger.info("✅ Migración completada exitosamente")
            
            # Mostrar estadísticas
            count_sql = text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            total_chunks = conn.execute(count_sql).scalar()
            logger.info(f"📊 Total de chunks en la tabla: {total_chunks}")
            
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        raise


if __name__ == "__main__":
    logger.info("🚀 Iniciando script de migración de embeddings...")
    migrate_add_metadata_columns()
    logger.info("🎉 Script completado")
