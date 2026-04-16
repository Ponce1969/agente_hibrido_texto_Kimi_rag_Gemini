"""
Repository for managing document embeddings in PostgreSQL with pgvector.

Responsibilities (Step 1 - RAG):
- Ensure schema and indexes exist.
- Insert (bulk) chunks with embeddings.
- Query top-k similar chunks by embedding.

Notes:
- Uses a dedicated PostgreSQL engine from `pg_engine.get_pg_engine()`.
- The table maintains only logical references to the SQLite entities (file_id, section_id).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from sqlalchemy import text

from src.adapters.db.embeddings_models import EmbeddingChunk, SimilarChunk
from src.adapters.db.pg_engine import get_pg_engine

EMBEDDING_DIM = (
    768  # Gemini gemini-embedding-001 with MRL output at 768 dims (HNSW max is 2000)
)
TABLE_NAME = "document_chunks"


class EmbeddingsRepository:
    def __init__(self) -> None:
        engine = get_pg_engine()
        if engine is None:
            raise RuntimeError(
                "DATABASE_URL_PG is not configured. EmbeddingsRepository requires PostgreSQL."
            )
        self.engine = engine

    def ensure_schema(self) -> None:
        """Create table and indexes if they don't exist."""
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id BIGSERIAL PRIMARY KEY,
            file_id INTEGER NOT NULL,
            section_id INTEGER,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector({EMBEDDING_DIM}) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            page_number INTEGER,
            section_type VARCHAR(100),
            file_name VARCHAR(500)
        );
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_file_id ON {TABLE_NAME}(file_id);
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_section_id ON {TABLE_NAME}(section_id);
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_embedding ON {TABLE_NAME} USING hnsw (embedding vector_cosine_ops);
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_page_number ON {TABLE_NAME}(page_number);
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_section_type ON {TABLE_NAME}(section_type);
        """
        with self.engine.begin() as conn:
            # Ensure extension exists (noop if already enabled)
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(text(ddl))

    def delete_file_chunks(self, file_id: int) -> int:
        """Delete all chunks for a given file_id. Returns number of deleted rows."""
        with self.engine.begin() as conn:
            res = conn.execute(
                text(f"DELETE FROM {TABLE_NAME} WHERE file_id = :fid"), {"fid": file_id}
            )
            return res.rowcount or 0

    def delete_chunks_by_file(self, file_id: int) -> int:
        """Alias for delete_file_chunks for consistency."""
        return self.delete_file_chunks(file_id)

    def count_chunks(self, file_id: int | None = None) -> int:
        """Return number of chunks already indexed for a file_id. If file_id is None, count all chunks."""
        if file_id is None:
            sql = text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            params = {}
        else:
            sql = text(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE file_id = :fid")
            params = {"fid": file_id}

        with self.engine.begin() as conn:
            res = conn.execute(sql, params).fetchone()
            return int(res[0]) if res is not None else 0

    def insert_chunks(self, chunks: Iterable[EmbeddingChunk]) -> int:
        """Bulk insert chunks. Returns number of inserted rows.
        Assumes `ensure_schema()` has been called.
        """
        rows = []
        for ch in chunks:
            embedding_list = list(ch.embedding)

            # Validar dimensión del vector antes de insertar
            if len(embedding_list) != EMBEDDING_DIM:
                raise ValueError(
                    f"Dimensión de embedding inválida: {len(embedding_list)} "
                    f"(esperado: {EMBEDDING_DIM})"
                )

            rows.append(
                {
                    "file_id": ch.file_id,
                    "section_id": ch.section_id,
                    "chunk_index": ch.chunk_index,
                    "content": ch.content,
                    "embedding": embedding_list,
                    "page_number": ch.page_number,
                    "section_type": ch.section_type,
                    "file_name": ch.file_name,
                }
            )
        if not rows:
            return 0
        sql = text(
            f"""
            INSERT INTO {TABLE_NAME} (file_id, section_id, chunk_index, content, embedding, page_number, section_type, file_name)
            VALUES (:file_id, :section_id, :chunk_index, :content, :embedding, :page_number, :section_type, :file_name)
            """
        )
        with self.engine.begin() as conn:
            conn.execute(sql, rows)
        return len(rows)

    def search_top_k(
        self,
        query_embedding: Sequence[float],
        file_id: int | None = None,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SimilarChunk]:
        """Return top-k most similar chunks using cosine distance (<=>).
        If file_id is provided, the search is filtered to that file.
        If min_similarity is provided (0.0-1.0), results below this threshold are excluded.

        IMPORTANTE: Usar <=> (coseno) para que match con el índice HNSW
        creado con vector_cosine_ops. Usar <-> (L2) ignoraría el índice.
        """
        query_list = list(query_embedding)
        if len(query_list) != EMBEDDING_DIM:
            raise ValueError(
                f"Dimensión de query_embedding inválida: {len(query_list)} "
                f"(esperado: {EMBEDDING_DIM})"
            )

        embedding_str = "[" + ",".join(str(x) for x in query_list) + "]"
        params: dict[str, int | float | str] = {
            "k": top_k,
            "embedding_vec": embedding_str,
        }

        filter_parts: list[str] = []
        if file_id is not None:
            filter_parts.append("file_id = :fid")
            params["fid"] = file_id

        max_distance: float | None = None
        if min_similarity > 0.0:
            max_distance = 1.0 - min_similarity
            filter_parts.append(
                "(embedding <=> CAST(:embedding_vec AS vector)) <= :max_distance"
            )
            params["max_distance"] = max_distance

        where_clause = f"WHERE {' AND '.join(filter_parts)}" if filter_parts else ""

        sql = text(
            f"""
            SELECT id, file_id, section_id, chunk_index, content,
                   (embedding <=> CAST(:embedding_vec AS vector)) AS distance,
                   page_number, section_type, file_name
            FROM {TABLE_NAME}
            {where_clause}
            ORDER BY embedding <=> CAST(:embedding_vec AS vector)
            LIMIT :k
            """
        )
        with self.engine.begin() as conn:
            res = conn.execute(sql, params)
            out: list[SimilarChunk] = []
            for row in res.mappings():
                out.append(
                    SimilarChunk(
                        id=row["id"],
                        file_id=row["file_id"],
                        section_id=row["section_id"],
                        chunk_index=row["chunk_index"],
                        content=row["content"],
                        distance=float(row["distance"]),
                        page_number=row.get("page_number"),
                        section_type=row.get("section_type"),
                        file_name=row.get("file_name"),
                    )
                )
            return out
