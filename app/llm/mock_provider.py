"""Mock LLM provider for testing."""

from typing import List, Optional
from app.llm.base_provider import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns deterministic responses.
    
    This provider is used for testing and development. It returns
    predictable responses without making real API calls.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize mock provider.
        
        Args:
            api_key: Not required for mock provider
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.call_count = 0
        self.last_prompt = None
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate deterministic mock text.
        
        Args:
            prompt: Input prompt (stored for testing)
            **kwargs: Ignored for mock provider
            
        Returns:
            Deterministic mock response
        """
        self.call_count += 1
        self.last_prompt = prompt
        
        # Return different responses based on call count for variety
        responses = [
            "This is a mock response from the LLM provider.",
            "This is the second mock response for testing purposes.",
            "Mock response number three with different content.",
            "Another deterministic mock response for testing.",
            "Final mock response in the rotation."
        ]
        
        response_index = (self.call_count - 1) % len(responses)
        return responses[response_index]
    
    def list_models(self) -> List[str]:
        """List mock models.
        
        Returns:
            List of mock model names
        """
        return [
            "mock-model-small",
            "mock-model-medium",
            "mock-model-large",
            "mock-model-expert"
        ]
    
    def reset(self) -> None:
        """Reset the provider state for testing."""
        self.call_count = 0
        self.last_prompt = None
    
    def get_call_count(self) -> int:
        """Get the number of times generate_text was called.
        
        Returns:
            Number of calls
        """
        return self.call_count
    
    def get_last_prompt(self) -> Optional[str]:
        """Get the last prompt that was passed to generate_text.
        
        Returns:
            Last prompt string or None
        """
        return self.last_prompt

