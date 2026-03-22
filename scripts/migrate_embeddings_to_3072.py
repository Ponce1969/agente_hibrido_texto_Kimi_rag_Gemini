"""
Script de verificación/migración para embeddings.

SITUACIÓN ACTUAL:
- El modelo 'text-embedding-004' fue DEPRECADO el 14 de enero de 2026
- El nuevo modelo 'gemini-embedding-001' usa MRL (Matryoshka Representation Learning)
- Ambos usan 768 dimensiones - la tabla de PostgreSQL NO necesita recrearse

LO QUE HAY QUE HACER:
1. ✅ Actualizar el código (ya hecho) - usar gemini-embedding-001 con MRL
2. ✅ Reconstruir la imagen Docker
3. ⚠️  Re-indexar los PDFs existentes (los embeddings antiguos son incompatibles)

Los 668 embeddings existentes fueron creados con text-embedding-004 que ya no existe.
Para que RAG funcione correctamente, hay que borrar y re-indexar los PDFs.
"""

import sys
import os
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🔄 VERIFICACIÓN DE MIGRACIÓN DE EMBEDDINGS")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("")

    # Verificar que podemos importar las dependencias
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))

        # Intentar conectar a PostgreSQL para verificar
        from sqlalchemy import create_engine, text
        from src.adapters.config.settings import settings

        db_url = settings.database_url_pg
        if not db_url:
            logger.error("❌ DATABASE_URL_PG no está configurada en .env")
            sys.exit(1)

        logger.info(f"🔌 Verificando conexión a PostgreSQL...")
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Verificar extensión vector
            result = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            if not result.fetchone():
                logger.error("❌ Extensión 'vector' no está instalada")
                sys.exit(1)
            logger.info("✅ Extensión vector instalada")

            # Verificar tabla
            result = conn.execute(
                text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'document_chunks' AND column_name = 'embedding'
            """)
            )
            col = result.fetchone()

            if col:
                logger.info(f"📊 Tabla 'document_chunks' existe")

                # Contar embeddings
                result = conn.execute(text("SELECT COUNT(*) FROM document_chunks"))
                count = result.fetchone()[0]
                logger.info(f"📊 Embeddings existentes: {count}")

                if count > 0:
                    logger.warning("")
                    logger.warning("⚠️  ATENCIÓN:")
                    logger.warning(
                        f"   Tienes {count} embeddings creados con text-embedding-004"
                    )
                    logger.warning(
                        "   Ese modelo YA NO EXISTE (deprecated el 14/ene/2026)"
                    )
                    logger.warning("")
                    logger.warning("   OPCIONES:")
                    logger.warning(
                        "   1. Mantener los embeddings (búsquedas pueden ser imprecisas)"
                    )
                    logger.warning(
                        "   2. Re-indexar los PDFs (recomendado para precisión)"
                    )
                    logger.warning("")
            else:
                logger.info("📊 Tabla 'document_chunks' no existe todavía")
                logger.info("   Se creará automáticamente cuando indexes el primer PDF")

        engine.dispose()

        logger.info("")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("✅ VERIFICACIÓN COMPLETADA")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("")
        logger.info("📝 SIGUIENTES PASOS:")
        logger.info("   1. Actualiza el código: git pull")
        logger.info("   2. Reconstruye Docker: docker compose build backend --no-cache")
        logger.info("   3. Reinicia: docker compose up -d backend")
        logger.info("   4. Ve a la app y RE-INDEXA tus PDFs (borrar y subir de nuevo)")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
