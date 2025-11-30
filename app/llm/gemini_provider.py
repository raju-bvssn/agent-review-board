"""Google Gemini LLM provider implementation."""

import time
import json
from typing import List, Optional, Dict, Any
from app.llm.base_provider import BaseLLMProvider

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import google.generativeai as genai
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider with free tier support.
    
    This provider implements the BaseLLMProvider interface for Google's Gemini API,
    including support for free models like gemini-1.5-flash.
    
    FREE TIER: gemini-1.5-flash is free up to 15 requests per minute.
    """
    
    # API Configuration
    API_BASE_URL = "https://generativelanguage.googleapis.com/v1"
    
    # Free and low-cost models
    DEFAULT_MODEL = "gemini-1.5-flash"  # FREE tier
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    AVAILABLE_MODELS = [
        "gemini-1.5-flash",      # FREE - Fast, good for most tasks
        "gemini-1.5-flash-8b",   # FREE - Even faster, lighter
        "gemini-1.5-pro",        # Paid - More capable
        "gemini-pro",            # Standard model
    ]
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Gemini provider.
        
        Args:
            api_key: Google AI Studio API key
            **kwargs: Additional configuration
                - model: Default model to use
                - timeout: Request timeout in seconds
                - max_retries: Maximum number of retries
                - temperature: Default temperature
                - max_tokens: Default max tokens (called max_output_tokens in Gemini)
        
        Raises:
            ValueError: If API key is missing
            ImportError: If httpx is not installed
        """
        super().__init__(api_key, **kwargs)
        
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx package not installed. "
                "Install with: pip install httpx"
            )
        
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        self.api_key = api_key
        self.model = kwargs.get('model', self.DEFAULT_MODEL)
        self.timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self.max_retries = kwargs.get('max_retries', self.MAX_RETRIES)
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_output_tokens = kwargs.get('max_tokens', 2000)
        
        # Initialize HTTP client
        self.client = httpx.Client(timeout=self.timeout)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using Gemini REST API v1.
        
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
        model_name = kwargs.get('model', self.model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_output_tokens)
        
        # Debug logging
        print(f"[Gemini] Using model: {model_name}")
        
        # Build API URL (v1 endpoint)
        url = f"{self.API_BASE_URL}/models/{model_name}:generateContent?key={self.api_key}"
        
        # Build request payload according to Google's v1 API schema
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Make POST request
                response = self.client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Handle HTTP errors
                if response.status_code == 404:
                    raise ValueError(
                        f"Model not supported for API v1. "
                        f"Try gemini-1.5-flash or gemini-1.5-pro. "
                        f"(Status: 404, Model: {model_name})"
                    )
                
                if response.status_code != 200:
                    error_detail = response.text
                    raise Exception(
                        f"Gemini API error (Status {response.status_code}): {error_detail}"
                    )
                
                # Parse response
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    raise Exception(
                        f"Invalid JSON response from Gemini API. "
                        f"Raw response: {response.text[:500]}"
                    )
                
                # Extract text from response
                try:
                    text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                    if text:
                        return text
                    else:
                        raise Exception("Empty text in Gemini response")
                
                except (KeyError, IndexError, TypeError) as e:
                    raise Exception(
                        f"Invalid response format from Gemini API. "
                        f"Expected structure: candidates[0].content.parts[0].text. "
                        f"Raw response: {json.dumps(response_data, indent=2)[:1000]}"
                    )
            
            except ValueError as e:
                # Don't retry for 404 or invalid model errors
                raise e
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Rate limit - retry
                if 'rate limit' in error_str or 'quota' in error_str or '429' in error_str:
                    last_exception = Exception(f"Gemini rate limit exceeded: {str(e)}")
                    if attempt < self.max_retries - 1:
                        wait_time = self.RETRY_DELAY * (2 ** attempt)
                        print(f"[Gemini] Rate limited, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Invalid API key - don't retry
                elif 'api key' in error_str or 'invalid' in error_str or '401' in error_str or '403' in error_str:
                    raise ValueError(f"Invalid Gemini API key: {str(e)}")
                
                # Server error - retry
                elif 'server' in error_str or '500' in error_str or '502' in error_str or '503' in error_str:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        print(f"[Gemini] Server error, retrying...")
                        time.sleep(self.RETRY_DELAY)
                        continue
                
                # Other error - don't retry
                else:
                    last_exception = e
                    break
        
        # All retries failed
        raise last_exception or Exception("Failed to generate text with Gemini")
    
    def list_models(self) -> List[str]:
        """List available Gemini models.
        
        Returns:
            List of model identifiers (includes free models)
        """
        # For v1 API, we use the known supported models
        # The models endpoint in v1 requires different permissions
        # So we return the known working models
        return self.AVAILABLE_MODELS.copy()
    
    def validate_connection(self) -> bool:
        """Validate that the API key works.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try a simple generation with minimal tokens
            test_prompt = "Hi"
            result = self.generate_text(test_prompt, max_tokens=10)
            return len(result) > 0
        except Exception as e:
            print(f"[Gemini] Connection validation failed: {str(e)}")
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of this provider.
        
        Returns:
            Provider name string
        """
        return "gemini"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using Gemini.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Generated response string
        """
        # Convert messages to Gemini format
        # For now, just use the last user message
        user_messages = [m['content'] for m in messages if m.get('role') == 'user']
        prompt = user_messages[-1] if user_messages else ""
        
        return self.generate_text(prompt, **kwargs)
    
    def embed(self, text: str, **kwargs) -> List[float]:
        """Generate embeddings for text using Gemini REST API v1.
        
        Args:
            text: Text to embed
            **kwargs: Additional parameters
            
        Returns:
            List of embedding values
        """
        try:
            # Use embedding model
            embedding_model = "text-embedding-004"
            url = f"{self.API_BASE_URL}/models/{embedding_model}:embedContent?key={self.api_key}"
            
            payload = {
                "content": {
                    "parts": [
                        {"text": text}
                    ]
                }
            }
            
            response = self.client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Embedding API error (Status {response.status_code}): {response.text}")
            
            response_data = response.json()
            
            # Extract embedding values
            embedding = response_data.get("embedding", {}).get("values", [])
            
            if not embedding:
                raise Exception("No embedding values in response")
            
            return embedding
        
        except Exception as e:
            raise Exception(f"Gemini embedding failed: {str(e)}")

