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

from typing import Iterable, List, Optional, Sequence, Tuple
from dataclasses import asdict
from datetime import datetime

from sqlalchemy import text

from src.adapters.db.pg_engine import get_pg_engine
from src.adapters.db.embeddings_models import EmbeddingChunk, SimilarChunk


EMBEDDING_DIM = 384  # Updated for all-MiniLM-L6-v2 (optimized for low resources)
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
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_file_id ON {TABLE_NAME}(file_id);
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_section_id ON {TABLE_NAME}(section_id);
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_embedding ON {TABLE_NAME} USING ivfflat (embedding vector_cosine_ops);
        """
        with self.engine.begin() as conn:
            # Ensure extension exists (noop if already enabled)
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(text(ddl))

    def delete_file_chunks(self, file_id: int) -> int:
        """Delete all chunks for a given file_id. Returns number of deleted rows."""
        with self.engine.begin() as conn:
            res = conn.execute(text(f"DELETE FROM {TABLE_NAME} WHERE file_id = :fid"), {"fid": file_id})
            return res.rowcount or 0

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
            rows.append({
                "file_id": ch.file_id,
                "section_id": ch.section_id,
                "chunk_index": ch.chunk_index,
                "content": ch.content,
                "embedding": list(ch.embedding),  # psycopg2 + pgvector accepts python lists
            })
        if not rows:
            return 0
        sql = text(
            f"""
            INSERT INTO {TABLE_NAME} (file_id, section_id, chunk_index, content, embedding)
            VALUES (:file_id, :section_id, :chunk_index, :content, :embedding)
            """
        )
        with self.engine.begin() as conn:
            conn.execute(sql, rows)
        return len(rows)

    def search_top_k(
        self,
        query_embedding: Sequence[float],
        file_id: Optional[int] = None,
        top_k: int = 5,
    ) -> List[SimilarChunk]:
        """Return top-k most similar chunks using cosine distance (<->).
        If file_id is provided, the search is filtered to that file.
        """
        params = {"q": list(query_embedding), "k": top_k}
        filter_sql = "WHERE file_id = :fid" if file_id is not None else ""
        if file_id is not None:
            params["fid"] = file_id

        sql = text(
            f"""
            SELECT id, file_id, section_id, chunk_index, content,
                   (embedding <-> :q) AS distance
            FROM {TABLE_NAME}
            {filter_sql}
            ORDER BY embedding <-> :q
            LIMIT :k
            """
        )
        with self.engine.begin() as conn:
            res = conn.execute(sql, params)
            out: List[SimilarChunk] = []
            for row in res:
                out.append(
                    SimilarChunk(
                        id=row["id"],
                        file_id=row["file_id"],
                        section_id=row["section_id"],
                        chunk_index=row["chunk_index"],
                        content=row["content"],
                        distance=float(row["distance"]),
                    )
                )
            return out
