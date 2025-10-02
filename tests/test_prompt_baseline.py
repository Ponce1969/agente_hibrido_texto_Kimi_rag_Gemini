"""
Tests de baseline para prompts actuales.
Estos tests capturan el comportamiento actual ANTES del refactor.
Sirven para comparar que el refactor no degrada la calidad.
"""
import pytest
from unittest.mock import Mock, AsyncMock
import json
from pathlib import Path


@pytest.mark.unit
@pytest.mark.baseline
class TestPromptBaseline:
    """
    Tests que capturan el estado actual de los prompts.
    IMPORTANTE: Estos tests deben pasar ANTES y DESPUÉS del refactor.
    """
    
    def test_current_prompt_structure(self):
        """Captura la estructura actual de los prompts."""
        from src.adapters.agents.prompts import get_system_prompt
        
        modes = [
            "Arquitecto Python Senior",
            "Ingeniero de Código",
            "Auditor de Seguridad",
            "Especialista en Bases de Datos",
            "Ingeniero de Refactoring"
        ]
        
        baseline = {}
        for mode in modes:
            prompt = get_system_prompt(mode)
            baseline[mode] = {
                "length": len(prompt),
                "estimated_tokens": len(prompt) // 4,
                "has_tools": "tool" in prompt.lower() or "herramienta" in prompt.lower(),
                "has_examples": "ejemplo" in prompt.lower() or "example" in prompt.lower(),
                "has_constraints": "debe" in prompt.lower() or "must" in prompt.lower()
            }
        
        # Guardar baseline para comparación futura
        baseline_file = Path(__file__).parent / "baseline_prompts.json"
        with open(baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)
        
        # Verificaciones básicas
        for mode, data in baseline.items():
            assert data["length"] > 0, f"Prompt vacío para {mode}"
            assert data["estimated_tokens"] > 0
    
    @pytest.mark.asyncio
    async def test_current_response_quality_sample(self, mock_groq_response):
        """
        Captura una muestra de respuestas con los prompts actuales.
        Esto sirve como baseline de calidad.
        """
        from src.application.services.chat_service import ChatService
        
        # Mock del cliente
        mock_client = AsyncMock()
        mock_client.get_chat_completion.return_value = "Respuesta de prueba sobre funciones en Python..."
        
        mock_repo = Mock()
        mock_repo.get_session_messages.return_value = []
        mock_repo.add_message = Mock()
        
        service = ChatService(mock_repo, mock_client, gemini=None)
        
        # Preguntas de prueba
        test_questions = [
            "¿Qué es una función de primera clase?",
            "¿Cómo implementar un decorador?",
            "¿Cuál es la diferencia entre list y tuple?"
        ]
        
        responses = {}
        for question in test_questions:
            response = await service.handle_chat_message(
                session_id=1,
                user_message=question,
                agent_mode="Arquitecto Python Senior",
                file_id=None
            )
            responses[question] = {
                "response": response,
                "length": len(response) if response else 0
            }
        
        # Guardar respuestas baseline
        baseline_file = Path(__file__).parent / "baseline_responses.json"
        with open(baseline_file, "w") as f:
            json.dump(responses, f, indent=2, ensure_ascii=False)
        
        # Verificar que todas las respuestas tengan contenido
        for question, data in responses.items():
            assert data["length"] > 0, f"Respuesta vacía para: {question}"


@pytest.mark.unit
@pytest.mark.baseline
class TestPromptTokenCounting:
    """Tests para medir tokens de los prompts actuales."""
    
    def test_measure_current_token_usage(self):
        """
        Mide el uso actual de tokens para establecer baseline.
        Después del refactor, compararemos con estos números.
        """
        from src.adapters.agents.prompts import get_system_prompt
        
        modes = [
            "Arquitecto Python Senior",
            "Ingeniero de Código",
            "Auditor de Seguridad",
            "Especialista en Bases de Datos",
            "Ingeniero de Refactoring"
        ]
        
        token_usage = {}
        for mode in modes:
            prompt = get_system_prompt(mode)
            
            # Estimación simple: 4 chars ≈ 1 token
            estimated_tokens = len(prompt) // 4
            
            token_usage[mode] = {
                "chars": len(prompt),
                "estimated_tokens": estimated_tokens,
                "lines": prompt.count('\n') + 1
            }
        
        # Guardar métricas
        metrics_file = Path(__file__).parent / "baseline_tokens.json"
        with open(metrics_file, "w") as f:
            json.dump(token_usage, f, indent=2)
        
        # Calcular promedio
        avg_tokens = sum(data["estimated_tokens"] for data in token_usage.values()) / len(token_usage)
        
        print(f"\n📊 Token Usage Baseline:")
        print(f"   Average tokens per prompt: {avg_tokens:.0f}")
        print(f"   Min: {min(data['estimated_tokens'] for data in token_usage.values())}")
        print(f"   Max: {max(data['estimated_tokens'] for data in token_usage.values())}")
        
        # Guardar para comparación
        assert avg_tokens > 0


