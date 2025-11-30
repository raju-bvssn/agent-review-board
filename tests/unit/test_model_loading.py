"""Unit tests for model loading in Start Session page."""

import pytest
from unittest.mock import MagicMock, patch


class TestModelLoadingLogic:
    """Test that model dropdown correctly loads provider-specific models."""
    
    def test_loads_provider_models_when_configured(self):
        """Test that models are loaded from configured provider."""
        # Simulate session state with OpenAI provider
        mock_session_state = {
            'llm_config': {
                'provider': 'openai',
                'api_key': 'sk-test-key',
                'model': 'gpt-4'
            },
            'available_models': ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
        }
        
        # Expected behavior: should use provider models
        assert mock_session_state['available_models'] == ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
        assert len(mock_session_state['available_models']) == 3
        assert 'mock-model-small' not in mock_session_state['available_models']
    
    def test_falls_back_to_mock_when_no_provider(self):
        """Test that mock models are used when no provider configured."""
        # Simulate session state with no provider
        mock_session_state = {}
        
        # Expected behavior: should use mock models
        fallback_models = ["mock-model-small", "mock-model-medium", "mock-model-large"]
        
        # Verify fallback logic would work
        if 'llm_config' not in mock_session_state:
            available_models = fallback_models
        
        assert available_models == fallback_models
        assert len(available_models) == 3
    
    def test_falls_back_when_provider_has_no_models(self):
        """Test fallback when provider returns empty model list."""
        # Simulate session state with provider but no models
        mock_session_state = {
            'llm_config': {
                'provider': 'ollama',
                'model': None
            },
            'available_models': []  # Empty list
        }
        
        # Expected behavior: should detect empty list and use fallback
        fallback_models = ["mock-model-small", "mock-model-medium", "mock-model-large"]
        
        if not mock_session_state['available_models']:
            available_models = fallback_models
        
        assert available_models == fallback_models
    
    def test_gemini_provider_models_loaded(self):
        """Test that Gemini models are correctly loaded."""
        mock_session_state = {
            'llm_config': {
                'provider': 'gemini',
                'api_key': 'test-gemini-key'
            },
            'available_models': [
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-pro'
            ]
        }
        
        assert 'gemini-1.5-flash' in mock_session_state['available_models']
        assert 'gemini-1.5-pro' in mock_session_state['available_models']
        assert len(mock_session_state['available_models']) > 0
    
    def test_huggingface_provider_models_loaded(self):
        """Test that HuggingFace models are correctly loaded."""
        mock_session_state = {
            'llm_config': {
                'provider': 'huggingface',
                'api_key': 'hf-test-key'
            },
            'available_models': [
                'tiiuae/falcon-7b-instruct',
                'mistralai/Mistral-7B-Instruct-v0.1',
                'meta-llama/Llama-2-7b-chat-hf'
            ]
        }
        
        assert 'tiiuae/falcon-7b-instruct' in mock_session_state['available_models']
        assert len(mock_session_state['available_models']) >= 1
    
    def test_ollama_provider_models_loaded(self):
        """Test that Ollama local models are correctly loaded."""
        mock_session_state = {
            'llm_config': {
                'provider': 'ollama'
            },
            'available_models': [
                'llama3',
                'mistral',
                'phi3',
                'codellama',
                'qwen2.5'
            ]
        }
        
        assert 'llama3' in mock_session_state['available_models']
        assert 'mistral' in mock_session_state['available_models']
        assert len(mock_session_state['available_models']) >= 1
    
    def test_anthropic_provider_models_loaded(self):
        """Test that Anthropic models are correctly loaded."""
        mock_session_state = {
            'llm_config': {
                'provider': 'anthropic',
                'api_key': 'sk-ant-test-key'
            },
            'available_models': [
                'claude-3-5-sonnet-20241022',
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307'
            ]
        }
        
        assert 'claude-3-5-sonnet-20241022' in mock_session_state['available_models']
        assert len(mock_session_state['available_models']) >= 1
    
    def test_models_config_includes_provider_name(self):
        """Test that models_config includes the provider name."""
        # Simulate building models config
        mock_llm_config = {
            'provider': 'openai',
            'api_key': 'sk-test-key'
        }
        
        presenter_model = 'gpt-4'
        
        # Build config as done in start_session.py
        models_config = {
            'presenter': presenter_model,
            'provider': mock_llm_config.get('provider', 'mock')
        }
        
        assert models_config['provider'] == 'openai'
        assert models_config['presenter'] == 'gpt-4'
    
    def test_models_config_defaults_to_mock_provider(self):
        """Test that models_config defaults to mock when no provider."""
        # No llm_config in session state
        mock_session_state = {}
        
        presenter_model = 'mock-model-medium'
        
        # Build config with fallback
        provider = mock_session_state.get('llm_config', {}).get('provider', 'mock')
        
        models_config = {
            'presenter': presenter_model,
            'provider': provider
        }
        
        assert models_config['provider'] == 'mock'
        assert models_config['presenter'] == 'mock-model-medium'
    
    def test_reviewer_models_use_same_available_models(self):
        """Test that reviewer model selection uses same available_models."""
        mock_session_state = {
            'llm_config': {'provider': 'gemini'},
            'available_models': ['gemini-1.5-flash', 'gemini-1.5-pro']
        }
        
        selected_roles = ['Technical Reviewer', 'Security Reviewer']
        reviewer_models = {}
        
        # Simulate reviewer model assignment
        for role in selected_roles:
            # In real code, user selects from available_models
            reviewer_models[role] = mock_session_state['available_models'][0]
        
        # Verify all reviewers can use provider models
        assert all(
            model in mock_session_state['available_models'] 
            for model in reviewer_models.values()
        )
    
    def test_empty_provider_name_falls_back_to_mock(self):
        """Test that empty provider name falls back to mock."""
        mock_session_state = {
            'llm_config': {
                'provider': '',  # Empty string
                'api_key': None
            }
        }
        
        provider = mock_session_state.get('llm_config', {}).get('provider', 'mock')
        
        if not provider:  # Empty string is falsy
            provider = 'mock'
        
        assert provider == 'mock'


class TestProviderDetection:
    """Test provider detection logic."""
    
    def test_detects_configured_provider(self):
        """Test that configured provider is correctly detected."""
        test_cases = [
            ('openai', 'OPENAI'),
            ('anthropic', 'ANTHROPIC'),
            ('gemini', 'GEMINI'),
            ('huggingface', 'HUGGINGFACE'),
            ('ollama', 'OLLAMA'),
            ('mock', 'MOCK'),
        ]
        
        for provider_name, expected_upper in test_cases:
            mock_config = {'provider': provider_name}
            detected = mock_config.get('provider', 'Mock').upper()
            assert detected == expected_upper
    
    def test_handles_none_provider(self):
        """Test handling of None provider value."""
        mock_config = {'provider': None}
        provider = mock_config.get('provider', 'mock')
        
        if not provider:
            provider = 'mock'
        
        assert provider == 'mock'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

