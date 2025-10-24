"""
Servicio de embeddings refactorizado con arquitectura hexagonal.

Este servicio usa SOLO el puerto EmbeddingsPort, sin dependencias
de implementaciones concretas.

Tipado estricto para mypy --strict con Python 3.12+
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.ports import EmbeddingsPort
    from src.domain.models.file_models import FileDocument, FileSection


class EmbeddingsServiceV2:
    """
    Servicio de aplicación para embeddings siguiendo arquitectura hexagonal.
    
    Este servicio orquesta la indexación de documentos sin conocer
    detalles de implementación (Gemini API, sentence-transformers, etc.).
    
    Principios:
    - Depende SOLO del puerto EmbeddingsPort
    - No importa de adapters
    - Lógica de negocio pura
    - Fácil de testear con mocks
    """
    
    def __init__(self, embeddings_client: EmbeddingsPort) -> None:
        """
        Inicializa el servicio de embeddings.
        
        Args:
            embeddings_client: Cliente de embeddings (ej: GeminiEmbeddingsAdapter)
        """
        self.embeddings = embeddings_client
    
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
            
        Raises:
            ValueError: Si no hay secciones para indexar
        """
        # Guard clause: validar entrada
        if not sections:
            raise ValueError("No hay secciones para indexar")
        
        # Delegar al cliente de embeddings
        indexed_count = await self.embeddings.index_document(
            file=file,
            sections=sections,
            batch_size=batch_size,
        )
        
        return indexed_count
    
    async def search_similar(
        self,
        query: str,
        file_id: str | None,
        *,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Busca secciones similares a una query.
        """
        if not query or not query.strip():
            raise ValueError("La query no puede estar vacía")

        query_embedding = await self.embeddings.generate_embedding(query)

        results = await self.embeddings.search_similar(
            query_embedding=query_embedding,
            file_id=file_id,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        return [
            {
                "text": result.text,
                "similarity": result.similarity,
                "section_id": result.section.id,
                "chunk_index": result.section.chunk_index,
            }
            for result in results
        ]
    
    async def delete_document_embeddings(self, file_id: str) -> int:
        """
        Elimina todos los embeddings de un documento.
        
        Args:
            file_id: ID del archivo
            
        Returns:
            Número de embeddings eliminados
        """
        return await self.embeddings.delete_document_embeddings(file_id)
    
    def get_embedding_dimension(self) -> int:
        """
        Obtiene la dimensión de los embeddings.
        
        Returns:
            Dimensión del vector (ej: 768 para Gemini)
        """
        return self.embeddings.get_embedding_dimension()


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    """
    Divide un texto en chunks con overlap.
    
    Args:
        text: Texto a dividir
        chunk_size: Tamaño máximo de cada chunk
        overlap: Solapamiento entre chunks
        
    Returns:
        Lista de chunks de texto
    """
    # Guard clause: validar entrada
    if not text.strip():
        return []
    
    if chunk_size <= 0:
        return [text]
    
    chunks: list[str] = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(text_length, start + chunk_size)
        chunks.append(text[start:end])
        
        # Si llegamos al final, terminar
        if end == text_length:
            break
        
        # Mover start considerando el overlap
        start = max(end - overlap, 0)
    
    return chunks
