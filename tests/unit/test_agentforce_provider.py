"""Unit tests for Agentforce provider."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestAgentforceProvider:
    """Test suite for AgentforceProvider."""
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_provider_initialization_oauth_password(self, mock_client_class):
        """Test provider initialization with OAuth password flow."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_password",
            client_id="test-client-id",
            client_secret="test-client-secret",
            username="user@test.com",
            password="password123"
        )
        
        assert provider.agent_id == "0XxdM0000029q33SAA"
        assert provider.instance_url == "https://test.salesforce.com"
        assert provider.auth_type == "oauth_password"
        assert provider.client_id == "test-client-id"
        mock_client_class.assert_called_once()
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_provider_initialization_session_id(self, mock_client_class):
        """Test provider initialization with session ID."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="session_id",
            session_id="test-session-id-12345"
        )
        
        assert provider.agent_id == "0XxdM0000029q33SAA"
        assert provider.auth_type == "session_id"
        assert provider.session_id == "test-session-id-12345"
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_provider_initialization_oauth_jwt(self, mock_client_class):
        """Test provider initialization with OAuth JWT flow."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_jwt",
            client_id="test-client-id",
            username="user@test.com",
            private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
        )
        
        assert provider.agent_id == "0XxdM0000029q33SAA"
        assert provider.auth_type == "oauth_jwt"
        assert provider.private_key is not None
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_missing_agent_id(self, mock_client_class):
        """Test that missing agent_id raises error."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        with pytest.raises(ValueError, match="agent_id is required"):
            AgentforceProvider(
                instance_url="https://test.salesforce.com",
                auth_type="session_id",
                session_id="test-session"
            )
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_missing_instance_url(self, mock_client_class):
        """Test that missing instance_url raises error."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        with pytest.raises(ValueError, match="instance_url is required"):
            AgentforceProvider(
                agent_id="0XxdM0000029q33SAA",
                auth_type="session_id",
                session_id="test-session"
            )
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_invalid_auth_type(self, mock_client_class):
        """Test that invalid auth_type raises error."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        with pytest.raises(ValueError, match="auth_type must be one of"):
            AgentforceProvider(
                agent_id="0XxdM0000029q33SAA",
                instance_url="https://test.salesforce.com",
                auth_type="invalid_auth"
            )
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_oauth_password_missing_credentials(self, mock_client_class):
        """Test that OAuth password flow requires all credentials."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        with pytest.raises(ValueError, match="oauth_password requires"):
            AgentforceProvider(
                agent_id="0XxdM0000029q33SAA",
                instance_url="https://test.salesforce.com",
                auth_type="oauth_password",
                client_id="test-client"
                # Missing client_secret, username, password
            )
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_oauth_jwt_missing_credentials(self, mock_client_class):
        """Test that OAuth JWT flow requires all credentials."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        with pytest.raises(ValueError, match="oauth_jwt requires"):
            AgentforceProvider(
                agent_id="0XxdM0000029q33SAA",
                instance_url="https://test.salesforce.com",
                auth_type="oauth_jwt",
                client_id="test-client"
                # Missing private_key, username
            )
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_session_id_missing_session(self, mock_client_class):
        """Test that session_id auth requires session_id."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        with pytest.raises(ValueError, match="session_id auth requires: session_id"):
            AgentforceProvider(
                agent_id="0XxdM0000029q33SAA",
                instance_url="https://test.salesforce.com",
                auth_type="session_id"
                # Missing session_id
            )
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', False)
    def test_missing_httpx_package(self):
        """Test error when httpx is not installed."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        with pytest.raises(ImportError, match="httpx package not installed"):
            AgentforceProvider(
                agent_id="0XxdM0000029q33SAA",
                instance_url="https://test.salesforce.com",
                auth_type="session_id",
                session_id="test-session"
            )
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_list_models(self, mock_client_class):
        """Test listing available agents (models)."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="session_id",
            session_id="test-session"
        )
        
        models = provider.list_models()
        
        assert isinstance(models, list)
        assert len(models) == 1
        assert models[0] == "0XxdM0000029q33SAA"
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_generate_text_with_session_id(self, mock_client_class):
        """Test text generation with session ID auth."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful Agentforce response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": "Real agent response from Salesforce"
            }
        }
        mock_client.post.return_value = mock_response
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="session_id",
            session_id="test-session-id"
        )
        
        result = provider.generate_text("test prompt")
        
        # Should return the actual response text
        assert result == "Real agent response from Salesforce"
        
        # Verify the API call was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        
        # Verify endpoint (should NOT include /actions)
        assert "/execute" in call_args[0][0]
        assert "/actions/execute" not in call_args[0][0]
        
        # Verify payload structure
        payload = call_args[1]['json']
        assert 'input' in payload
        assert 'text' in payload['input']
        assert payload['input']['text'] == "test prompt"
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_generate_text_with_oauth_password_success(self, mock_client_class):
        """Test text generation with OAuth password flow."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        # Mock successful OAuth token response
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "test-access-token-12345",
            "instance_url": "https://test.salesforce.com",
            "id": "https://login.salesforce.com/id/test",
            "token_type": "Bearer"
        }
        
        # Mock successful Agentforce API response
        mock_api_response = Mock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = {
            "output": {
                "text": "OAuth authenticated agent response"
            }
        }
        
        mock_client = Mock()
        # First call is OAuth, second call is Agentforce API
        mock_client.post.side_effect = [mock_token_response, mock_api_response]
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_password",
            client_id="test-client-id",
            client_secret="test-secret",
            username="user@test.com",
            password="password123"
        )
        
        result = provider.generate_text("test prompt")
        
        # Should get the actual response
        assert result == "OAuth authenticated agent response"
        
        # Verify both calls were made
        assert mock_client.post.call_count == 2
        
        # First call should be OAuth token
        first_call = mock_client.post.call_args_list[0]
        assert "/services/oauth2/token" in first_call[0][0]
        
        # Second call should be Agentforce API
        second_call = mock_client.post.call_args_list[1]
        assert "/execute" in second_call[0][0]
        assert "/actions/execute" not in second_call[0][0]
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_generate_text_oauth_failure(self, mock_client_class):
        """Test OAuth authentication failure handling."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        # Mock failed OAuth response
        mock_token_response = Mock()
        mock_token_response.status_code = 401
        mock_token_response.text = "Invalid credentials"
        
        mock_client = Mock()
        mock_client.post.return_value = mock_token_response
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_password",
            client_id="test-client-id",
            client_secret="test-secret",
            username="user@test.com",
            password="wrong-password"
        )
        
        # Should return error message, not raise exception
        result = provider.generate_text("test prompt")
        
        assert "[Agentforce Authentication Error]" in result
        assert "Failed to get access token" in result
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_validate_connection_session_id(self, mock_client_class):
        """Test connection validation with session ID."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="session_id",
            session_id="test-session"
        )
        
        is_valid = provider.validate_connection()
        
        # Placeholder mode - should return True
        assert is_valid is True
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_validate_connection_oauth_password_success(self, mock_client_class):
        """Test connection validation with OAuth password flow."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        # Mock successful OAuth token response
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "test-token",
            "instance_url": "https://test.salesforce.com"
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_token_response
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_password",
            client_id="test-client",
            client_secret="test-secret",
            username="user@test.com",
            password="password123"
        )
        
        is_valid = provider.validate_connection()
        
        assert is_valid is True
        mock_client.post.assert_called_once()
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_validate_connection_oauth_failure(self, mock_client_class):
        """Test connection validation with OAuth failure."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        # Mock failed OAuth response
        mock_token_response = Mock()
        mock_token_response.status_code = 401
        mock_token_response.text = "Invalid credentials"
        
        mock_client = Mock()
        mock_client.post.return_value = mock_token_response
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_password",
            client_id="test-client",
            client_secret="wrong-secret",
            username="user@test.com",
            password="wrong-password"
        )
        
        is_valid = provider.validate_connection()
        
        assert is_valid is False
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_validate_connection_oauth_jwt_not_implemented(self, mock_client_class):
        """Test that JWT auth returns True in placeholder mode."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_jwt",
            client_id="test-client",
            username="user@test.com",
            private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----"
        )
        
        # JWT not implemented yet - should return True for placeholder
        is_valid = provider.validate_connection()
        assert is_valid is True
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_get_provider_name(self, mock_client_class):
        """Test get_provider_name returns 'agentforce'."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="session_id",
            session_id="test-session"
        )
        
        assert provider.get_provider_name() == "agentforce"
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_chat_method(self, mock_client_class):
        """Test chat method converts messages to prompt."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        # Mock successful Agentforce response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": "I'm doing well, thank you!"
            }
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="session_id",
            session_id="test-session"
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = provider.chat(messages)
        
        # Should return the actual response
        assert result == "I'm doing well, thank you!"
        
        # Verify API was called
        mock_client.post.assert_called_once()
        
        # Verify the prompt includes conversation context
        call_args = mock_client.post.call_args
        payload = call_args[1]['json']
        assert 'input' in payload
        assert 'text' in payload['input']
        # The prompt should include the latest user message
        assert "How are you?" in payload['input']['text']
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_embed_not_supported(self, mock_client_class):
        """Test that embed method raises NotImplementedError."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="session_id",
            session_id="test-session"
        )
        
        with pytest.raises(NotImplementedError, match="does not currently support text embeddings"):
            provider.embed("test text")
    
    @patch('app.llm.agentforce_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_token_caching(self, mock_client_class):
        """Test that OAuth tokens are cached and reused."""
        from app.llm.agentforce_provider import AgentforceProvider
        
        # Mock successful OAuth token response
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "test-token-12345",
            "instance_url": "https://test.salesforce.com"
        }
        
        # Mock successful Agentforce API response
        mock_api_response = Mock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = {
            "output": {
                "text": "Agent response"
            }
        }
        
        mock_client = Mock()
        # Set up responses: OAuth, API, API (second call reuses token)
        mock_client.post.side_effect = [
            mock_token_response,  # First OAuth call
            mock_api_response,     # First Agentforce API call
            mock_api_response      # Second Agentforce API call (token cached)
        ]
        mock_client_class.return_value = mock_client
        
        provider = AgentforceProvider(
            agent_id="0XxdM0000029q33SAA",
            instance_url="https://test.salesforce.com",
            auth_type="oauth_password",
            client_id="test-client",
            client_secret="test-secret",
            username="user@test.com",
            password="password123"
        )
        
        # First call should: authenticate + call API = 2 calls
        provider.generate_text("prompt 1")
        assert mock_client.post.call_count == 2
        
        # Verify first call was OAuth
        first_call = mock_client.post.call_args_list[0]
        assert "/services/oauth2/token" in first_call[0][0]
        
        # Second call should use cached token: only API call = 1 more call (total 3)
        provider.generate_text("prompt 2")
        assert mock_client.post.call_count == 3
        
        # Verify no additional OAuth calls (token was cached)
        oauth_calls = [call for call in mock_client.post.call_args_list 
                       if "/services/oauth2/token" in call[0][0]]
        assert len(oauth_calls) == 1  # Only the first call

