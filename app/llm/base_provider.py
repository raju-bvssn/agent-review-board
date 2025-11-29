"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers.
    
    All provider implementations must inherit from this class and implement
    the required methods. This ensures a unified interface across different
    LLM providers (OpenAI, Anthropic, local models, etc.).
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize the provider.
        
        Args:
            api_key: API key for the provider (if required)
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text string
            
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models for this provider.
        
        Returns:
            List of model names/identifiers
            
        Raises:
            Exception: If listing fails
        """
        pass
    
    def validate_connection(self) -> bool:
        """Validate that the provider connection works.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            models = self.list_models()
            return len(models) > 0
        except Exception:
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of this provider.
        
        Returns:
            Provider name string
        """
        return self.__class__.__name__.replace("Provider", "").lower()

