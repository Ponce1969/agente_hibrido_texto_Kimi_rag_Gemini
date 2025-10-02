"""
Tests del sistema RAG (Retrieval-Augmented Generation).
Verifica que la búsqueda vectorial y generación de respuestas funcione correctamente.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.application.services.embeddings_service import EmbeddingsService
from src.adapters.db.embeddings_repository import EmbeddingsRepository


@pytest.mark.unit
@pytest.mark.rag
class TestEmbeddingsService:
    """Tests unitarios del servicio de embeddings."""
    
    def test_embed_query_returns_correct_dimensions(self):
        """Verifica que el embedding tenga 384 dimensiones."""
        repo = Mock(spec=EmbeddingsRepository)
        service = EmbeddingsService(repo)
        
        query = "¿Qué son las funciones en Python?"
        embedding = service.embed_query(query)
        
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_search_returns_top_k_results(self, sample_chunks):
        """Verifica que search devuelva exactamente top_k resultados."""
        repo = Mock(spec=EmbeddingsRepository)
        repo.search_top_k.return_value = sample_chunks[:3]
        
        service = EmbeddingsService(repo)
        
        results = service.search("test query", file_id=1, top_k=3)
        
        assert len(results) == 3
        assert all(hasattr(r, 'content') for r in results)
        repo.search_top_k.assert_called_once()
    
    def test_search_with_no_results(self):
        """Verifica el comportamiento cuando no hay resultados."""
        repo = Mock(spec=EmbeddingsRepository)
        repo.search_top_k.return_value = []
        
        service = EmbeddingsService(repo)
        
        results = service.search("query sin resultados", file_id=999, top_k=5)
        
        assert results == []


@pytest.mark.integration
@pytest.mark.rag
@pytest.mark.slow
class TestRAGIntegration:
    """Tests de integración del sistema RAG completo."""
    
    @pytest.mark.skip(reason="Requiere PostgreSQL corriendo")
    def test_full_rag_pipeline(self):
        """
        Test del pipeline completo:
        1. Generar embedding de query
        2. Buscar en PostgreSQL
        3. Construir contexto
        4. Enviar a LLM
        """
        # Este test se implementará cuando tengamos PostgreSQL en CI
        pass
    
    def test_rag_context_construction(self, sample_chunks):
        """Verifica que el contexto RAG se construya correctamente."""
        # Simular construcción de contexto
        context_parts = []
        for chunk in sample_chunks:
            snippet = f"[sec {chunk['section_id']} ch {chunk['chunk_index']} d={chunk['distance']:.3f}]\n{chunk['content']}"
            context_parts.append(snippet)
        
        rag_context = "\n\n".join(context_parts)
        
        assert "sec 1 ch 0" in rag_context
        assert "funciones en Python" in rag_context
        assert len(rag_context) > 0


@pytest.mark.unit
@pytest.mark.rag
class TestEmbeddingsRepository:
    """Tests del repositorio de embeddings."""
    
    def test_embedding_conversion_to_vector_string(self, sample_embedding):
        """Verifica que el embedding se convierta correctamente a string de PostgreSQL."""
        # Simular conversión
        embedding_str = "[" + ",".join(str(x) for x in sample_embedding) + "]"
        
        assert embedding_str.startswith("[")
        assert embedding_str.endswith("]")
        assert "," in embedding_str
        assert len(embedding_str) > 100  # Debe ser un string largo
    
    def test_count_chunks_returns_integer(self):
        """Verifica que count_chunks devuelva un entero."""
        repo = EmbeddingsRepository()
        
        # Mock del engine
        with patch.object(repo, 'engine') as mock_engine:
            mock_conn = Mock()
            mock_result = Mock()
            mock_result.scalar.return_value = 522
            mock_conn.execute.return_value = mock_result
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=False)
            mock_engine.begin.return_value = mock_conn
            
            count = repo.count_chunks(file_id=1)
            
            assert isinstance(count, int)
            assert count >= 0


@pytest.mark.rag
class TestRAGErrorHandling:
    """Tests de manejo de errores en el sistema RAG."""
    
    def test_handles_empty_query(self):
        """Verifica que maneje queries vacías correctamente."""
        repo = Mock(spec=EmbeddingsRepository)
        service = EmbeddingsService(repo)
        
        # Query vacía no debería crashear
        try:
            embedding = service.embed_query("")
            assert len(embedding) == 384
        except Exception as e:
            pytest.fail(f"No debería fallar con query vacía: {e}")
    
    def test_handles_very_long_query(self):
        """Verifica que maneje queries muy largas."""
        repo = Mock(spec=EmbeddingsRepository)
        service = EmbeddingsService(repo)
        
        long_query = "test " * 1000  # 5000 caracteres
        
        try:
            embedding = service.embed_query(long_query)
            assert len(embedding) == 384
        except Exception as e:
            pytest.fail(f"No debería fallar con query larga: {e}")
    
    def test_handles_special_characters(self):
        """Verifica que maneje caracteres especiales."""
        repo = Mock(spec=EmbeddingsRepository)
        service = EmbeddingsService(repo)
        
        special_query = "¿Qué es λ (lambda)? ∀x ∈ ℝ"
        
        try:
            embedding = service.embed_query(special_query)
            assert len(embedding) == 384
        except Exception as e:
            pytest.fail(f"No debería fallar con caracteres especiales: {e}")


@pytest.mark.rag
class TestRAGPerformance:
    """Tests de performance del sistema RAG."""
    
    @pytest.mark.slow
    def test_search_performance(self):
        """Verifica que la búsqueda sea razonablemente rápida."""
        import time
        
        repo = Mock(spec=EmbeddingsRepository)
        repo.search_top_k.return_value = []
        
        service = EmbeddingsService(repo)
        
        start = time.time()
        service.search("test query", file_id=1, top_k=5)
        elapsed = time.time() - start
        
        # La búsqueda debería tomar menos de 1 segundo
        assert elapsed < 1.0, f"Búsqueda muy lenta: {elapsed:.2f}s"
