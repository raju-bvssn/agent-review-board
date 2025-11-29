"""Unit tests for HuggingFace provider."""

import pytest
from unittest.mock import Mock, patch
import requests


class TestHuggingFaceProvider:
    """Test suite for HuggingFaceProvider."""
    
    def test_provider_initialization(self):
        """Test provider initialization with API key."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        assert provider.api_key == "test-token"
        assert provider.model == "tiiuae/falcon-7b-instruct"
        assert provider.timeout == 60
    
    def test_missing_api_key(self):
        """Test that missing API key raises error."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        with pytest.raises(ValueError, match="API key is required"):
            HuggingFaceProvider(api_key=None)
    
    def test_list_models(self):
        """Test listing available models."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(api_key="test-token")
        models = provider.list_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "tiiuae/falcon-7b-instruct" in models
        assert "mistralai/Mistral-7B-Instruct-v0.2" in models
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_generate_text_success(self, mock_post):
        """Test successful text generation."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "Generated response"}
        ]
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="test-token")
        result = provider.generate_text("test prompt")
        
        assert result == "Generated response"
        mock_post.assert_called_once()
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_generate_text_model_loading(self, mock_post):
        """Test handling of model loading state."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        # Mock 503 response (model loading)
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "error": "Model is loading",
            "estimated_time": 20
        }
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        with pytest.raises(Exception, match="Model is loading"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_generate_text_rate_limit(self, mock_post):
        """Test rate limit handling."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        # Mock 429 response (rate limit)
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        with pytest.raises(Exception, match="Rate limit"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_generate_text_invalid_key(self, mock_post):
        """Test invalid API key handling."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        # Mock 401 response (unauthorized)
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid token"}
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="invalid-token")
        
        with pytest.raises(ValueError, match="Invalid HuggingFace API key"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_generate_text_timeout(self, mock_post):
        """Test timeout handling."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        with pytest.raises(Exception, match="timeout"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_generate_text_connection_error(self, mock_post):
        """Test connection error handling."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        with pytest.raises(Exception, match="Connection error"):
            provider.generate_text("test prompt")
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_validate_connection_success(self, mock_post):
        """Test successful connection validation."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "OK"}
        ]
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="test-token")
        assert provider.validate_connection() is True
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_validate_connection_failure(self, mock_post):
        """Test failed connection validation."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_post.side_effect = Exception("Connection failed")
        
        provider = HuggingFaceProvider(api_key="test-token")
        assert provider.validate_connection() is False
    
    def test_get_provider_name(self):
        """Test provider name."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(api_key="test-token")
        assert provider.get_provider_name() == "huggingface"
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_chat(self, mock_post):
        """Test chat functionality."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "Chat response"}
        ]
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = provider.chat(messages)
        assert result == "Chat response"
        
        # Verify that messages were formatted into a prompt
        call_args = mock_post.call_args
        assert "User:" in str(call_args)
        assert "Assistant:" in str(call_args)
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_embed_success(self, mock_post):
        """Test successful embedding generation."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [0.1, 0.2, 0.3, 0.4]
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="test-token")
        result = provider.embed("test text")
        
        assert isinstance(result, list)
        assert len(result) == 4
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_embed_failure(self, mock_post):
        """Test embedding failure handling."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        with pytest.raises(Exception, match="embedding failed"):
            provider.embed("test text")
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_custom_model(self, mock_post):
        """Test using custom model."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "Custom model response"}
        ]
        mock_post.return_value = mock_response
        
        provider = HuggingFaceProvider(
            api_key="test-token",
            model="mistralai/Mistral-7B-Instruct-v0.2"
        )
        
        result = provider.generate_text("test prompt")
        assert result == "Custom model response"
        
        # Verify correct model URL was called
        call_args = mock_post.call_args
        assert "mistralai/Mistral-7B-Instruct-v0.2" in call_args[0][0]
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_response_format_variations(self, mock_post):
        """Test handling different response formats."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        # Test format 1: list with generated_text
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "Response 1"}]
        mock_post.return_value = mock_response
        
        result = provider.generate_text("test")
        assert result == "Response 1"
        
        # Test format 2: list with text
        mock_response.json.return_value = [{"text": "Response 2"}]
        result = provider.generate_text("test")
        assert result == "Response 2"
        
        # Test format 3: dict with generated_text
        mock_response.json.return_value = {"generated_text": "Response 3"}
        result = provider.generate_text("test")
        assert result == "Response 3"

