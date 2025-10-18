#!/bin/bash
# Script para verificar las tablas en PostgreSQL del servidor

echo "🔍 Verificando tablas en PostgreSQL..."
echo ""

# Conectarse al contenedor de PostgreSQL y listar tablas
docker exec -it agente_hibrido_texto_kimi_rag_gemini-postgres-1 psql -U postgres -d agente_db -c "\dt"

echo ""
echo "🔍 Verificando extensión pgvector..."
docker exec -it agente_hibrido_texto_kimi_rag_gemini-postgres-1 psql -U postgres -d agente_db -c "\dx"

echo ""
echo "🔍 Contando registros en cada tabla..."
docker exec -it agente_hibrido_texto_kimi_rag_gemini-postgres-1 psql -U postgres -d agente_db -c "
SELECT 
    schemaname,
    tablename,
    (SELECT COUNT(*) FROM pg_catalog.pg_class c WHERE c.relname = tablename) as row_count
FROM pg_catalog.pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY tablename;
"

echo ""
echo "🔍 Verificando tabla embedding_chunks (pgvector)..."
docker exec -it agente_hibrido_texto_kimi_rag_gemini-postgres-1 psql -U postgres -d agente_db -c "
SELECT 
    COUNT(*) as total_chunks,
    COUNT(DISTINCT file_id) as total_files
FROM embedding_chunks;
"
