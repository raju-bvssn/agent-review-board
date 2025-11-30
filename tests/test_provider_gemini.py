"""Unit tests for Gemini provider with REST API v1."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestGeminiProvider:
    """Test suite for GeminiProvider using REST API v1."""
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_provider_initialization(self, mock_client_class):
        """Test provider initialization with API key."""
        from app.llm.gemini_provider import GeminiProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        
        assert provider.api_key == "test-key"
        assert provider.model == "gemini-1.5-flash"
        mock_client_class.assert_called_once()
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_missing_api_key(self, mock_client_class):
        """Test that missing API key raises error."""
        from app.llm.gemini_provider import GeminiProvider
        
        with pytest.raises(ValueError, match="API key is required"):
            GeminiProvider(api_key=None)
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', False)
    def test_missing_package(self):
        """Test error when httpx is not installed."""
        from app.llm.gemini_provider import GeminiProvider
        
        with pytest.raises(ImportError, match="httpx package not installed"):
            GeminiProvider(api_key="test-key")
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_list_models(self, mock_client_class):
        """Test listing available models."""
        from app.llm.gemini_provider import GeminiProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        models = provider.list_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert 'gemini-1.5-flash' in models
        assert 'gemini-1.5-pro' in models
        assert 'gemini-pro' in models
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_list_models_fallback(self, mock_client_class):
        """Test that known models are returned."""
        from app.llm.gemini_provider import GeminiProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        models = provider.list_models()
        
        assert isinstance(models, list)
        assert "gemini-1.5-flash" in models
        assert "gemini-1.5-pro" in models
        assert "gemini-pro" in models
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_generate_text_success(self, mock_client_class):
        """Test successful text generation."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Generated response text"}
                        ]
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        result = provider.generate_text("test prompt")
        
        assert result == "Generated response text"
        mock_client.post.assert_called_once()
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_generate_text_rate_limit(self, mock_client_class):
        """Test rate limit handling."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        
        with pytest.raises(Exception, match="rate limit"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_generate_text_invalid_key(self, mock_client_class):
        """Test invalid API key handling."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="invalid-key")
        
        with pytest.raises(ValueError, match="Invalid Gemini API key"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_validate_connection_success(self, mock_client_class):
        """Test successful connection validation."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello"}
                        ]
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        assert provider.validate_connection() is True
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_validate_connection_failure(self, mock_client_class):
        """Test failed connection validation."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        result = provider.validate_connection()
        assert result is False
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_get_provider_name(self, mock_client_class):
        """Test provider name."""
        from app.llm.gemini_provider import GeminiProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        assert provider.get_provider_name() == "gemini"
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_chat(self, mock_client_class):
        """Test chat functionality."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Chat response"}
                        ]
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = provider.chat(messages)
        assert result == "Chat response"
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_embed(self, mock_client_class):
        """Test embedding generation."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": {
                "values": [0.1, 0.2, 0.3, 0.4]
            }
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        result = provider.embed("test text")
        
        assert isinstance(result, list)
        assert len(result) == 4
        assert result == [0.1, 0.2, 0.3, 0.4]
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_embed_failure(self, mock_client_class):
        """Test embedding failure handling."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        
        with pytest.raises(Exception, match="Gemini embedding failed"):
            provider.embed("test text")
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_custom_parameters(self, mock_client_class):
        """Test provider with custom parameters."""
        from app.llm.gemini_provider import GeminiProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(
            api_key="test-key",
            model="gemini-1.5-pro",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert provider.model == "gemini-1.5-pro"
        assert provider.temperature == 0.5
        assert provider.max_output_tokens == 1000
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_404_error_handling(self, mock_client_class):
        """Test 404 error provides helpful message about v1 API."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="Model not supported for API v1"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_debug_logging(self, mock_client_class, capsys):
        """Test that debug logging prints model name."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Response"}
                        ]
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        provider.generate_text("test", model="gemini-1.5-pro")
        
        # Check that debug message was printed
        captured = capsys.readouterr()
        assert "[Gemini] Using model: gemini-1.5-pro" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
