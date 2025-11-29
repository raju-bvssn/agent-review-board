"""HuggingFace Inference API provider implementation."""

import time
from typing import List, Optional, Dict, Any
import requests
from app.llm.base_provider import BaseLLMProvider


class HuggingFaceProvider(BaseLLMProvider):
    """HuggingFace Inference API provider with free model support.
    
    This provider uses the HuggingFace Inference API which offers free access
    to many models. Some models are free, others require Pro subscription.
    
    FREE MODELS:
    - tiiuae/falcon-7b-instruct (text generation)
    - sentence-transformers/all-MiniLM-L6-v2 (embeddings)
    """
    
    API_BASE = "https://api-inference.huggingface.co/models"
    DEFAULT_MODEL = "tiiuae/falcon-7b-instruct"  # FREE
    DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # FREE
    DEFAULT_TIMEOUT = 60  # HF can be slow on free tier
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # Free and stable models
    FREE_MODELS = [
        "tiiuae/falcon-7b-instruct",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "google/flan-t5-xxl",
        "bigscience/bloom-7b1",
    ]
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize HuggingFace provider.
        
        Args:
            api_key: HuggingFace API token
            **kwargs: Additional configuration
                - model: Default model to use
                - timeout: Request timeout in seconds
                - max_retries: Maximum number of retries
                - temperature: Default temperature
                - max_tokens: Default max tokens (called max_new_tokens in HF)
        
        Raises:
            ValueError: If API key is missing
        """
        super().__init__(api_key, **kwargs)
        
        if not api_key:
            raise ValueError("HuggingFace API key is required")
        
        self.model = kwargs.get('model', self.DEFAULT_MODEL)
        self.timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self.max_retries = kwargs.get('max_retries', self.MAX_RETRIES)
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_new_tokens = kwargs.get('max_tokens', 500)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using HuggingFace API.
        
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
        max_tokens = kwargs.get('max_tokens', self.max_new_tokens)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False
            }
        }
        
        url = f"{self.API_BASE}/{model}"
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list) and len(data) > 0:
                        if 'generated_text' in data[0]:
                            return data[0]['generated_text'].strip()
                        elif 'text' in data[0]:
                            return data[0]['text'].strip()
                    elif isinstance(data, dict):
                        if 'generated_text' in data:
                            return data['generated_text'].strip()
                    
                    # Fallback
                    return str(data).strip()
                
                elif response.status_code == 503:
                    # Model loading - wait and retry
                    error_data = response.json()
                    if 'estimated_time' in error_data:
                        wait_time = min(error_data['estimated_time'], 20)
                    else:
                        wait_time = self.RETRY_DELAY * (2 ** attempt)
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    raise Exception("Model is loading, please try again in a moment")
                
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = self.RETRY_DELAY * (2 ** attempt)
                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    raise Exception("Rate limit exceeded for HuggingFace API")
                
                elif response.status_code == 401:
                    raise ValueError("Invalid HuggingFace API key")
                
                else:
                    error_msg = response.json().get('error', 'Unknown error')
                    raise Exception(f"HuggingFace API error: {error_msg}")
            
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
            
            except ValueError:
                # Don't retry on auth errors
                raise
            
            except Exception as e:
                last_exception = e
                # Don't retry on unexpected exceptions
                break
        
        raise last_exception or Exception("Failed to generate text")
    
    def list_models(self) -> List[str]:
        """List available HuggingFace models.
        
        Returns:
            List of free and recommended model identifiers
        """
        # Return curated list of free, stable models
        return self.FREE_MODELS
    
    def validate_connection(self) -> bool:
        """Validate that the API key works.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Make a minimal request to validate the key
            result = self.generate_text(
                "Say OK",
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
        return "huggingface"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using HuggingFace models.
        
        HuggingFace doesn't have a native chat API, so we convert
        messages to a prompt format.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Generated response string
        """
        # Convert messages to prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        prompt = "\n".join(prompt_parts)
        
        return self.generate_text(prompt, **kwargs)
    
    def embed(self, text: str, **kwargs) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Text to embed
            **kwargs: Additional parameters
                - model: Embedding model to use
            
        Returns:
            List of embedding values
        """
        model = kwargs.get('model', self.DEFAULT_EMBEDDING_MODEL)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": text
        }
        
        url = f"{self.API_BASE}/{model}"
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"HuggingFace embedding failed: {response.status_code}")
        
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {str(e)}")

