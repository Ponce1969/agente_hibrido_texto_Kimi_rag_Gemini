-- Script SQL para verificar todas las tablas y la extensión pgvector

-- 1. Verificar extensión pgvector
\echo '🔍 Verificando extensión pgvector...'
\dx vector

-- 2. Listar todas las tablas
\echo ''
\echo '📋 Tablas en la base de datos:'
\dt

-- 3. Describir cada tabla
\echo ''
\echo '📊 Estructura de cada tabla:'

\echo ''
\echo '=== users ==='
\d users

\echo ''
\echo '=== chat_sessions ==='
\d chat_sessions

\echo ''
\echo '=== chat_messages ==='
\d chat_messages

\echo ''
\echo '=== file_uploads ==='
\d file_uploads

\echo ''
\echo '=== file_sections ==='
\d file_sections

\echo ''
\echo '=== embedding_chunks (PGVECTOR) ==='
\d embedding_chunks

\echo ''
\echo '=== metrics ==='
\d metrics

-- 4. Contar registros
\echo ''
\echo '📊 Conteo de registros por tabla:'
SELECT 'users' as tabla, COUNT(*) as registros FROM users
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM chat_sessions
UNION ALL
SELECT 'chat_messages', COUNT(*) FROM chat_messages
UNION ALL
SELECT 'file_uploads', COUNT(*) FROM file_uploads
UNION ALL
SELECT 'file_sections', COUNT(*) FROM file_sections
UNION ALL
SELECT 'embedding_chunks', COUNT(*) FROM embedding_chunks
UNION ALL
SELECT 'metrics', COUNT(*) FROM metrics;

-- 5. Verificar chunks indexados por archivo
\echo ''
\echo '📄 Chunks indexados por archivo:'
SELECT 
    fu.id as file_id,
    fu.filename_original,
    COUNT(ec.id) as chunks_count
FROM file_uploads fu
LEFT JOIN embedding_chunks ec ON ec.file_id = fu.id
GROUP BY fu.id, fu.filename_original
ORDER BY fu.id;