@pytest.mark.unit
class TestPromptContentBaseline:
    """Tests que verifican el contenido actual de los prompts."""
    
    def test_prompts_contain_key_elements(self):
        """Verifica que los prompts actuales contengan elementos clave."""
        from src.adapters.agents.prompts import get_system_prompt
        
        architect_prompt = get_system_prompt("Arquitecto Python Senior")
        
        # Elementos que esperamos encontrar
        expected_elements = [
            ("Python", "Debe mencionar Python"),
            ("código" or "code", "Debe mencionar código"),
        ]
        
        for element, description in expected_elements:
            assert element.lower() in architect_prompt.lower(), description
    
    def test_prompts_are_in_spanish(self):
        """Verifica que los prompts estén en español."""
        from src.adapters.agents.prompts import get_system_prompt
        
        # Palabras comunes en español
        spanish_words = ["eres", "debes", "puedes", "código", "función"]
        
        for mode in ["Arquitecto Python Senior", "DBA"]:
            prompt = get_system_prompt(mode)
            prompt_lower = prompt.lower()
            
            # Al menos algunas palabras en español deben estar presentes
            spanish_count = sum(1 for word in spanish_words if word in prompt_lower)
            assert spanish_count > 0, f"Prompt para {mode} no parece estar en español"


@pytest.mark.unit
class TestPromptConsistency:
    """Tests que verifican consistencia entre prompts."""
    
    def test_all_prompts_have_similar_structure(self):
        """Verifica que todos los prompts tengan estructura similar."""
        from src.adapters.agents.prompts import get_system_prompt
        
        modes = [
            "Arquitecto Python Senior",
            "Ingeniero de Código",
            "Auditor de Seguridad"
        ]
        
        structures = []
        for mode in modes:
            prompt = get_system_prompt(mode)
            structure = {
                "has_role_definition": "eres" in prompt.lower() or "you are" in prompt.lower(),
                "has_instructions": "debe" in prompt.lower() or "must" in prompt.lower(),
                "has_formatting": "formato" in prompt.lower() or "format" in prompt.lower(),
                "length_category": "long" if len(prompt) > 2000 else "medium" if len(prompt) > 1000 else "short"
            }
            structures.append(structure)
        
        # Verificar que todos tengan definición de rol
        assert all(s["has_role_definition"] for s in structures), "Todos deben definir el rol"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.baseline
class TestPromptPerformanceBaseline:
    """Tests de performance con prompts actuales."""
    
    @pytest.mark.asyncio
    async def test_response_time_baseline(self):
        """
        Mide el tiempo de respuesta con prompts actuales.
        Esto establece un baseline de performance.
        """
        import time
        from src.application.services.chat_service import ChatService
        
        mock_client = AsyncMock()
        mock_client.get_chat_completion.return_value = "Respuesta de prueba"
        
        mock_repo = Mock()
        mock_repo.get_session_messages.return_value = []
        mock_repo.add_message = Mock()
        
        service = ChatService(mock_repo, mock_client, gemini=None)
        
        # Medir tiempo
        start = time.time()
        await service.handle_chat_message(
            session_id=1,
            user_message="Test question",
            agent_mode="Arquitecto Python Senior",
            file_id=None
        )
        elapsed = time.time() - start
        
        # Guardar métrica
        metrics = {"response_time_seconds": elapsed}
        metrics_file = Path(__file__).parent / "baseline_performance.json"
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n⏱️  Response time baseline: {elapsed:.3f}s")
        
        # Después del refactor, el tiempo debería ser similar o mejor
        assert elapsed < 5.0, "Respuesta muy lenta"
