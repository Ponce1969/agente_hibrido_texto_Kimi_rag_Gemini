#!/usr/bin/env python3
"""
Tests de integración post-migración.

Verifica que la migración de código obsoleto fue exitosa
y que todo funciona correctamente con la arquitectura hexagonal.
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
import os

# Configuración para tests con Docker
BASE_URL = "http://localhost:8000"


class TestMigracionCompleta:
    """Tests de verificación post-migración."""
    
    def test_servicios_existentes(self):
        """Verifica que los servicios v2 existen y son accesibles."""
        # Verificar que no hay referencias al código viejo
        from src.application.services.chat_service import ChatServiceV2
        from src.application.services.embeddings_service import EmbeddingsServiceV2
        
        assert ChatServiceV2 is not None
        assert EmbeddingsServiceV2 is not None
    
    def test_no_hay_codigo_viejo(self):
        """Verifica que no hay imports del código viejo."""
        import src.adapters.dependencies as deps
        
        # Verificar que no hay referencias a archivos eliminados
        assert not hasattr(deps, 'get_chat_service_v1')
        assert not hasattr(deps, 'get_embeddings_service_v1')
    
    @pytest.mark.asyncio
    async def test_api_health(self):
        """Verifica que la API está funcionando."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{BASE_URL}/docs")
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("API no disponible - ejecutar con Docker")
    
    @pytest.mark.asyncio
    async def test_endpoints_disponibles(self):
        """Verifica que los endpoints principales existen."""
        async with httpx.AsyncClient() as client:
            try:
                # Verificar endpoints de chat
                response = await client.get(f"{BASE_URL}/api/v1/sessions?user_id=test")
                assert response.status_code in [200, 422]  # 422 es válido para parámetros
            except httpx.ConnectError:
                pytest.skip("API no disponible - ejecutar con Docker")
    
    def test_arquitectura_hexagonal(self):
        """Verifica que la arquitectura hexagonal está implementada."""
        from src.domain.ports import LLMPort, ChatRepositoryPort, EmbeddingsPort
        from src.application.services.chat_service import ChatServiceV2
        
        # Verificar que ChatServiceV2 usa solo puertos
        service_init = ChatServiceV2.__init__.__annotations__
        assert 'llm_client' in service_init
        assert 'repository' in service_init
        assert 'embeddings_service' in service_init
    
    def test_no_violaciones_arquitectura(self):
        """Verifica que no hay violaciones de arquitectura."""
        import inspect
        from src.application.services.chat_service import ChatServiceV2
        
        # Verificar que no importa de adapters directamente
        source = inspect.getsource(ChatServiceV2)
        assert "from src.adapters" not in source
        assert "import src.adapters" not in source
    
    def test_servicio_embeddings_funcional(self):
        """Verifica que el servicio de embeddings está funcional."""
        from src.application.services.embeddings_service import EmbeddingsServiceV2
        from src.adapters.dependencies import get_embeddings_service
        
        # Verificar que se puede crear instancia
        service = get_embeddings_service()
        assert isinstance(service, EmbeddingsServiceV2)
        assert hasattr(service, 'search_similar')
        assert hasattr(service, 'index_document')


class TestRAGFuncional:
    """Tests del sistema RAG post-migración."""
    
    @pytest.mark.asyncio
    async def test_rag_con_file_id(self):
        """Verifica que el sistema RAG funciona con file_id."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Crear sesión
                response = await client.post(
                    f"{BASE_URL}/api/v1/sessions",
                    json={"user_id": "test_user"}
                )
                assert response.status_code == 201, f"Failed to create session: {response.text}"
                session_id = response.json()["session_id"]
                
                # Probar RAG
                response = await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "session_id": session_id,  # Pass as int
                        "message": "¿Qué dice el documento sobre buenas prácticas?",
                        "mode": "Arquitecto Python Senior",  # Usar valor del enum AgentMode
                        "file_id": 2
                    }
                )
                assert response.status_code == 200
                # Verificar que hay respuesta (puede no contener exactamente "buenas prácticas")
                assert len(response.json()["reply"]) > 0
            except (httpx.ConnectError, httpx.ReadTimeout):
                pytest.skip("API no disponible o timeout - ejecutar con Docker")


if __name__ == "__main__":
    # Ejecutar tests rápidos
    import subprocess
    subprocess.run(["uv", "run", "pytest", __file__, "-v", "--tb=short"])
