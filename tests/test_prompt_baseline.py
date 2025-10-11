"""
Tests de baseline para prompts actuales.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.application.services.chat_service import ChatServiceV2
from src.adapters.agents.prompts import get_system_prompt

@pytest.mark.unit
class TestPromptContentBaseline:
    """Tests que verifican el contenido actual de los prompts."""

    def test_prompts_contain_key_elements(self):
        """Verifica que los prompts actuales contengan elementos clave."""
        architect_prompt = get_system_prompt("architect")
        expected_elements = [("Python", "Debe mencionar Python"), ("código", "Debe mencionar código")]
        for element, description in expected_elements:
            assert element.lower() in architect_prompt.lower(), description

    def test_prompts_are_in_spanish(self):
        """Verifica que los prompts estén en español."""
        spanish_words = ["eres", "debes", "puedes", "código", "función"]
        modes = ["architect", "code_generator", "security_analyst"]
        for mode in modes:
            prompt = get_system_prompt(mode).lower()
            assert any(word in prompt for word in spanish_words), f"El prompt para {mode} no parece estar en español."
