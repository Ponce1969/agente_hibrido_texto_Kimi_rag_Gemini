"""
Puerto (Interface) para servicios de embeddings.

Este puerto define el contrato para generación y búsqueda de embeddings vectoriales.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from ..models.file_models import FileDocument, FileSection

# Type aliases para mayor claridad
type EmbeddingVector = npt.NDArray[np.float32]
type SimilarityScore = float


class SearchResult:
    """Resultado de búsqueda de similitud."""

    def __init__(
        self,
        section: FileSection,
        similarity: SimilarityScore,
        text: str,
    ) -> None:
        self.section = section
        self.similarity = similarity
        self.text = text

    def __repr__(self) -> str:
        return f"SearchResult(similarity={self.similarity:.4f}, text={self.text[:50]}...)"


class EmbeddingsPort(ABC):
    """
    Puerto para servicio de embeddings vectoriales.

    Esta interfaz abstrae la generación y búsqueda de embeddings,
    permitiendo cambiar entre diferentes modelos y backends
    (sentence-transformers, OpenAI, Cohere, etc.).

    Ejemplos de implementaciones:
        - SentenceTransformerEmbeddings: Usa all-MiniLM-L6-v2 local
        - OpenAIEmbeddings: Usa API de OpenAI embeddings
        - CohereEmbeddings: Usa API de Cohere
    """

    @abstractmethod
    async def generate_embedding(self, text: str) -> EmbeddingVector:
        """
        Genera un embedding vectorial para un texto.

        Args:
            text: Texto a convertir en embedding

        Returns:
            Vector de embedding normalizado

        Raises:
            EmbeddingError: Si hay error en la generación
        """
        ...

    @abstractmethod
    async def generate_embeddings_batch(
        self,
        texts: list[str],
        *,
        batch_size: int = 32,
    ) -> list[EmbeddingVector]:
        """
        Genera embeddings para múltiples textos en batch.

        Args:
            texts: Lista de textos a procesar
            batch_size: Tamaño del batch para procesamiento

        Returns:
            Lista de vectores de embedding

        Raises:
            EmbeddingError: Si hay error en la generación
        """
        ...

    @abstractmethod
    async def store_embedding(
        self,
        file_id: str,
        section_id: int,
        text: str,
        embedding: EmbeddingVector,
    ) -> None:
        """
        Almacena un embedding en el repositorio vectorial.

        Args:
            file_id: ID del archivo
            section_id: ID de la sección
            text: Texto original
            embedding: Vector de embedding

        Raises:
            RepositoryError: Si hay error en el almacenamiento
        """
        ...

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: EmbeddingVector,
        file_id: str,
        *,
        top_k: int = 5,
        min_similarity: SimilarityScore = 0.0,
    ) -> list[SearchResult]:
        """
        Busca secciones similares usando similitud coseno.

        Args:
            query_embedding: Vector de embedding de la query
            file_id: ID del archivo donde buscar
            top_k: Número máximo de resultados
            min_similarity: Similitud mínima requerida (0.0 a 1.0)

        Returns:
            Lista de resultados ordenados por similitud descendente
        """
        ...

    @abstractmethod
    async def search_similar_across_files(
        self,
        query_embedding: EmbeddingVector,
        *,
        file_ids: list[str] | None = None,
        top_k: int = 5,
        min_similarity: SimilarityScore = 0.0,
    ) -> list[SearchResult]:
        """
        Busca secciones similares en múltiples archivos.

        Args:
            query_embedding: Vector de embedding de la query
            file_ids: IDs de archivos donde buscar (None = todos)
            top_k: Número máximo de resultados
            min_similarity: Similitud mínima requerida

        Returns:
            Lista de resultados ordenados por similitud descendente
        """
        ...

    @abstractmethod
    async def index_document(
        self,
        file: FileDocument,
        sections: list[FileSection],
        *,
        batch_size: int = 32,
    ) -> int:
        """
        Indexa un documento completo generando embeddings para todas sus secciones.

        Args:
            file: Documento a indexar
            sections: Secciones del documento
            batch_size: Tamaño del batch para procesamiento

        Returns:
            Número de secciones indexadas

        Raises:
            EmbeddingError: Si hay error en la indexación
        """
        ...

    @abstractmethod
    async def delete_document_embeddings(self, file_id: str) -> int:
        """
        Elimina todos los embeddings de un documento.

        Args:
            file_id: ID del archivo

        Returns:
            Número de embeddings eliminados
        """
        ...

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Obtiene la dimensión de los embeddings.

        Returns:
            Dimensión del vector (ej: 384 para all-MiniLM-L6-v2)
        """
        ...
