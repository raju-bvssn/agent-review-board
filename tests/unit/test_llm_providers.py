"""Unit tests for LLM providers."""

import pytest
from app.llm.base_provider import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""
    
    def test_provider_initialization(self):
        """Test that MockLLMProvider can be initialized."""
        provider = MockLLMProvider()
        
        assert provider is not None
        assert provider.get_provider_name() == "mockllm"
    
    def test_generate_text_returns_string(self):
        """Test that generate_text returns a string."""
        provider = MockLLMProvider()
        
        result = provider.generate_text("Test prompt")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_text_is_deterministic(self):
        """Test that generate_text returns deterministic responses."""
        provider = MockLLMProvider()
        
        result1 = provider.generate_text("Test prompt")
        
        # Reset and test again
        provider.reset()
        result2 = provider.generate_text("Test prompt")
        
        assert result1 == result2
    
    def test_generate_text_tracks_calls(self):
        """Test that MockLLMProvider tracks call count."""
        provider = MockLLMProvider()
        
        assert provider.get_call_count() == 0
        
        provider.generate_text("Prompt 1")
        assert provider.get_call_count() == 1
        
        provider.generate_text("Prompt 2")
        assert provider.get_call_count() == 2
    
    def test_generate_text_stores_last_prompt(self):
        """Test that MockLLMProvider stores last prompt."""
        provider = MockLLMProvider()
        
        prompt = "This is my test prompt"
        provider.generate_text(prompt)
        
        assert provider.get_last_prompt() == prompt
    
    def test_list_models_returns_list(self):
        """Test that list_models returns a list of strings."""
        provider = MockLLMProvider()
        
        models = provider.list_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(model, str) for model in models)
    
    def test_list_models_includes_expected_models(self):
        """Test that list_models includes expected mock models."""
        provider = MockLLMProvider()
        
        models = provider.list_models()
        
        assert "mock-model-small" in models
        assert "mock-model-medium" in models
        assert "mock-model-large" in models
    
    def test_validate_connection_succeeds(self):
        """Test that validate_connection returns True for MockProvider."""
        provider = MockLLMProvider()
        
        assert provider.validate_connection() is True
    
    def test_reset_clears_state(self):
        """Test that reset clears provider state."""
        provider = MockLLMProvider()
        
        provider.generate_text("Test prompt")
        assert provider.get_call_count() == 1
        assert provider.get_last_prompt() is not None
        
        provider.reset()
        assert provider.get_call_count() == 0
        assert provider.get_last_prompt() is None


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider abstract class."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseLLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            provider = BaseLLMProvider()
    
    def test_provider_interface_methods_exist(self):
        """Test that the interface defines required methods."""
        # Check that abstract methods are defined
        assert hasattr(BaseLLMProvider, 'generate_text')
        assert hasattr(BaseLLMProvider, 'list_models')
        assert hasattr(BaseLLMProvider, 'validate_connection')
        assert hasattr(BaseLLMProvider, 'get_provider_name')

