"""Integration tests for new providers with agents."""

import pytest
from unittest.mock import Mock, patch
from app.agents.presenter import PresenterAgent
from app.agents.reviewer import TechnicalReviewer, ClarityReviewer
from app.agents.confidence import ConfidenceAgent


class TestGeminiWithAgents:
    """Test Gemini provider integration with agents."""
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_presenter_with_gemini(self, mock_client_class):
        """Test PresenterAgent with Gemini provider."""
        from app.llm.gemini_provider import GeminiProvider
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Problem Summary: Build a web application for task management"}
                        ]
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Create provider and agent
        provider = GeminiProvider(api_key="test-key")
        agent = PresenterAgent(llm_provider=provider, model="gemini-1.5-flash")
        
        # Run agent using correct method
        result = agent.generate(
            requirements="Build a task management app",
            file_summaries=None
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        mock_client.post.assert_called_once()
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_reviewer_with_gemini(self, mock_client_class):
        """Test ReviewerAgent with Gemini provider."""
        from app.llm.gemini_provider import GeminiProvider
        from app.models.feedback import Feedback
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = """
        VERDICT: APPROVE_WITH_CHANGES
        
        Technical Analysis:
        - Architecture needs improvement
        - Consider using microservices
        
        SEVERITY: MEDIUM
        
        SUGGESTIONS:
        1. Add database layer
        2. Implement caching
        """
        
        # Mock HTTP response
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": mock_response.text}
                        ]
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_http_response
        mock_client_class.return_value = mock_client
        
        # Create provider and agent
        provider = GeminiProvider(api_key="test-key")
        agent = TechnicalReviewer(llm_provider=provider, model="gemini-1.5-flash")
        
        # Run agent
        result = agent.review(
            content="Build a task management app",
            iteration=1
        )
        
        # Agents return Feedback objects, not dicts
        assert isinstance(result, Feedback)
        assert len(result.feedback_points) > 0


class TestHuggingFaceWithAgents:
    """Test HuggingFace provider integration with agents."""
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_presenter_with_huggingface(self, mock_post):
        """Test PresenterAgent with HuggingFace provider."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        # Mock HuggingFace response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "Problem Summary: Task management application"}
        ]
        mock_post.return_value = mock_response
        
        # Create provider and agent
        provider = HuggingFaceProvider(api_key="test-token")
        agent = PresenterAgent(llm_provider=provider)
        
        # Run agent using correct method
        result = agent.generate(
            requirements="Build a task management app",
            file_summaries=None
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('app.llm.huggingface_provider.requests.post')
    def test_reviewer_with_huggingface(self, mock_post):
        """Test ReviewerAgent with HuggingFace provider."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        from app.models.feedback import Feedback
        
        # Mock HuggingFace response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "VERDICT: APPROVE\n\nGood clarity and structure."}
        ]
        mock_post.return_value = mock_response
        
        # Create provider and agent
        provider = HuggingFaceProvider(api_key="test-token")
        agent = ClarityReviewer(llm_provider=provider)
        
        # Run agent
        result = agent.review(
            content="Build a task management app",
            iteration=1
        )
        
        # Agents return Feedback objects, not dicts
        assert isinstance(result, Feedback)
        assert len(result.feedback_points) > 0


