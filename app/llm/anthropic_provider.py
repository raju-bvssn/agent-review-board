"""Anthropic LLM provider implementation."""

import time
from typing import List, Optional, Dict, Any
import requests
from app.llm.base_provider import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider with retry logic and error handling.
    
    This provider implements the BaseLLMProvider interface for Anthropic's API,
    including support for retries, timeouts, and error mapping.
    """
    
    API_BASE = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    ANTHROPIC_VERSION = "2023-06-01"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            **kwargs: Additional configuration
                - model: Default model to use
                - timeout: Request timeout in seconds
                - max_retries: Maximum number of retries
                - temperature: Default temperature
                - max_tokens: Default max tokens
        """
        super().__init__(api_key, **kwargs)
        
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.model = kwargs.get('model', self.DEFAULT_MODEL)
        self.timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self.max_retries = kwargs.get('max_retries', self.MAX_RETRIES)
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens_default = kwargs.get('max_tokens', 2000)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using Anthropic API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
                - model: Override default model
                - temperature: Override default temperature
                - max_tokens: Override default max tokens
                
        Returns:
            Generated text string
            
        Raises:
            Exception: If generation fails after all retries
        """
        model = kwargs.get('model', self.model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens_default)
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.API_BASE}/messages",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['content'][0]['text']
                
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = self.RETRY_DELAY * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 401:
                    raise ValueError("Invalid API key")
                
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.RETRY_DELAY)
                        continue
                    raise Exception(f"Anthropic API server error: {response.status_code}")
                
                else:
                    # Client error - don't retry
                    error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"Anthropic API error: {error_detail}")
            
            except requests.exceptions.Timeout:
                last_exception = Exception(f"Request timeout after {self.timeout}s")
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
            
            except requests.exceptions.ConnectionError as e:
                last_exception = Exception(f"Connection error: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
            
            except Exception as e:
                last_exception = e
                # Don't retry on unexpected exceptions
                break
        
        # If we get here, all retries failed
        raise last_exception or Exception("Failed to generate text")
    
    def list_models(self) -> List[str]:
        """List available Anthropic models.
        
        Note: Anthropic doesn't have a models endpoint, so we return
        a hardcoded list of known models.
        
        Returns:
            List of model identifiers
        """
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
        ]
    
    def validate_connection(self) -> bool:
        """Validate that the API key works by making a minimal API call.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Make a minimal request to validate the key
            result = self.generate_text(
                "Say 'OK' if you can read this.",
                max_tokens=10
            )
            return len(result) > 0
        except Exception:
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of this provider.
        
        Returns:
            Provider name string
        """
        return "anthropic"

