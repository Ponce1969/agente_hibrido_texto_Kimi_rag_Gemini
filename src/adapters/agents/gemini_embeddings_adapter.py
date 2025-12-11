"""
Adaptador de Gemini Embeddings que implementa EmbeddingsPort.

Este adaptador usa la API de Google Gemini para generar embeddings vectoriales,
eliminando la necesidad de modelos locales y liberando recursos del sistema.

Modelo: text-embedding-004 (768 dimensiones)
Ventajas: Sin carga en CPU/RAM, mayor calidad, procesamiento en cloud
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import numpy as np
import numpy.typing as npt

from src.adapters.config.settings import settings
from src.domain.ports.embeddings_port import EmbeddingsPort, SearchResult

if TYPE_CHECKING:
    from src.domain.models.file_models import FileDocument, FileSection

# Type alias
type EmbeddingVector = npt.NDArray[np.float32]


class GeminiEmbeddingsAdapter(EmbeddingsPort):
    """
    Adaptador de Gemini Embeddings que implementa EmbeddingsPort.

    Características:
    - Usa API de Google Gemini (text-embedding-004)
    - 768 dimensiones (vs 384 del modelo local)
    - Sin carga en CPU/RAM local
    - Procesamiento paralelo en cloud
    - Gratis hasta 1500 requests/día

    Optimizado para hardware de bajos recursos (AMD APU A10).
    """

    EMBEDDING_MODEL = "text-embedding-004"
    EMBEDDING_DIMENSION = 768

    def __init__(self, client: httpx.AsyncClient) -> None:
        """
        Inicializa el adaptador de Gemini Embeddings.

        Args:
            client: Cliente HTTP asíncrono para requests
        """
        self.client = client
        self.api_key = settings.gemini_api_key
        self._validate_api_key()

    def _validate_api_key(self) -> None:
        """Valida que la API key esté configurada."""
        if not self.api_key:
            raise ValueError(
                "Gemini API key no configurada. "
                "Configura GEMINI_API_KEY en el archivo .env"
            )

    async def generate_embedding(self, text: str) -> EmbeddingVector:
        """
        Genera un embedding vectorial usando Gemini API.

        Args:
            text: Texto a convertir en embedding

        Returns:
            Vector de embedding normalizado (768 dims)

        Raises:
            ValueError: Si el texto está vacío
            RuntimeError: Si hay error en la API
        """
        # Guard clause: validar texto
        if not text.strip():
            raise ValueError("El texto no puede estar vacío")

        # Construir URL de la API
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.EMBEDDING_MODEL}:embedContent?key={self.api_key}"
        )

        # Payload para la API
        payload = {
            "model": f"models/{self.EMBEDDING_MODEL}",
            "content": {
                "parts": [{"text": text}]
            }
        }

        # Llamar a la API
        response = await self.client.post(
            url,
            json=payload,
            timeout=httpx.Timeout(10.0, connect=10.0, read=30.0, write=10.0, pool=10.0),
        )
        response.raise_for_status()

        # Extraer embedding de la respuesta
        data = response.json()
        embedding_values = data.get("embedding", {}).get("values", [])

        if not embedding_values:
            raise RuntimeError("Gemini no retornó embedding válido")

        # Convertir a numpy array y normalizar
        embedding = np.array(embedding_values, dtype=np.float32)

        # Normalizar el vector (para similitud coseno)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    async def generate_embeddings_batch(
        self,
        texts: list[str],
        *,
        batch_size: int = 32,
    ) -> list[EmbeddingVector]:
        """
        Genera embeddings para múltiples textos en batch.

        Nota: Gemini API procesa uno a uno, pero lo hacemos
        concurrentemente para aprovechar async.

        Args:
            texts: Lista de textos a procesar
            batch_size: Tamaño del batch (usado para limitar concurrencia)

        Returns:
            Lista de vectores de embedding
        """
        # Guard clause: validar entrada
        if not texts:
            return []

        embeddings: list[EmbeddingVector] = []

        # Procesar en batches para no saturar la API
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Generar embeddings concurrentemente dentro del batch
            import asyncio
            batch_embeddings = await asyncio.gather(
                *[self.generate_embedding(text) for text in batch]
            )
            embeddings.extend(batch_embeddings)

        return embeddings

    async def store_embedding(
        self,
        file_id: str,
        section_id: int,
        text: str,
        embedding: EmbeddingVector,
        *,
        page_number: int | None = None,
        section_type: str | None = None,
        file_name: str | None = None,
        chunk_index: int = 0,
    ) -> None:
        """
        Almacena un embedding en PostgreSQL con pgvector.

        Args:
            file_id: ID del archivo
            section_id: ID de la sección
            text: Texto original
            embedding: Vector de embedding
            page_number: Número de página del chunk (opcional)
            section_type: Tipo de sección (opcional)
            file_name: Nombre del archivo (opcional)
            chunk_index: Índice del chunk (default: 0)
        """
        # Importar modelos y repositorio
        from src.adapters.db.embeddings_models import EmbeddingChunk
        from src.adapters.db.embeddings_repository import EmbeddingsRepository

        repo = EmbeddingsRepository()

        # Convertir numpy array a lista para PostgreSQL
        embedding_list = embedding.tolist()

        # 🛡️ SANITIZAR: Eliminar caracteres NUL (0x00) que PostgreSQL no acepta
        sanitized_text = text.replace('\x00', '')

        # Crear chunk con metadatos y guardar
        chunk = EmbeddingChunk(
            file_id=int(file_id),
            section_id=section_id,
            chunk_index=chunk_index,
            content=sanitized_text,
            embedding=embedding_list,
            page_number=page_number,
            section_type=section_type,
            file_name=file_name,
        )

        repo.insert_chunks([chunk])

    async def search_similar(
        self,
        query_embedding: EmbeddingVector,
        file_id: str,
        *,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SearchResult]:
        """
        Busca secciones similares usando similitud coseno.

        Args:
            query_embedding: Vector de embedding de la query
            file_id: ID del archivo donde buscar
            top_k: Número máximo de resultados
            min_similarity: Similitud mínima requerida

        Returns:
            Lista de resultados ordenados por similitud
        """
        from src.adapters.db.embeddings_repository import EmbeddingsRepository

        repo = EmbeddingsRepository()

        # Convertir a lista para PostgreSQL
        query_list = query_embedding.tolist()

        # Buscar en base de datos
        results = repo.search_top_k(
            query_embedding=query_list,
            file_id=int(file_id),
            top_k=top_k,
        )

        # Convertir a SearchResult
        search_results: list[SearchResult] = []
        for result in results:
            # Crear FileSection mock (mejorar en futuro)
            from src.domain.models.file_models import FileSection

            # Convertir distance a similarity (1 - distance)
            similarity = 1.0 - result.distance

            section = FileSection(
                id=result.section_id or 0,
                file_id=file_id,
                text=result.content,
                page_number=None,
                chunk_index=result.chunk_index,
            )

            search_results.append(
                SearchResult(
                    section=section,
                    similarity=similarity,
                    text=result.content,
                )
            )

        return search_results

    async def search_similar_across_files(
        self,
        query_embedding: EmbeddingVector,
        *,
        file_ids: list[str] | None = None,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SearchResult]:
        """
        Busca secciones similares en múltiples archivos.

        Args:
            query_embedding: Vector de embedding de la query
            file_ids: IDs de archivos donde buscar (None = todos)
            top_k: Número máximo de resultados
            min_similarity: Similitud mínima requerida

        Returns:
            Lista de resultados ordenados por similitud
        """
        # Si no hay file_ids específicos, buscar en todos
        if not file_ids:
            # Implementar búsqueda global (futuro)
            raise NotImplementedError("Búsqueda global no implementada aún")

        # Buscar en cada archivo y combinar resultados
        all_results: list[SearchResult] = []

        for file_id in file_ids:
            results = await self.search_similar(
                query_embedding=query_embedding,
                file_id=file_id,
                top_k=top_k,
                min_similarity=min_similarity,
            )
            all_results.extend(results)

        # Ordenar por similitud y limitar a top_k
        all_results.sort(key=lambda r: r.similarity, reverse=True)
        return all_results[:top_k]

    async def index_document(
        self,
        file: FileDocument,
        sections: list[FileSection],
        *,
        batch_size: int = 32,
    ) -> int:
        """
        Indexa un documento completo generando embeddings.

        Args:
            file: Documento a indexar
            sections: Secciones del documento
            batch_size: Tamaño del batch para procesamiento

        Returns:
            Número de secciones indexadas
        """
        # Guard clause: validar entrada
        if not sections:
            return 0

        # Extraer textos de las secciones
        texts = [section.text for section in sections]

        # Generar embeddings en batch
        embeddings = await self.generate_embeddings_batch(
            texts,
            batch_size=batch_size,
        )

        # Guardar cada embedding con metadatos
        for idx, (section, embedding) in enumerate(zip(sections, embeddings, strict=False)):
            await self.store_embedding(
                file_id=file.id,
                section_id=section.id,
                text=section.text,
                embedding=embedding,
                page_number=section.page_number,
                section_type="chapter" if section.page_number is not None else None,
                file_name=file.filename,
                chunk_index=idx,
            )

        return len(sections)

    async def delete_document_embeddings(self, file_id: str) -> int:
        """
        Elimina todos los embeddings de un documento.

        Args:
            file_id: ID del archivo

        Returns:
            Número de embeddings eliminados
        """
        from src.adapters.db.embeddings_repository import EmbeddingsRepository

        repo = EmbeddingsRepository()

        return repo.delete_file_chunks(int(file_id))

    def get_embedding_dimension(self) -> int:
        """
        Obtiene la dimensión de los embeddings de Gemini.

        Returns:
            768 (dimensión de text-embedding-004)
        """
        return self.EMBEDDING_DIMENSION
