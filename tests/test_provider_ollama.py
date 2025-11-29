"""Unit tests for Ollama provider."""

import pytest
from unittest.mock import Mock, patch
import requests


class TestOllamaProvider:
    """Test suite for OllamaProvider."""
    
    def test_provider_initialization(self):
        """Test provider initialization without API key."""
        from app.llm.ollama_provider import OllamaProvider
        
        # Ollama doesn't require API key
        provider = OllamaProvider()
        
        assert provider.api_key is None
        assert provider.model == "llama3"
        assert provider.api_base == "http://localhost:11434/api"
    
    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        from app.llm.ollama_provider import OllamaProvider
        
        provider = OllamaProvider(
            model="mistral",
            base_url="http://custom-host:8080/api",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert provider.model == "mistral"
        assert provider.api_base == "http://custom-host:8080/api"
        assert provider.temperature == 0.5
        assert provider.num_predict == 1000
    
    def test_list_models_fallback(self):
        """Test listing models when Ollama is not running."""
        from app.llm.ollama_provider import OllamaProvider
        
        provider = OllamaProvider()
        models = provider.list_models()
        
        # Should return known models even if Ollama is offline
        assert isinstance(models, list)
        assert len(models) > 0
        assert "llama3" in models
        assert "mistral" in models
        assert "phi3" in models
    
    @patch('app.llm.ollama_provider.requests.get')
    def test_list_models_from_api(self, mock_get):
        """Test listing models from running Ollama instance."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:latest"},
                {"name": "mistral:7b"},
                {"name": "phi3:medium"}
            ]
        }
        mock_get.return_value = mock_response
        
        provider = OllamaProvider()
        models = provider.list_models()
        
        assert "llama3:latest" in models
        assert "mistral:7b" in models
        assert "phi3:medium" in models
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_generate_text_success(self, mock_post):
        """Test successful text generation."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated text response",
            "done": True
        }
        mock_post.return_value = mock_response
        
        provider = OllamaProvider()
        result = provider.generate_text("test prompt")
        
        assert result == "Generated text response"
        mock_post.assert_called_once()
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_generate_text_model_not_found(self, mock_post):
        """Test error when model is not pulled."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Model not found"}
        mock_post.return_value = mock_response
        
        provider = OllamaProvider(model="nonexistent-model")
        
        with pytest.raises(Exception, match="Model .* not found"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_generate_text_connection_error(self, mock_post):
        """Test handling when Ollama is not running."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        provider = OllamaProvider()
        
        with pytest.raises(Exception, match="Cannot connect to Ollama"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_generate_text_timeout(self, mock_post):
        """Test timeout handling."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        provider = OllamaProvider()
        
        with pytest.raises(Exception, match="timeout"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.ollama_provider.requests.get')
    def test_validate_connection_success(self, mock_get):
        """Test successful connection validation."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        provider = OllamaProvider()
        assert provider.validate_connection() is True
    
    @patch('app.llm.ollama_provider.requests.get')
    def test_validate_connection_failure(self, mock_get):
        """Test failed connection validation."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_get.side_effect = Exception("Connection failed")
        
        provider = OllamaProvider()
        assert provider.validate_connection() is False
    
    @patch('app.llm.ollama_provider.requests.get')
    def test_is_running(self, mock_get):
        """Test checking if Ollama is running."""
        from app.llm.ollama_provider import OllamaProvider
        
        # Test when running
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        provider = OllamaProvider()
        assert provider.is_running() is True
        
        # Test when not running
        mock_get.side_effect = Exception("Not running")
        assert provider.is_running() is False
    
    def test_get_provider_name(self):
        """Test provider name."""
        from app.llm.ollama_provider import OllamaProvider
        
        provider = OllamaProvider()
        assert provider.get_provider_name() == "ollama"
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_chat_native_api(self, mock_post):
        """Test chat using native Ollama chat API."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Chat response"},
            "done": True
        }
        mock_post.return_value = mock_response
        
        provider = OllamaProvider()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = provider.chat(messages)
        assert result == "Chat response"
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_chat_fallback_to_generate(self, mock_post):
        """Test chat falling back to generate API."""
        from app.llm.ollama_provider import OllamaProvider
        
        # First call (chat API) fails
        mock_post.side_effect = [
            Exception("Chat API not available"),
            Mock(
                status_code=200,
                json=lambda: {"response": "Fallback response", "done": True}
            )
        ]
        
        provider = OllamaProvider()
        
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        result = provider.chat(messages)
        assert result == "Fallback response"
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_embed_success(self, mock_post):
        """Test successful embedding generation."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        mock_post.return_value = mock_response
        
        provider = OllamaProvider()
        result = provider.embed("test text")
        
        assert isinstance(result, list)
        assert len(result) == 4
        assert result == [0.1, 0.2, 0.3, 0.4]
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_embed_failure(self, mock_post):
        """Test embedding failure handling."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        provider = OllamaProvider()
        
        with pytest.raises(Exception, match="embedding failed"):
            provider.embed("test text")
    
    @patch('app.llm.ollama_provider.requests.get')
    def test_get_ollama_version(self, mock_get):
        """Test getting Ollama version."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.1.23"}
        mock_get.return_value = mock_response
        
        provider = OllamaProvider()
        version = provider.get_ollama_version()
        
        assert version == "0.1.23"
    
    @patch('app.llm.ollama_provider.requests.get')
    def test_get_ollama_version_failure(self, mock_get):
        """Test getting version when Ollama is not running."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_get.side_effect = Exception("Not running")
        
        provider = OllamaProvider()
        version = provider.get_ollama_version()
        
        assert version is None
    
    def test_messages_to_prompt(self):
        """Test message to prompt conversion."""
        from app.llm.ollama_provider import OllamaProvider
        
        provider = OllamaProvider()
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]
        
        prompt = provider._messages_to_prompt(messages)
        
        assert "System: You are helpful" in prompt
        assert "User: Hello" in prompt
        assert "Assistant: Hi there" in prompt
        assert "User: How are you?" in prompt
        assert "Assistant:" in prompt  # Prompt for next response
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_custom_parameters(self, mock_post):
        """Test generation with custom parameters."""
        from app.llm.ollama_provider import OllamaProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Custom response",
            "done": True
        }
        mock_post.return_value = mock_response
        
        provider = OllamaProvider(
            model="mistral",
            temperature=0.5,
            max_tokens=1000
        )
        
        result = provider.generate_text(
            "test prompt",
            temperature=0.9,
            max_tokens=500
        )
        
        assert result == "Custom response"
        
        # Verify parameters were passed
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['options']['temperature'] == 0.9
        assert payload['options']['num_predict'] == 500

