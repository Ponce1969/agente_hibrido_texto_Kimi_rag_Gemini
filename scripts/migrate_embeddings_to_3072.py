"""
Script de migración para actualizar la dimensión de embeddings de 768 a 3072.

Este script es necesario porque:
- El modelo 'text-embedding-004' fue deprecado el 14 de enero de 2026
- El nuevo modelo 'gemini-embedding-001' usa 3072 dimensiones
- NO es posible alterar una columna vector en pgvector
- Por lo tanto, hay que recrear la tabla y re-indexar los PDFs

Uso:
    python scripts/migrate_embeddings_to_3072.py
"""

import sys
import os
import logging
from pathlib import Path

# Agregar el directorio raíz al path para poder importar src
_root_dir = Path(__file__).parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

OLD_DIM = 768
NEW_DIM = 3072
TABLE_NAME = "document_chunks"


def migrate():
    """Migra la tabla de embeddings a la nueva dimensión."""

    # Solicitar la URL de la base de datos
    db_url = input(
        f"\n"
        f"🔄 MIGRAR EMBEDDINGS DE {OLD_DIM} A {NEW_DIM} DIMENSIONES\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"Ingresa la URL de PostgreSQL (o presiona Enter para usar DATABASE_URL_PG del .env):\n"
        f"> "
    ).strip()

    if not db_url:
        from src.adapters.config.settings import settings

        db_url = settings.database_url_pg

    if not db_url:
        logger.error("❌ No se proporcionó URL de base de datos")
        sys.exit(1)

    # Conectar a la base de datos
    logger.info(f"🔌 Conectando a PostgreSQL...")
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # 1. Verificar que la extensión vector existe
        logger.info("📋 Verificando extensión vector...")
        result = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        if not result.fetchone():
            logger.error("❌ La extensión 'vector' no está instalada")
            sys.exit(1)
        logger.info("✅ Extensión vector instalada")

        # 2. Verificar si la tabla existe
        logger.info(f"📋 Verificando tabla '{TABLE_NAME}'...")
        result = conn.execute(
            text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{TABLE_NAME}'
            )
        """)
        )
        table_exists = result.fetchone()[0]

        if table_exists:
            # 3. Contar embeddings existentes
            result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
            count = result.fetchone()[0]
            logger.info(f"📊 Tabla '{TABLE_NAME}' existe con {count} embeddings")

            if count > 0:
                # 4. Solicitar confirmación
                logger.warning(
                    f"⚠️  ATENCIÓN: Se eliminarán {count} embeddings existentes"
                )
                confirm = input(
                    "❓ ¿Estás seguro? Escribe 'SI' para continuar: "
                ).strip()

                if confirm != "SI":
                    logger.info("❌ Migración cancelada por el usuario")
                    sys.exit(0)

                # 5. Eliminar tabla antigua
                logger.info(f"🗑️  Eliminando tabla '{TABLE_NAME}'...")
                conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE"))
                conn.commit()
                logger.info(f"✅ Tabla '{TABLE_NAME}' eliminada")
            else:
                # Tabla vacía, solo eliminarla
                logger.info(f"🗑️  Eliminando tabla '{TABLE_NAME}' vacía...")
                conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE"))
                conn.commit()
        else:
            logger.info(f"📊 Tabla '{TABLE_NAME}' no existe (primera vez)")

        # 6. Crear nueva tabla con dimensión 3072
        logger.info(f"🆕 Creando tabla '{TABLE_NAME}' con dimensión {NEW_DIM}...")
        ddl = f"""
        CREATE TABLE {TABLE_NAME} (
            id BIGSERIAL PRIMARY KEY,
            file_id INTEGER NOT NULL,
            section_id INTEGER,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector({NEW_DIM}) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            page_number INTEGER,
            section_type VARCHAR(100),
            file_name VARCHAR(500)
        );
        CREATE INDEX idx_{TABLE_NAME}_file_id ON {TABLE_NAME}(file_id);
        CREATE INDEX idx_{TABLE_NAME}_section_id ON {TABLE_NAME}(section_id);
        CREATE INDEX idx_{TABLE_NAME}_embedding ON {TABLE_NAME} USING ivfflat (embedding vector_cosine_ops);
        CREATE INDEX idx_{TABLE_NAME}_page_number ON {TABLE_NAME}(page_number);
        CREATE INDEX idx_{TABLE_NAME}_section_type ON {TABLE_NAME}(section_type);
        """
        conn.execute(text(ddl))
        conn.commit()
        logger.info(f"✅ Tabla '{TABLE_NAME}' creada con dimensión {NEW_DIM}")

    logger.info("")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("✅ MIGRACIÓN COMPLETADA")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("")
    logger.info("📝 SIGUIENTES PASOS:")
    logger.info("   1. Actualiza el código en git (si es necesario)")
    logger.info("   2. Reconstruye y reinicia los contenedores Docker")
    logger.info("   3. Ve a la aplicación y re-indexa cada PDF")
    logger.info("      (borra el PDF y súbelo de nuevo, o usa el botón de indexar)")
    logger.info("")

    engine.dispose()


if __name__ == "__main__":
    migrate()
