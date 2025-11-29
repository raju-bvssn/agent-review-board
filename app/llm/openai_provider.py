"""OpenAI LLM provider implementation."""

import time
from typing import List, Optional, Dict, Any
import requests
from app.llm.base_provider import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider with retry logic and error handling.
    
    This provider implements the BaseLLMProvider interface for OpenAI's API,
    including support for streaming, retries, timeouts, and error mapping.
    """
    
    API_BASE = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            **kwargs: Additional configuration
                - model: Default model to use
                - timeout: Request timeout in seconds
                - max_retries: Maximum number of retries
                - temperature: Default temperature
                - max_tokens: Default max tokens
        """
        super().__init__(api_key, **kwargs)
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = kwargs.get('model', self.DEFAULT_MODEL)
        self.timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self.max_retries = kwargs.get('max_retries', self.MAX_RETRIES)
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens_default = kwargs.get('max_tokens', 2000)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using OpenAI API.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
                - model: Override default model
                - temperature: Override default temperature
                - max_tokens: Override default max tokens
                - stream: Enable streaming (not yet implemented)
                
        Returns:
            Generated text string
            
        Raises:
            Exception: If generation fails after all retries
        """
        model = kwargs.get('model', self.model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens_default)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
                    f"{self.API_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                
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
                    raise Exception(f"OpenAI API server error: {response.status_code}")
                
                else:
                    # Client error - don't retry
                    error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"OpenAI API error: {error_detail}")
            
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
        """List available OpenAI models.
        
        Returns:
            List of model identifiers
            
        Raises:
            Exception: If API call fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(
                f"{self.API_BASE}/models",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                # Filter to chat models only
                models = [
                    model['id'] for model in data['data']
                    if 'gpt' in model['id'].lower()
                ]
                return sorted(models)
            
            elif response.status_code == 401:
                raise ValueError("Invalid API key")
            
            else:
                raise Exception(f"Failed to list models: {response.status_code}")
        
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.timeout}s")
        
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: {str(e)}")
    
    def validate_connection(self) -> bool:
        """Validate that the API key works.
        
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
        return "openai"

