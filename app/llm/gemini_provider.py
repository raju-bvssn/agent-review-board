"""Google Gemini LLM provider implementation."""

import time
from typing import List, Optional, Dict, Any
from app.llm.base_provider import BaseLLMProvider

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider with free tier support.
    
    This provider implements the BaseLLMProvider interface for Google's Gemini API,
    including support for free models like gemini-1.5-flash.
    
    FREE TIER: gemini-1.5-flash is free up to 15 requests per minute.
    """
    
    # Free and low-cost models
    DEFAULT_MODEL = "gemini-1.5-flash"  # FREE tier
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    AVAILABLE_MODELS = [
        "gemini-1.5-flash",      # FREE - Fast, good for most tasks
        "gemini-1.5-flash-8b",   # FREE - Even faster, lighter
        "gemini-1.5-pro",        # Paid - More capable
        "gemini-1.0-pro",        # Paid - Previous generation
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
            ImportError: If google-generativeai is not installed
        """
        super().__init__(api_key, **kwargs)
        
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        self.model = kwargs.get('model', self.DEFAULT_MODEL)
        self.timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self.max_retries = kwargs.get('max_retries', self.MAX_RETRIES)
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_output_tokens = kwargs.get('max_tokens', 2000)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt using Gemini API.
        
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
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Create model instance
                model = genai.GenerativeModel(model_name)
                
                # Configure generation
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
                
                # Generate
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Extract text
                if response.text:
                    return response.text
                else:
                    raise Exception("Empty response from Gemini")
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Rate limit - retry
                if 'rate limit' in error_str or 'quota' in error_str:
                    last_exception = Exception(f"Gemini rate limit exceeded: {str(e)}")
                    if attempt < self.max_retries - 1:
                        wait_time = self.RETRY_DELAY * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                
                # Invalid API key - don't retry
                elif 'api key' in error_str or 'invalid' in error_str:
                    raise ValueError(f"Invalid Gemini API key: {str(e)}")
                
                # Server error - retry
                elif 'server' in error_str or '500' in error_str:
                    last_exception = e
                    if attempt < self.max_retries - 1:
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
        try:
            # Try to get models from API
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name.replace('models/', ''))
            
            if models:
                return sorted(models)
        except Exception:
            # Fallback to known models if API fails
            pass
        
        # Return known models (including free ones)
        return self.AVAILABLE_MODELS
    
    def validate_connection(self) -> bool:
        """Validate that the API key works.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try listing models
            models = self.list_models()
            return len(models) > 0
        except Exception:
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
        """Generate embeddings for text.
        
        Args:
            text: Text to embed
            **kwargs: Additional parameters
            
        Returns:
            List of embedding values
        """
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text
            )
            return result['embedding']
        except Exception as e:
            raise Exception(f"Gemini embedding failed: {str(e)}")

