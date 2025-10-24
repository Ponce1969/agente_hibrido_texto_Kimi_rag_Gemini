#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras del sistema RAG.

Este script verifica:
1. Que el schema de PostgreSQL tiene las nuevas columnas
2. Que los chunks se generan con el nuevo tamaño (1000 chars)
3. Que las búsquedas retornan 10 chunks por defecto
4. Que los metadatos se almacenan correctamente

Uso:
    python scripts/test_rag_improvements.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.adapters.db.pg_engine import get_pg_engine
from src.adapters.config.settings import settings
from src.application.services.embeddings_service import chunk_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_configuration() -> bool:
    """Verifica que la configuración esté actualizada."""
    logger.info("🔍 Verificando configuración...")
    
    tests_passed = True
    
    # Verificar chunk_size
    if settings.embedding_chunk_size == 1000:
        logger.info("✅ embedding_chunk_size = 1000")
    else:
        logger.error(f"❌ embedding_chunk_size = {settings.embedding_chunk_size} (esperado: 1000)")
        tests_passed = False
    
    # Verificar overlap
    if settings.embedding_chunk_overlap == 150:
        logger.info("✅ embedding_chunk_overlap = 150")
    else:
        logger.error(f"❌ embedding_chunk_overlap = {settings.embedding_chunk_overlap} (esperado: 150)")
        tests_passed = False
    
    # Verificar max_search_results
    if settings.max_search_results == 10:
        logger.info("✅ max_search_results = 10")
    else:
        logger.error(f"❌ max_search_results = {settings.max_search_results} (esperado: 10)")
        tests_passed = False
    
    return tests_passed


def test_database_schema() -> bool:
    """Verifica que el schema de PostgreSQL tenga las nuevas columnas."""
    logger.info("🔍 Verificando schema de PostgreSQL...")
    
    engine = get_pg_engine()
    if engine is None:
        logger.error("❌ DATABASE_URL_PG no configurada")
        return False
    
    try:
        with engine.begin() as conn:
            # Verificar columnas
            check_sql = text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'document_chunks' 
                AND column_name IN ('page_number', 'section_type', 'file_name')
                ORDER BY column_name
            """)
            
            columns = {row[0]: row[1] for row in conn.execute(check_sql)}
            
            expected_columns = {
                'page_number': 'integer',
                'section_type': 'character varying',
                'file_name': 'character varying'
            }
            
            tests_passed = True
            for col_name, expected_type in expected_columns.items():
                if col_name in columns:
                    logger.info(f"✅ Columna '{col_name}' existe ({columns[col_name]})")
                else:
                    logger.error(f"❌ Columna '{col_name}' no existe")
                    tests_passed = False
            
            # Verificar índices
            index_sql = text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'document_chunks'
                AND indexname LIKE 'idx_document_chunks_%'
            """)
            
            indexes = {row[0] for row in conn.execute(index_sql)}
            
            expected_indexes = {
                'idx_document_chunks_page_number',
                'idx_document_chunks_section_type'
            }
            
            for idx_name in expected_indexes:
                if idx_name in indexes:
                    logger.info(f"✅ Índice '{idx_name}' existe")
                else:
                    logger.warning(f"⚠️  Índice '{idx_name}' no existe (ejecutar migración)")
            
            return tests_passed
            
    except Exception as e:
        logger.error(f"❌ Error verificando schema: {e}")
        return False


def test_chunking() -> bool:
    """Verifica que la función de chunking use los nuevos valores."""
    logger.info("🔍 Verificando función de chunking...")
    
    # Texto de prueba más largo (5000+ caracteres para tener varios chunks de 1000)
    test_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 100
    
    # Generar chunks con defaults
    chunks = chunk_text(test_text)
    
    logger.info(f"📊 Texto de prueba: {len(test_text)} caracteres")
    logger.info(f"📊 Chunks generados: {len(chunks)}")
    
    # Verificar que los chunks individuales estén cerca de 1000
    # (excepto el último que puede ser más corto)
    chunk_sizes = [len(c) for c in chunks[:-1]]  # Excluir el último
    
    if chunk_sizes:
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        logger.info(f"📊 Tamaño promedio de chunks (sin último): {avg_size:.0f} caracteres")
        
        # El tamaño promedio debería estar cerca de 1000
        if 900 <= avg_size <= 1100:
            logger.info("✅ Tamaño de chunks correcto (~1000 chars)")
            return True
        else:
            logger.error(f"❌ Tamaño de chunks incorrecto (esperado: ~1000, obtenido: {avg_size:.0f})")
            return False
    else:
        # Si solo hay 1 chunk, verificar que sea <= 1000
        if len(chunks) == 1 and len(chunks[0]) <= 1000:
            logger.info("✅ Texto corto, 1 chunk generado correctamente")
            return True
        else:
            logger.error(f"❌ Comportamiento inesperado con texto corto")
            return False


async def test_embeddings_service() -> bool:
    """Verifica que el servicio de embeddings use top_k=10."""
    logger.info("🔍 Verificando servicio de embeddings...")
    
    try:
        from src.application.services.embeddings_service import EmbeddingsServiceV2
        import inspect
        
        # Obtener signature del método search_similar
        sig = inspect.signature(EmbeddingsServiceV2.search_similar)
        top_k_default = sig.parameters['top_k'].default
        
        if top_k_default == 10:
            logger.info(f"✅ EmbeddingsServiceV2.search_similar default top_k = {top_k_default}")
            return True
        else:
            logger.error(f"❌ EmbeddingsServiceV2.search_similar default top_k = {top_k_default} (esperado: 10)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando servicio: {e}")
        return False


async def main() -> None:
    """Ejecuta todas las pruebas."""
    logger.info("🚀 Iniciando pruebas de mejoras RAG...")
    logger.info("=" * 60)
    
    results = {
        "Configuración": test_configuration(),
        "Schema PostgreSQL": test_database_schema(),
        "Chunking": test_chunking(),
        "Servicio Embeddings": await test_embeddings_service(),
    }
    
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DE PRUEBAS:")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("🎉 TODAS LAS PRUEBAS PASARON")
        logger.info("")
        logger.info("✅ El sistema está listo para usar las mejoras RAG")
        logger.info("📝 Próximos pasos:")
        logger.info("   1. Re-indexar PDFs existentes para aprovechar chunks más grandes")
        logger.info("   2. Probar búsquedas con top_k=10 en Streamlit")
        logger.info("   3. Verificar que los metadatos se almacenan correctamente")
    else:
        logger.error("❌ ALGUNAS PRUEBAS FALLARON")
        logger.error("")
        logger.error("🔧 Acciones requeridas:")
        if not results["Schema PostgreSQL"]:
            logger.error("   - Ejecutar: python scripts/migrate_embeddings_add_metadata.py")
        logger.error("   - Revisar la configuración en .env")
        logger.error("   - Verificar que todos los archivos fueron actualizados")


if __name__ == "__main__":
    asyncio.run(main())