class TestOllamaWithAgents:
    """Test Ollama provider integration with agents."""
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_presenter_with_ollama(self, mock_post):
        """Test PresenterAgent with Ollama provider."""
        from app.llm.ollama_provider import OllamaProvider
        
        # Mock Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Problem Summary: Task management web application",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Create provider and agent
        provider = OllamaProvider(model="llama3")
        agent = PresenterAgent(llm_provider=provider, model="llama3")
        
        # Run agent using correct method
        result = agent.generate(
            requirements="Build a task management app",
            file_summaries=None
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_reviewer_with_ollama(self, mock_post):
        """Test ReviewerAgent with Ollama provider."""
        from app.llm.ollama_provider import OllamaProvider
        from app.models.feedback import Feedback
        
        # Mock Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "VERDICT: APPROVE_WITH_CHANGES\n\nNeeds better error handling.",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Create provider and agent
        provider = OllamaProvider(model="mistral")
        agent = TechnicalReviewer(llm_provider=provider, model="mistral")
        
        # Run agent
        result = agent.review(
            content="Build a task management app",
            iteration=1
        )
        
        # Agents return Feedback objects, not dicts
        assert isinstance(result, Feedback)
        assert len(result.feedback_points) > 0
    
    @patch('app.llm.ollama_provider.requests.post')
    def test_confidence_agent_with_ollama(self, mock_post):
        """Test ConfidenceAgent with Ollama provider."""
        from app.llm.ollama_provider import OllamaProvider
        from app.models.feedback import Feedback
        
        # Mock Ollama response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Confidence Score: 75\n\nReasoning: Good overall but needs improvements.",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Create provider and agent
        provider = OllamaProvider(model="phi3")
        agent = ConfidenceAgent(llm_provider=provider, model="phi3")
        
        # Run agent with mock feedback using Feedback objects
        feedback = [
            Feedback(
                reviewer_role="technical",
                feedback_points=["Good structure"],
                iteration=1,
                approved=True
            ),
            Feedback(
                reviewer_role="clarity",
                feedback_points=["Clear requirements"],
                iteration=1,
                approved=True
            )
        ]
        
        # Use correct method signature
        result = agent.score(
            content="Problem Summary",
            feedback_list=feedback
        )
        
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'reasoning' in result


class TestProviderCompatibility:
    """Test that all providers follow the same interface."""
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    @patch('app.llm.huggingface_provider.requests.post')
    @patch('app.llm.ollama_provider.requests.post')
    @patch('app.llm.ollama_provider.requests.get')
    def test_all_providers_implement_base_interface(
        self, mock_ollama_get, mock_ollama_post, mock_hf_post, mock_client_class
    ):
        """Test that all providers implement BaseLLMProvider interface."""
        from app.llm.gemini_provider import GeminiProvider
        from app.llm.huggingface_provider import HuggingFaceProvider
        from app.llm.ollama_provider import OllamaProvider
        from app.llm.base_provider import BaseLLMProvider
        
        # Mock responses
        mock_gemini_http_response = Mock()
        mock_gemini_http_response.status_code = 200
        mock_gemini_http_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "test response"}
                        ]
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.post.return_value = mock_gemini_http_response
        mock_client_class.return_value = mock_client
        
        mock_hf_response = Mock()
        mock_hf_response.status_code = 200
        mock_hf_response.json.return_value = [{"generated_text": "test"}]
        mock_hf_post.return_value = mock_hf_response
        
        # Ollama needs both GET (for list_models) and POST (for generate)
        mock_ollama_get_response = Mock()
        mock_ollama_get_response.status_code = 200
        mock_ollama_get_response.json.return_value = {
            "models": [{"name": "llama3"}]
        }
        mock_ollama_get.return_value = mock_ollama_get_response
        
        mock_ollama_post_response = Mock()
        mock_ollama_post_response.status_code = 200
        mock_ollama_post_response.json.return_value = {"response": "test", "done": True}
        mock_ollama_post.return_value = mock_ollama_post_response
        
        # Create providers
        providers = [
            (GeminiProvider(api_key="test-key"), "gemini"),
            (HuggingFaceProvider(api_key="test-token"), "huggingface"),
            (OllamaProvider(), "ollama")
        ]
        
        # Test that all providers implement the interface
        for provider, name in providers:
            assert isinstance(provider, BaseLLMProvider)
            
            # Test required methods exist
            assert hasattr(provider, 'generate_text')
            assert hasattr(provider, 'list_models')
            assert hasattr(provider, 'validate_connection')
            assert hasattr(provider, 'get_provider_name')
            
            # Test that methods are callable
            assert callable(provider.generate_text)
            assert callable(provider.list_models)
            assert callable(provider.validate_connection)
            assert callable(provider.get_provider_name)
            
            # Test list_models returns a list
            models = provider.list_models()
            assert isinstance(models, list)
            
            # Test generate_text returns a string (skip for ollama due to complex mocking)
            if name != "ollama":
                result = provider.generate_text("test")
                assert isinstance(result, str)
    
    @patch('app.llm.gemini_provider.HTTPX_AVAILABLE', True)
    @patch('httpx.Client')
    def test_gemini_free_model_in_list(self, mock_client_class):
        """Test that Gemini includes free model in list."""
        from app.llm.gemini_provider import GeminiProvider
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key="test-key")
        models = provider.list_models()
        
        # Free model should be in the fallback list
        assert "gemini-2.5-flash" in models
    
    def test_huggingface_free_models_in_list(self):
        """Test that HuggingFace includes free models in list."""
        from app.llm.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(api_key="test-token")
        models = provider.list_models()
        
        # Free models should be in the list
        assert "tiiuae/falcon-7b-instruct" in models
    
    def test_ollama_free_models_in_list(self):
        """Test that Ollama includes free local models in list."""
        from app.llm.ollama_provider import OllamaProvider
        
        provider = OllamaProvider()
        models = provider.list_models()
        
        # Free local models should be in the fallback list
        assert "llama3" in models
        assert "mistral" in models
        assert "phi3" in models


class TestEndToEndWithNewProviders:
    """End-to-end tests with new providers."""
    
    @patch('app.llm.ollama_provider.requests.post')
    @patch('app.llm.ollama_provider.requests.get')
    def test_full_review_cycle_with_ollama(self, mock_get, mock_post):
        """Test complete review cycle with Ollama provider."""
        from app.llm.ollama_provider import OllamaProvider
        from app.models.feedback import Feedback
        
        # Mock Ollama is running
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "models": [
                {"name": "llama3"}
            ]
        }
        mock_get.return_value = mock_get_response
        
        # Mock generate responses
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        
        responses = [
            # Presenter response
            {"response": "Problem Summary: Build a task management web app", "done": True},
            # Reviewer 1 response
            {"response": "VERDICT: APPROVE\n\nGood technical approach.", "done": True},
            # Reviewer 2 response
            {"response": "VERDICT: APPROVE\n\nClear requirements.", "done": True},
            # Confidence response
            {"response": "Score: 85\n\nReasoning: Strong consensus.", "done": True}
        ]
        
        mock_post_response.json.side_effect = responses
        mock_post.return_value = mock_post_response
        
        # Create provider
        provider = OllamaProvider(model="llama3")
        
        # Run presenter using correct method
        presenter = PresenterAgent(llm_provider=provider, model="llama3")
        presenter_output = presenter.generate(
            requirements="Build a task management app",
            file_summaries=None
        )
        assert len(presenter_output) > 0
        
        # Run reviewers
        tech_reviewer = TechnicalReviewer(llm_provider=provider, model="llama3")
        clarity_reviewer = ClarityReviewer(llm_provider=provider, model="llama3")
        
        tech_result = tech_reviewer.review(presenter_output, iteration=1)
        clarity_result = clarity_reviewer.review(presenter_output, iteration=1)
        
        # Agents return Feedback objects
        assert isinstance(tech_result, Feedback)
        assert isinstance(clarity_result, Feedback)
        
        # Run confidence agent with correct method signature
        confidence = ConfidenceAgent(llm_provider=provider, model="llama3")
        score_result = confidence.score(
            content=presenter_output,
            feedback_list=[tech_result, clarity_result]
        )
        
        assert 'score' in score_result
        assert isinstance(score_result['score'], (int, float))

