"""Ollama local LLM provider implementation."""

import time
from typing import List, Optional, Dict, Any
import requests
from app.llm.base_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider - completely free and runs locally.
    
    Ollama is a local LLM runtime that runs models on your machine.
    No API key required, completely free, and private.
    
    INSTALLATION:
    1. Download from https://ollama.com/download
    2. Install and start Ollama
    3. Pull models: ollama pull llama3
    
    FREE LOCAL MODELS:
    - llama3 (8B and 70B)
    - mistral (7B)
    - phi3 (3.8B)
    - codellama (7B, 13B, 34B)
    - qwen2.5 (various sizes)
    """
    
    API_BASE = "http://localhost:11434/api"
    DEFAULT_MODEL = "llama3"  # FREE local model
    DEFAULT_TIMEOUT = 60  # Local can be slow on CPU
    MAX_RETRIES = 2  # Fewer retries for local
    
    # Known free local models
    KNOWN_MODELS = [
        "llama3",
        "llama3:70b",
        "mistral",
        "mistral:7b",
        "phi3",
        "phi3:medium",
        "codellama",
        "codellama:13b",
        "qwen2.5",
        "qwen2.5:7b",
        "gemma2",
        "neural-chat",
    ]
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Ollama provider.
        
        Args:
            api_key: Not required for Ollama (local)
            **kwargs: Additional configuration
                - base_url: Ollama API URL (default: http://localhost:11434/api)
                - model: Default model to use
                - timeout: Request timeout in seconds
                - temperature: Default temperature
                - max_tokens: Default max tokens (called num_predict in Ollama)
        """
        super().__init__(api_key, **kwargs)
        
        # Ollama doesn't need API key
        self.api_base = kwargs.get('base_url', self.API_BASE)
        self.model = kwargs.get('model', self.DEFAULT_MODEL)
        self.timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self.temperature = kwargs.get('temperature', 0.7)
        self.num_predict = kwargs.get('max_tokens', 500)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using Ollama.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
                - model: Override default model
                - temperature: Override default temperature
                - max_tokens: Override default max tokens
                - stream: Enable streaming (default: False)
                
        Returns:
            Generated text string
            
        Raises:
            Exception: If generation fails or Ollama is not running
        """
        model = kwargs.get('model', self.model)
        temperature = kwargs.get('temperature', self.temperature)
        num_predict = kwargs.get('max_tokens', self.num_predict)
        stream = kwargs.get('stream', False)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        }
        
        url = f"{self.api_base}/generate"
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '').strip()
            
            elif response.status_code == 404:
                raise Exception(
                    f"Model '{model}' not found. "
                    f"Pull it first: ollama pull {model}"
                )
            
            else:
                error_msg = response.json().get('error', 'Unknown error')
                raise Exception(f"Ollama API error: {error_msg}")
        
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Cannot connect to Ollama. "
                "Make sure Ollama is installed and running. "
                "Download from: https://ollama.com/download"
            )
        
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.timeout}s")
    
    def list_models(self) -> List[str]:
        """List available Ollama models.
        
        Returns:
            List of model identifiers (from local Ollama or fallback list)
        """
        url = f"{self.api_base}/tags"
        
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                
                if models:
                    return sorted(models)
        
        except requests.exceptions.ConnectionError:
            # Ollama not running - return known models
            pass
        
        except Exception:
            # Any other error - return known models
            pass
        
        # Fallback to known models
        return self.KNOWN_MODELS
    
    def validate_connection(self) -> bool:
        """Validate that Ollama is running and accessible.
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        url = f"{self.api_base}/tags"
        
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of this provider.
        
        Returns:
            Provider name string
        """
        return "ollama"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Generated response string
        """
        model = kwargs.get('model', self.model)
        
        url = f"{self.api_base}/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('message', {}).get('content', '').strip()
            else:
                # Fallback to generate with formatted prompt
                prompt = self._messages_to_prompt(messages)
                return self.generate_text(prompt, **kwargs)
        
        except Exception:
            # Fallback to generate
            prompt = self._messages_to_prompt(messages)
            return self.generate_text(prompt, **kwargs)
    
    def embed(self, text: str, **kwargs) -> List[float]:
        """Generate embeddings for text using Ollama.
        
        Args:
            text: Text to embed
            **kwargs: Additional parameters
                - model: Embedding model (default: nomic-embed-text)
            
        Returns:
            List of embedding values
        """
        model = kwargs.get('model', 'nomic-embed-text')
        
        url = f"{self.api_base}/embeddings"
        
        payload = {
            "model": model,
            "prompt": text
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('embedding', [])
            else:
                raise Exception(f"Ollama embedding failed: {response.status_code}")
        
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt string.
        
        Args:
            messages: List of message dicts
            
        Returns:
            Formatted prompt string
        """
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
        return "\n".join(prompt_parts)
    
    def is_running(self) -> bool:
        """Check if Ollama service is running.
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        return self.validate_connection()
    
    def get_ollama_version(self) -> Optional[str]:
        """Get Ollama version if running.
        
        Returns:
            Version string or None
        """
        url = f"{self.api_base}/version"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json().get('version', 'unknown')
        except Exception:
            pass
        
        return None

