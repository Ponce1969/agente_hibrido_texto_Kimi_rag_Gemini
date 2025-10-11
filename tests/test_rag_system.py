"""
Tests del sistema RAG (Retrieval-Augmented Generation).
"""
import pytest
import numpy as np
import asyncio
import time
from unittest.mock import Mock, AsyncMock

from src.application.services.embeddings_service import EmbeddingsServiceV2
from src.domain.ports import EmbeddingsPort
from src.domain.models.file_models import FileSection


@pytest.mark.unit
@pytest.mark.rag
class TestEmbeddingsService:
    """Tests unitarios del servicio de embeddings."""

    @pytest.mark.asyncio
    async def test_search_similar_calls_embedding_generation(self):
        mock_client = AsyncMock(spec=EmbeddingsPort)
        mock_client.generate_embedding.return_value = np.random.rand(768)
        mock_client.search_similar.return_value = []  # No results needed for this test
        service = EmbeddingsServiceV2(mock_client)

        await service.search_similar(query="test query", file_id="1")

        # Verificar que la generación de embedding fue llamada
        mock_client.generate_embedding.assert_called_once_with("test query")
        # Verificar que la búsqueda fue llamada
        mock_client.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_similar_returns_list_of_dicts(self):
        mock_client = AsyncMock(spec=EmbeddingsPort)
        # Mock de la respuesta del puerto
        mock_result = Mock()
        mock_result.text = "chunk content"
        mock_result.similarity = 0.9
        mock_result.section = Mock(id=1, chunk_index=0)
        mock_client.search_similar.return_value = [mock_result]

        service = EmbeddingsServiceV2(mock_client)
        results = await service.search_similar(query="test query", file_id="1", top_k=1)
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], dict)
        assert 'text' in results[0]
        assert 'similarity' in results[0]

    @pytest.mark.asyncio
    async def test_search_similar_with_no_results(self):
        mock_client = AsyncMock(spec=EmbeddingsPort)
        mock_client.search_similar.return_value = []
        service = EmbeddingsServiceV2(mock_client)
        results = await service.search_similar(query="query sin resultados", file_id="999")
        assert results == []

@pytest.mark.rag
class TestRAGErrorHandling:
    """Tests de manejo de errores en el sistema RAG."""

    @pytest.mark.asyncio
    async def test_handles_empty_query(self):
        mock_client = AsyncMock(spec=EmbeddingsPort)
        service = EmbeddingsServiceV2(mock_client)
        with pytest.raises(ValueError):
            await service.search_similar(query="", file_id="1")
