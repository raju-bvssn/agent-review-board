"""Salesforce Agentforce LLM provider implementation."""

import time
import json
from typing import List, Optional, Dict, Any
from app.llm.base_provider import BaseLLMProvider

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class AgentforceProvider(BaseLLMProvider):
    """Salesforce Agentforce API provider.
    
    This provider implements the BaseLLMProvider interface for Salesforce Agentforce,
    supporting multiple authentication methods (OAuth JWT, OAuth Password, Session ID).
    
    The Agentforce Agent ID acts as the "model" in ARB's provider system.
    """
    
    # Default configuration
    DEFAULT_TIMEOUT = 60  # Agentforce may take longer than typical LLMs
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # Supported authentication types
    AUTH_TYPES = ["oauth_jwt", "oauth_password", "session_id"]
    
    # Salesforce API version for Agentforce
    API_VERSION = "v61.0"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Agentforce provider.
        
        Args:
            api_key: Not used for Agentforce (auth via other methods)
            **kwargs: Configuration parameters
                - agent_id: Agentforce Agent ID (e.g., "0XxdM0000029q33SAA")
                - instance_url: Salesforce instance URL (e.g., "https://yourorg.salesforce.com")
                - auth_type: Authentication method ("oauth_jwt", "oauth_password", "session_id")
                
                For oauth_jwt:
                - client_id: Connected App Consumer Key
                - private_key: Private key in PEM format (string)
                - username: Salesforce username
                
                For oauth_password:
                - client_id: Connected App Consumer Key
                - client_secret: Connected App Consumer Secret
                - username: Salesforce username
                - password: Salesforce password (may include security token)
                
                For session_id:
                - session_id: Valid Salesforce session ID
                
                Optional:
                - timeout: Request timeout in seconds (default: 60)
                - max_retries: Maximum number of retries (default: 3)
        
        Raises:
            ValueError: If required configuration is missing
            ImportError: If httpx is not installed
        """
        super().__init__(api_key, **kwargs)
        
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx package not installed. "
                "Install with: pip install httpx"
            )
        
        # Required configuration
        self.agent_id = kwargs.get('agent_id')
        self.instance_url = kwargs.get('instance_url', '').rstrip('/')
        self.auth_type = kwargs.get('auth_type', 'oauth_jwt')
        
        if not self.agent_id:
            raise ValueError("agent_id is required for Agentforce provider")
        
        if not self.instance_url:
            raise ValueError("instance_url is required for Agentforce provider")
        
        if self.auth_type not in self.AUTH_TYPES:
            raise ValueError(
                f"auth_type must be one of {self.AUTH_TYPES}, got: {self.auth_type}"
            )
        
        # Auth-specific configuration
        self.client_id = kwargs.get('client_id')
        self.client_secret = kwargs.get('client_secret')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.private_key = kwargs.get('private_key')
        self.session_id = kwargs.get('session_id')
        self.system_prompt = kwargs.get('system_prompt') or ""
        
        # Validate auth-specific requirements
        if self.auth_type == 'oauth_jwt':
            if not all([self.client_id, self.private_key, self.username]):
                raise ValueError(
                    "oauth_jwt requires: client_id, private_key, username"
                )
        elif self.auth_type == 'oauth_password':
            if not all([self.client_id, self.client_secret, self.username, self.password]):
                raise ValueError(
                    "oauth_password requires: client_id, client_secret, username, password"
                )
        elif self.auth_type == 'session_id':
            if not self.session_id:
                raise ValueError("session_id auth requires: session_id")
        
        # Optional configuration
        self.timeout = kwargs.get('timeout', self.DEFAULT_TIMEOUT)
        self.max_retries = kwargs.get('max_retries', self.MAX_RETRIES)
        
        # Initialize HTTP client
        self.client = httpx.Client(timeout=self.timeout)
        
        # Cache for access token
        self._access_token = None
        self._token_expiry = 0
    
    def _get_access_token(self) -> str:
        """Get or refresh Salesforce access token.
        
        Returns:
            Valid access token string
            
        Raises:
            Exception: If authentication fails
        """
        # Check if cached token is still valid
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token
        
        # Authenticate based on auth_type
        if self.auth_type == 'session_id':
            # Direct session ID - no OAuth needed
            return self.session_id
        
        elif self.auth_type == 'oauth_jwt':
            return self._authenticate_jwt()
        
        elif self.auth_type == 'oauth_password':
            return self._authenticate_password()
        
        raise ValueError(f"Unsupported auth_type: {self.auth_type}")
    
    def _authenticate_jwt(self) -> str:
        """Authenticate using OAuth 2.0 JWT Bearer Flow.
        
        Returns:
            Access token string
            
        Raises:
            Exception: If authentication fails
        """
        # TODO: Implement JWT Bearer Flow authentication
        # Reference: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm
        #
        # Steps:
        # 1. Create JWT assertion with:
        #    - iss: client_id
        #    - sub: username
        #    - aud: instance_url or https://login.salesforce.com
        #    - exp: current time + 3 minutes
        # 2. Sign JWT with private_key (RS256)
        # 3. POST to {instance_url}/services/oauth2/token with:
        #    - grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
        #    - assertion={jwt_token}
        # 4. Extract access_token from response
        # 5. Cache token (expires in ~2 hours typically)
        #
        # Required package: pip install pyjwt cryptography
        
        raise NotImplementedError(
            "TODO: JWT authentication not yet implemented. "
            "Need to create and sign JWT assertion, then exchange for access token. "
            "See: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm"
        )
    
    def _authenticate_password(self) -> str:
        """Authenticate using OAuth 2.0 Username-Password Flow.
        
        Returns:
            Access token string
            
        Raises:
            Exception: If authentication fails
        """
        # TODO: Implement Username-Password Flow authentication
        # Reference: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_username_password_flow.htm
        #
        # Steps:
        # 1. POST to {instance_url}/services/oauth2/token with:
        #    - grant_type=password
        #    - client_id={client_id}
        #    - client_secret={client_secret}
        #    - username={username}
        #    - password={password}{security_token}  # Note: password may include security token
        # 2. Extract access_token from response
        # 3. Cache token with expiry
        
        token_url = f"{self.instance_url}/services/oauth2/token"
        
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }
        
        try:
            response = self.client.post(
                token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(
                    f"Salesforce OAuth authentication failed (Status {response.status_code}): {error_detail}"
                )
            
            response_data = response.json()
            access_token = response_data.get('access_token')
            
            if not access_token:
                raise Exception("No access_token in OAuth response")
            
            # Cache token (Salesforce tokens typically expire in 2 hours)
            # We'll cache for 1.5 hours to be safe
            self._access_token = access_token
            self._token_expiry = time.time() + (90 * 60)  # 90 minutes
            
            return access_token
        
        except Exception as e:
            raise Exception(f"Salesforce authentication failed: {str(e)}")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Salesforce Agentforce.
        
        Args:
            prompt: The input prompt for the agent
            **kwargs: Additional parameters (currently unused)
                - temperature: Not directly supported by Agentforce (ignored)
                - max_tokens: Not directly supported by Agentforce (ignored)
                
        Returns:
            Generated text string from Agentforce agent (or error message on failure)
        """
        
        # Get access token (prefer session_id, fallback to OAuth)
        try:
            access_token = self.session_id if self.session_id else self._get_access_token()
        except Exception as e:
            return (
                f"[Agentforce Authentication Error]\n"
                f"Failed to get access token: {str(e)}\n"
                f"→ Falling back to placeholder mode."
            )
        
        # Build dynamic endpoint
        instance_url = self.instance_url.rstrip("/")
        endpoint = f"{instance_url}/services/data/{self.API_VERSION}/agentforce/agents/{self.agent_id}/execute"
        
        # Build request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "text": prompt,
                "context": self.system_prompt  # NOTE: Some agents use "instructions" instead of "context"
            }
        }
        # NOTE: If the agent ignores context, switch the key to: "instructions": self.system_prompt
        
        # Debug logging
        print(f"[Agentforce] Calling agent {self.agent_id} at {endpoint}")
        
        # Retry logic
        last_exception = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.post(endpoint, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse standard Salesforce response format
                    if "output" in data and "text" in data["output"]:
                        result_text = data["output"]["text"]
                        print(f"[Agentforce] Received {len(result_text)} chars")
                        return result_text
                    else:
                        return (
                            f"[Agentforce Warning] Unexpected response format:\n"
                            f"{json.dumps(data, indent=2)}"
                        )
                
                else:
                    error_text = response.text
                    last_exception = Exception(f"HTTP {response.status_code}: {error_text}")
                    
                    # Retry on server errors (500+)
                    if response.status_code >= 500:
                        if attempt < self.MAX_RETRIES - 1:
                            wait_time = self.RETRY_DELAY * (2 ** attempt)
                            print(f"[Agentforce] Server error, retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    
                    # Don't retry on client errors (401, 403, 404)
                    break
            
            except Exception as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    print(f"[Agentforce] Error, retrying...")
                    time.sleep(self.RETRY_DELAY)
                    continue
                break
        
        # All retries failed - return error as text (don't raise)
        return (
            f"[Agentforce API Error]\n"
            f"Endpoint: {endpoint}\n"
            f"Error: {str(last_exception)}\n\n"
            f"→ Falling back to placeholder output.\n"
            f"Prompt sent: {prompt[:200]}..."
        )
    
    def list_models(self) -> List[str]:
        """List available Agentforce agents.
        
        In ARB's provider system, the Agentforce Agent ID acts as the "model".
        This returns the configured agent ID.
        
        Returns:
            List containing the configured agent ID
        """
        return [self.agent_id]
    
    def validate_connection(self) -> bool:
        """Validate that Agentforce connection works.
        
        Returns:
            True if authentication succeeds, False otherwise
        """
        try:
            # Try to get an access token
            access_token = self._get_access_token()
            
            # If we get here, authentication worked
            print(f"[Agentforce] Connection validated successfully")
            return True
        
        except NotImplementedError:
            # JWT auth not implemented yet - return True for placeholder
            print(f"[Agentforce] Connection validation: Auth method not implemented (placeholder mode)")
            return True
        
        except Exception as e:
            print(f"[Agentforce] Connection validation failed: {str(e)}")
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of this provider.
        
        Returns:
            Provider name string
        """
        return "agentforce"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using Agentforce.
        
        Agentforce doesn't have a separate chat mode, so we convert
        the messages to a single prompt and call generate_text.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Generated response string
        """
        # Extract system message if present
        system_messages = [m['content'] for m in messages if m.get('role') == 'system']
        system_prompt = system_messages[0] if system_messages else None
        
        # Get user messages
        user_messages = [m['content'] for m in messages if m.get('role') == 'user']
        prompt = user_messages[-1] if user_messages else ""
        
        # Add assistant context if present
        assistant_messages = [m['content'] for m in messages if m.get('role') == 'assistant']
        if assistant_messages:
            # Include conversation history in prompt
            conversation = "\n\n".join([
                f"User: {user_messages[i]}\nAssistant: {assistant_messages[i]}"
                for i in range(min(len(user_messages) - 1, len(assistant_messages)))
            ])
            prompt = f"{conversation}\n\nUser: {prompt}"
        
        return self.generate_text(
            prompt,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def embed(self, text: str, **kwargs) -> List[float]:
        """Generate embeddings for text.
        
        Agentforce may not support embeddings directly.
        This is a placeholder that raises NotImplementedError.
        
        Args:
            text: Text to embed
            **kwargs: Additional parameters
            
        Returns:
            List of embedding values
            
        Raises:
            NotImplementedError: Agentforce embeddings not supported
        """
        raise NotImplementedError(
            "Agentforce does not currently support text embeddings. "
            "Use a different provider (OpenAI, Gemini, etc.) for embedding operations."
        )

