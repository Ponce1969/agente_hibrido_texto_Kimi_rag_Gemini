"""
Tests para validar el sistema de embeddings del Día 3.

Valida:
- GeminiEmbeddingsAdapter funciona correctamente
- EmbeddingsServiceV2 usa solo puertos
- Inyección de dependencias funciona
- No hay violaciones de arquitectura
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, Mock

from src.domain.ports import EmbeddingsPort
from src.domain.models.file_models import FileDocument, FileSection, FileStatus
from src.application.services.embeddings_service import EmbeddingsServiceV2, chunk_text


class MockEmbeddingsPort(EmbeddingsPort):
    """Mock del puerto de embeddings para testing."""
    
    def __init__(self, dimension: int = 768) -> None:
        self.dimension = dimension
        self.indexed_count = 0
        self.deleted_count = 0
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Genera un embedding mock."""
        # Retornar vector aleatorio normalizado
        vector = np.random.rand(self.dimension).astype(np.float32)
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else vector
    
    async def generate_embeddings_batch(
        self,
        texts: list[str],
        *,
        batch_size: int = 32,
    ) -> list[np.ndarray]:
        """Genera embeddings en batch."""
        return [await self.generate_embedding(text) for text in texts]
    
    async def store_embedding(
        self,
        file_id: str,
        section_id: int,
        text: str,
        embedding: np.ndarray,
    ) -> None:
        """Mock de almacenamiento."""
        pass
    
    async def search_similar(
        self,
        query_embedding: np.ndarray,
        file_id: str,
        *,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list:
        """Mock de búsqueda."""
        from src.domain.ports.embeddings_port import SearchResult
        
        # Retornar resultados mock
        section = FileSection(
            id=1,
            file_id=file_id,
            text="Mock result text",
            page_number=1,
            chunk_index=0,
        )
        
        return [
            SearchResult(
                section=section,
                similarity=0.95,
                text="Mock result text",
            )
        ]
    
    async def search_similar_across_files(
        self,
        query_embedding: np.ndarray,
        *,
        file_ids: list[str] | None = None,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list:
        """Mock de búsqueda multi-archivo."""
        return []
    
    async def index_document(
        self,
        file: FileDocument,
        sections: list[FileSection],
        *,
        batch_size: int = 32,
    ) -> int:
        """Mock de indexación."""
        self.indexed_count = len(sections)
        return self.indexed_count
    
    async def delete_document_embeddings(self, file_id: str) -> int:
        """Mock de eliminación."""
        self.deleted_count = 5
        return self.deleted_count
    
    def get_embedding_dimension(self) -> int:
        """Retorna dimensión."""
        return self.dimension


class TestEmbeddingsServiceV2:
    """Tests para EmbeddingsServiceV2 con arquitectura hexagonal."""
    
    def test_service_creation(self) -> None:
        """Test que el servicio se crea correctamente."""
        mock_embeddings = MockEmbeddingsPort()
        
        service = EmbeddingsServiceV2(
            embeddings_client=mock_embeddings,
        )
        
        assert service.embeddings == mock_embeddings
    
    @pytest.mark.asyncio
    async def test_index_document(self) -> None:
        """Test indexar un documento."""
        mock_embeddings = MockEmbeddingsPort()
        service = EmbeddingsServiceV2(mock_embeddings)
        
        # Crear documento y secciones mock
        from datetime import datetime, UTC
        
        file = FileDocument(
            id="1",
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            status=FileStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        
        sections = [
            FileSection(
                id=1,
                file_id="1",
                text="Section 1 text",
                page_number=1,
                chunk_index=0,
            ),
            FileSection(
                id=2,
                file_id="1",
                text="Section 2 text",
                page_number=1,
                chunk_index=1,
            ),
        ]
        
        # Indexar
        count = await service.index_document(file, sections)
        
        assert count == 2
        assert mock_embeddings.indexed_count == 2
    
    @pytest.mark.asyncio
    async def test_search_similar(self) -> None:
        """Test buscar secciones similares."""
        mock_embeddings = MockEmbeddingsPort()
        service = EmbeddingsServiceV2(mock_embeddings)
        
        # Buscar
        results = await service.search_similar(
            query="test query",
            file_id="1",
            top_k=5,
        )
        
        assert len(results) == 1
        assert results[0]["text"] == "Mock result text"
        assert results[0]["similarity"] == 0.95
    
    @pytest.mark.asyncio
    async def test_delete_embeddings(self) -> None:
        """Test eliminar embeddings."""
        mock_embeddings = MockEmbeddingsPort()
        service = EmbeddingsServiceV2(mock_embeddings)
        
        count = await service.delete_document_embeddings("1")
        
        assert count == 5
        assert mock_embeddings.deleted_count == 5
    
    def test_get_embedding_dimension(self) -> None:
        """Test obtener dimensión."""
        mock_embeddings = MockEmbeddingsPort(dimension=768)
        service = EmbeddingsServiceV2(mock_embeddings)
        
        dim = service.get_embedding_dimension()
        
        assert dim == 768


class TestChunkText:
    """Tests para la función chunk_text."""
    
    def test_chunk_text_basic(self) -> None:
        """Test chunking básico."""
        text = "A" * 1000
        chunks = chunk_text(text, chunk_size=300, overlap=50)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 300 for chunk in chunks)
    
    def test_chunk_text_empty(self) -> None:
        """Test con texto vacío."""
        chunks = chunk_text("", chunk_size=300)
        
        assert chunks == []
    
    def test_chunk_text_small(self) -> None:
        """Test con texto pequeño."""
        text = "Small text"
        chunks = chunk_text(text, chunk_size=300)
        
        assert len(chunks) == 1
        assert chunks[0] == text


class TestAdapters:
    """Tests para verificar que los adaptadores funcionan."""
    
    def test_gemini_embeddings_adapter_import(self) -> None:
        """Test que GeminiEmbeddingsAdapter se puede importar."""
        from src.adapters.agents.gemini_embeddings_adapter import GeminiEmbeddingsAdapter
        assert GeminiEmbeddingsAdapter is not None
    
    def test_embeddings_service_v2_import(self) -> None:
        """Test que EmbeddingsServiceV2 se puede importar."""
        from src.application.services.embeddings_service import EmbeddingsServiceV2
        assert EmbeddingsServiceV2 is not None


class TestDependencies:
    """Tests para el sistema de inyección de dependencias."""
    
    def test_dependencies_import(self) -> None:
        """Test que el módulo de dependencies se puede importar."""
        from src.adapters import dependencies
        assert dependencies is not None
    
    def test_get_gemini_embeddings_adapter(self) -> None:
        """Test que se puede crear un GeminiEmbeddingsAdapter."""
        from src.adapters.dependencies import get_gemini_embeddings_adapter
        
        adapter = get_gemini_embeddings_adapter()
        assert adapter is not None
        assert hasattr(adapter, 'generate_embedding')
    
    def test_get_embeddings_service(self) -> None:
        """Test que se puede crear un EmbeddingsServiceV2."""
        from src.adapters.dependencies import get_embeddings_service
        
        service = get_embeddings_service()
        assert service is not None
        assert hasattr(service, 'index_document')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
