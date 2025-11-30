"""Unit tests for Provider Factory."""

import pytest
from unittest.mock import patch
from app.llm.provider_factory import ProviderFactory
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider


class TestProviderFactory:
    """Tests for ProviderFactory."""
    
    def test_create_mock_provider(self):
        """Test creating a mock provider."""
        provider = ProviderFactory.create_provider('mock')
        
        assert isinstance(provider, MockLLMProvider)
        assert provider.get_provider_name() == 'mockllm'
    
    def test_create_openai_provider_with_api_key(self):
        """Test creating OpenAI provider with API key."""
        provider = ProviderFactory.create_provider('openai', api_key='test-key')
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == 'test-key'
    
    def test_create_anthropic_provider_with_api_key(self):
        """Test creating Anthropic provider with API key."""
        provider = ProviderFactory.create_provider('anthropic', api_key='test-key')
        
        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == 'test-key'
    
    def test_create_provider_case_insensitive(self):
        """Test that provider names are case insensitive."""
        provider1 = ProviderFactory.create_provider('Mock')
        provider2 = ProviderFactory.create_provider('MOCK')
        provider3 = ProviderFactory.create_provider('mock')
        
        assert all(isinstance(p, MockLLMProvider) for p in [provider1, provider2, provider3])
    
    def test_create_provider_with_whitespace(self):
        """Test that provider names handle whitespace."""
        provider = ProviderFactory.create_provider('  mock  ')
        
        assert isinstance(provider, MockLLMProvider)
    
    def test_create_provider_unknown_raises_error(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            ProviderFactory.create_provider('unknown_provider')
    
    def test_create_openai_without_api_key_raises_error(self):
        """Test that OpenAI without API key raises error."""
        with pytest.raises(ValueError, match="API key required"):
            ProviderFactory.create_provider('openai')
    
    def test_create_anthropic_without_api_key_raises_error(self):
        """Test that Anthropic without API key raises error."""
        with pytest.raises(ValueError, match="API key required"):
            ProviderFactory.create_provider('anthropic')
    
    def test_get_available_providers(self):
        """Test getting list of available providers."""
        providers = ProviderFactory.get_available_providers()
        
        assert isinstance(providers, list)
        assert 'mock' in providers
        assert 'openai' in providers
        assert 'anthropic' in providers
        assert 'gemini' in providers
        assert 'huggingface' in providers
        assert 'ollama' in providers
        assert len(providers) >= 6
    
    def test_is_valid_provider(self):
        """Test checking if provider is valid."""
        assert ProviderFactory.is_valid_provider('mock') is True
        assert ProviderFactory.is_valid_provider('openai') is True
        assert ProviderFactory.is_valid_provider('anthropic') is True
        assert ProviderFactory.is_valid_provider('gemini') is True
        assert ProviderFactory.is_valid_provider('huggingface') is True
        assert ProviderFactory.is_valid_provider('ollama') is True
        assert ProviderFactory.is_valid_provider('unknown') is False
    
    def test_requires_api_key(self):
        """Test checking if provider requires API key."""
        assert ProviderFactory.requires_api_key('mock') is False
        assert ProviderFactory.requires_api_key('ollama') is False
        assert ProviderFactory.requires_api_key('openai') is True
        assert ProviderFactory.requires_api_key('anthropic') is True
        assert ProviderFactory.requires_api_key('gemini') is True
        assert ProviderFactory.requires_api_key('huggingface') is True
    
    def test_create_provider_with_custom_config(self):
        """Test creating provider with custom configuration."""
        provider = ProviderFactory.create_provider(
            'mock',
            custom_param='test_value'
        )
        
        assert provider.config.get('custom_param') == 'test_value'
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_create_gemini_provider(self, mock_client_class):
        """Test creating Gemini provider."""
        from app.llm.gemini_provider import GeminiProvider
        
        provider = ProviderFactory.create_provider('gemini', api_key='test-key')
        
        assert isinstance(provider, GeminiProvider)
        assert provider.api_key == 'test-key'
    
    def test_create_huggingface_provider(self):
        """Test creating HuggingFace provider."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        provider = ProviderFactory.create_provider('huggingface', api_key='test-token')
        
        assert isinstance(provider, HuggingFaceProvider)
        assert provider.api_key == 'test-token'
    
    def test_create_ollama_provider(self):
        """Test creating Ollama provider without API key."""
        from app.llm.ollama_provider import OllamaProvider
        
        provider = ProviderFactory.create_provider('ollama')
        
        assert isinstance(provider, OllamaProvider)
        assert provider.api_key is None
    
    def test_get_free_providers(self):
        """Test getting list of free providers."""
        free_providers = ProviderFactory.get_free_providers()
        
        assert isinstance(free_providers, list)
        assert 'mock' in free_providers
        assert 'gemini' in free_providers
        assert 'huggingface' in free_providers
        assert 'ollama' in free_providers
        assert 'openai' not in free_providers
        assert 'anthropic' not in free_providers
    
    def test_get_provider_info(self):
        """Test getting provider information."""
        # Test Gemini info
        gemini_info = ProviderFactory.get_provider_info('gemini')
        assert gemini_info['free'] is True
        assert gemini_info['requires_key'] is True
        assert gemini_info['local'] is False
        
        # Test Ollama info
        ollama_info = ProviderFactory.get_provider_info('ollama')
        assert ollama_info['free'] is True
        assert ollama_info['requires_key'] is False
        assert ollama_info['local'] is True
        
        # Test OpenAI info
        openai_info = ProviderFactory.get_provider_info('openai')
        assert openai_info['free'] is False
        assert openai_info['requires_key'] is True
        
        # Test unknown provider
        unknown_info = ProviderFactory.get_provider_info('unknown')
        assert unknown_info == {}
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_create_gemini_without_api_key_raises_error(self, mock_client_class):
        """Test that Gemini without API key raises error."""
        with pytest.raises(ValueError, match="API key required"):
            ProviderFactory.create_provider('gemini')
    
    def test_create_huggingface_without_api_key_raises_error(self):
        """Test that HuggingFace without API key raises error."""
        with pytest.raises(ValueError, match="API key required"):
            ProviderFactory.create_provider('huggingface')

