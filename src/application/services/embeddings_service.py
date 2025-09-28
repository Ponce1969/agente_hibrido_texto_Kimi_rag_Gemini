"""
EmbeddingsService: handles chunking and embedding generation for PDFs, storing into PostgreSQL (pgvector).

Step 2 of RAG plan: service and indexation endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from sqlmodel import Session, select
from datetime import datetime

from src.adapters.db.embeddings_repository import EmbeddingsRepository, EMBEDDING_DIM
from src.adapters.config.settings import settings
from src.adapters.db.embeddings_models import EmbeddingChunk
from src.adapters.db.database import engine as sqlite_engine
from src.adapters.db.file_models import FileUpload, FileSection, FileStatus


# Choose a 768-dim model to match repository schema
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"  # 768 dims


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    if chunk_size <= 0:
        return [text]
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(end - overlap, 0)
    return chunks


class EmbeddingsService:
    def __init__(self, repo: EmbeddingsRepository) -> None:
        self.repo = repo
        # Lazy import to avoid heavy import times when unused
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def _embed_texts(self, texts: Sequence[str]) -> List[Sequence[float]]:
        # The model returns numpy arrays; convert to python lists of floats
        vectors = self.model.encode(
            list(texts),
            normalize_embeddings=True,
            batch_size=max(1, int(getattr(settings, "embedding_batch_size", 8))),
            show_progress_bar=False,
        )
        # Ensure each vector length matches EMBEDDING_DIM
        out: List[Sequence[float]] = []
        for v in vectors:
            if len(v) != EMBEDDING_DIM:
                raise ValueError(f"Embedding dimension mismatch: got {len(v)} expected {EMBEDDING_DIM}")
            out.append([float(x) for x in v])
        return out

    def embed_query(self, query: str) -> Sequence[float]:
        vecs = self._embed_texts([query])
        return vecs[0]

    def index_file(
        self,
        file_id: int,
        section_ids: Optional[List[int]] = None,
        chunk_size: int = settings.embedding_chunk_size,
        overlap: int = settings.embedding_chunk_overlap,
    ) -> int:
        """
        Build embeddings for a PDF previously processed into sections, storing results in PostgreSQL.
        Returns number of chunks inserted.
        """
        # Read file and sections from SQLite
        with Session(sqlite_engine) as s:
            fu = s.get(FileUpload, file_id)
            if not fu:
                raise ValueError("Archivo no encontrado")
            if fu.status != FileStatus.READY:
                raise ValueError("El archivo aún no está listo para indexación")

            stmt = select(FileSection).where(FileSection.file_id == file_id).order_by(FileSection.start_page)
            all_sections = s.exec(stmt).all()

        if section_ids:
            sections = [sec for sec in all_sections if sec.id in set(section_ids)]
        else:
            sections = all_sections

        # Extract text per section using PyPDF (on-demand, similar to files endpoint)
        try:
            from pypdf import PdfReader  # type: ignore
            import io
        except Exception as e:
            raise RuntimeError(f"Soporte PDF no disponible: {e}")

        with open(fu.path, "rb") as f:
            raw = f.read()
        reader = PdfReader(io.BytesIO(raw))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception:
                raise RuntimeError("El PDF está cifrado y no pudo ser leído.")

        # Delete previous chunks for this file_id to keep index consistent
        self.repo.ensure_schema()
        self.repo.delete_file_chunks(file_id)

        total_inserted = 0
        for sec in sections:
            print(f"[Embeddings] Procesando sección id={sec.id} páginas {sec.start_page+1}-{sec.end_page+1}…")
            parts: List[str] = []
            for idx in range(sec.start_page, sec.end_page + 1):
                try:
                    text = reader.pages[idx].extract_text() or ""
                except Exception:
                    text = ""
                parts.append(text)
            section_text = "\n".join(parts).strip()
            if not section_text:
                print(f"[Embeddings] Sección id={sec.id} sin texto extraíble, se omite.")
                continue

            chunk_texts = _chunk_text(section_text, chunk_size=chunk_size, overlap=overlap)
            print(f"[Embeddings] Sección id={sec.id}: {len(chunk_texts)} chunks para embedir…")
            embeddings = self._embed_texts(chunk_texts)

            chunks: List[EmbeddingChunk] = []
            for i, (t, vec) in enumerate(zip(chunk_texts, embeddings)):
                chunks.append(
                    EmbeddingChunk(
                        file_id=file_id,
                        section_id=sec.id,
                        chunk_index=i,
                        content=t,
                        embedding=vec,
                    )
                )
            inserted = self.repo.insert_chunks(chunks)
            total_inserted += inserted
            print(f"[Embeddings] Sección id={sec.id}: insertados {inserted} chunks (acumulado={total_inserted}).")

        return total_inserted

    def search(self, query: str, file_id: Optional[int] = None, top_k: int = 5):
        qvec = self.embed_query(query)
        return self.repo.search_top_k(qvec, file_id=file_id, top_k=top_k)
