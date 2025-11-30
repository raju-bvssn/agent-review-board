"""LLM Provider Factory for dynamic provider instantiation."""

from typing import Optional, Dict, Any
from app.llm.base_provider import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.huggingface_provider import HuggingFaceProvider
from app.llm.ollama_provider import OllamaProvider
from app.utils.env import is_cloud


class ProviderFactory:
    """Factory for creating LLM provider instances.
    
    This factory allows dynamic provider selection based on configuration,
    ensuring consistent interface across all providers.
    
    Supported providers:
    - OpenAI (Paid - GPT-4, GPT-3.5)
    - Anthropic (Paid - Claude)
    - Gemini (FREE tier available - gemini-1.5-flash)
    - HuggingFace (FREE models available)
    - Ollama (FREE local models - LOCAL ONLY, not available in cloud)
    - Mock (Testing only)
    """
    
    # Registry of available providers
    # Build dynamically to exclude Ollama in cloud environment
    PROVIDERS = {
        'mock': MockLLMProvider,
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'gemini': GeminiProvider,
        'huggingface': HuggingFaceProvider,
    }
    
    # Add Ollama only in local environment (not supported in Streamlit Cloud)
    if not is_cloud():
        PROVIDERS['ollama'] = OllamaProvider
    
    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """Create a provider instance.
        
        Args:
            provider_name: Name of the provider
                ('mock', 'openai', 'anthropic', 'gemini', 'huggingface', 'ollama')
            api_key: API key for the provider (not required for mock/ollama)
            **kwargs: Additional provider-specific configuration
            
        Returns:
            Instance of BaseLLMProvider
            
        Raises:
            ValueError: If provider_name is not recognized
        """
        provider_name = provider_name.lower().strip()
        
        if provider_name not in cls.PROVIDERS:
            available = ', '.join(cls.PROVIDERS.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )
        
        provider_class = cls.PROVIDERS[provider_name]
        
        # Providers that don't require API key
        if provider_name in ('mock', 'ollama'):
            return provider_class(**kwargs)
        
        # Real providers require API key
        if not api_key:
            raise ValueError(f"API key required for {provider_name} provider")
        
        return provider_class(api_key=api_key, **kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider names.
        
        Returns:
            List of provider names
        """
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def is_valid_provider(cls, provider_name: str) -> bool:
        """Check if a provider name is valid.
        
        Args:
            provider_name: Name to check
            
        Returns:
            True if provider exists, False otherwise
        """
        return provider_name.lower().strip() in cls.PROVIDERS
    
    @classmethod
    def requires_api_key(cls, provider_name: str) -> bool:
        """Check if a provider requires an API key.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            True if API key required, False otherwise
        """
        no_key_providers = ['mock']
        if not is_cloud():
            no_key_providers.append('ollama')
        
        return provider_name.lower().strip() not in no_key_providers
    
    @classmethod
    def get_free_providers(cls) -> list:
        """Get list of free provider names.
        
        Returns:
            List of provider names that are free or have free tiers
        """
        free_providers = ['mock', 'gemini', 'huggingface']
        
        # Add Ollama only in local environment
        if not is_cloud():
            free_providers.append('ollama')
        
        return free_providers
    
    @classmethod
    def get_provider_info(cls, provider_name: str) -> Dict[str, Any]:
        """Get information about a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dictionary with provider information
        """
        info = {
            'mock': {
                'name': 'Mock Provider',
                'description': 'Testing only - generates deterministic responses',
                'free': True,
                'requires_key': False,
                'local': True,
            },
            'openai': {
                'name': 'OpenAI',
                'description': 'GPT-4, GPT-3.5 models',
                'free': False,
                'requires_key': True,
                'local': False,
            },
            'anthropic': {
                'name': 'Anthropic',
                'description': 'Claude models',
                'free': False,
                'requires_key': True,
                'local': False,
            },
            'gemini': {
                'name': 'Google Gemini',
                'description': 'FREE gemini-1.5-flash (15 req/min)',
                'free': True,
                'requires_key': True,
                'local': False,
            },
            'huggingface': {
                'name': 'HuggingFace',
                'description': 'FREE models like falcon-7b-instruct',
                'free': True,
                'requires_key': True,
                'local': False,
            },
            'ollama': {
                'name': 'Ollama (Local)',
                'description': 'FREE local models (llama3, mistral, etc.) - LOCAL ONLY',
                'free': True,
                'requires_key': False,
                'local': True,
                'cloud_available': False,
            },
        }
        
        return info.get(provider_name.lower().strip(), {})

