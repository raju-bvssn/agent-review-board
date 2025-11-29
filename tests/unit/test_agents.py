"""Unit tests for agents."""

import pytest
from app.agents.base_agent import BaseAgent
from app.agents.presenter import PresenterAgent
from app.agents.reviewer import ReviewerAgent, TechnicalReviewer, ClarityReviewer, SecurityReviewer
from app.agents.confidence import ConfidenceAgent
from app.llm.mock_provider import MockLLMProvider
from app.models.feedback import Feedback


class TestPresenterAgent:
    """Tests for PresenterAgent."""
    
    def test_presenter_agent_initialization(self):
        """Test that PresenterAgent can be initialized."""
        provider = MockLLMProvider()
        agent = PresenterAgent(provider)
        
        assert agent is not None
        assert agent.role == "presenter"
        assert agent.llm_provider is provider
    
    def test_presenter_generate_returns_string(self):
        """Test that generate returns a string."""
        provider = MockLLMProvider()
        agent = PresenterAgent(provider)
        
        result = agent.generate("Test requirements")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_presenter_execute_method(self):
        """Test that execute method works."""
        provider = MockLLMProvider()
        agent = PresenterAgent(provider)
        
        result = agent.execute(requirements="Test requirements")
        
        assert isinstance(result, str)


class TestReviewerAgent:
    """Tests for ReviewerAgent."""
    
    def test_reviewer_agent_initialization(self):
        """Test that ReviewerAgent can be initialized."""
        provider = MockLLMProvider()
        agent = ReviewerAgent(provider, role="test_reviewer")
        
        assert agent is not None
        assert agent.role == "test_reviewer"
        assert agent.llm_provider is provider
    
    def test_reviewer_review_returns_feedback(self):
        """Test that review returns Feedback object."""
        provider = MockLLMProvider()
        agent = ReviewerAgent(provider, role="test_reviewer")
        
        result = agent.review("Test content", iteration=1)
        
        assert isinstance(result, Feedback)
        assert result.reviewer_role == "test_reviewer"
        assert result.iteration == 1
        assert len(result.feedback_points) > 0
    
    def test_reviewer_feedback_not_approved_by_default(self):
        """Test that feedback is not approved by default."""
        provider = MockLLMProvider()
        agent = ReviewerAgent(provider, role="test_reviewer")
        
        result = agent.review("Test content", iteration=1)
        
        assert result.approved is False
        assert result.modified is False
    
    def test_reviewer_execute_method(self):
        """Test that execute method works."""
        provider = MockLLMProvider()
        agent = ReviewerAgent(provider, role="test_reviewer")
        
        result = agent.execute(content="Test content", iteration=1)
        
        assert isinstance(result, Feedback)


class TestSpecializedReviewers:
    """Tests for specialized reviewer subclasses."""
    
    def test_technical_reviewer_initialization(self):
        """Test TechnicalReviewer initialization."""
        provider = MockLLMProvider()
        agent = TechnicalReviewer(provider)
        
        assert agent.role == "technical_reviewer"
    
    def test_clarity_reviewer_initialization(self):
        """Test ClarityReviewer initialization."""
        provider = MockLLMProvider()
        agent = ClarityReviewer(provider)
        
        assert agent.role == "clarity_reviewer"
    
    def test_security_reviewer_initialization(self):
        """Test SecurityReviewer initialization."""
        provider = MockLLMProvider()
        agent = SecurityReviewer(provider)
        
        assert agent.role == "security_reviewer"


class TestConfidenceAgent:
    """Tests for ConfidenceAgent."""
    
    def test_confidence_agent_initialization(self):
        """Test that ConfidenceAgent can be initialized."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        assert agent is not None
        assert agent.role == "confidence"
        assert agent.llm_provider is provider
    
    def test_confidence_score_returns_dict(self):
        """Test that score returns a dict with score and reasoning."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        result = agent.score("Test content", [])
        
        assert isinstance(result, dict)
        assert "score" in result
        assert "reasoning" in result
        assert 0.0 <= result["score"] <= 100.0
    
    def test_confidence_evaluate_convergence_returns_dict(self):
        """Test that evaluate_convergence returns a dict."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        result = agent.evaluate_convergence([])
        
        assert isinstance(result, dict)
        assert "is_converging" in result
        assert "convergence_score" in result
    
    def test_confidence_execute_method(self):
        """Test that execute method works."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        result = agent.execute(content="Test content", feedback_list=[])
        
        assert isinstance(result, dict)
        assert "score" in result


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseAgent cannot be instantiated directly."""
        provider = MockLLMProvider()
        
        with pytest.raises(TypeError):
            agent = BaseAgent(provider)
    
    def test_agent_interface_methods_exist(self):
        """Test that the interface defines required methods."""
        assert hasattr(BaseAgent, 'execute')
        assert hasattr(BaseAgent, 'get_role')

