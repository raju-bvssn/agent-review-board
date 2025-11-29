"""Unit tests for Phase 2 agent implementations."""

import pytest
from app.agents.presenter import PresenterAgent
from app.agents.reviewer import (
    ReviewerAgent, TechnicalReviewer, ClarityReviewer,
    SecurityReviewer, BusinessReviewer, UXReviewer
)
from app.agents.confidence import ConfidenceAgent
from app.llm.mock_provider import MockLLMProvider
from app.models.feedback import Feedback


class TestPresenterAgentPhase2:
    """Tests for Phase 2 PresenterAgent."""
    
    def test_presenter_generates_with_mock_provider(self):
        """Test that presenter generates content using mock provider."""
        provider = MockLLMProvider()
        agent = PresenterAgent(provider)
        
        result = agent.generate("Create a REST API for user management")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Mock provider should have been called
        assert provider.get_call_count() > 0
    
    def test_presenter_with_feedback(self):
        """Test presenter with feedback from previous iteration."""
        provider = MockLLMProvider()
        agent = PresenterAgent(provider)
        
        feedback = ["Add authentication", "Include rate limiting"]
        previous_output = "Previous version"
        
        result = agent.generate(
            requirements="Create API",
            feedback=feedback,
            previous_output=previous_output
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_presenter_with_file_summaries(self):
        """Test presenter with file summaries."""
        provider = MockLLMProvider()
        agent = PresenterAgent(provider)
        
        file_summaries = ["requirements.txt contents", "design_doc.pdf summary"]
        
        result = agent.generate(
            requirements="Create API",
            file_summaries=file_summaries
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_presenter_execute_method(self):
        """Test presenter execute method."""
        provider = MockLLMProvider()
        agent = PresenterAgent(provider)
        
        result = agent.execute(requirements="Test requirements")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestReviewerAgentPhase2:
    """Tests for Phase 2 ReviewerAgent."""
    
    def test_reviewer_generates_feedback(self):
        """Test that reviewer generates feedback."""
        provider = MockLLMProvider()
        agent = ReviewerAgent(provider, role="test_reviewer")
        
        content = "This is content to review"
        result = agent.review(content, iteration=0)
        
        assert isinstance(result, Feedback)
        assert result.reviewer_role == "test_reviewer"
        assert len(result.feedback_points) > 0
    
    def test_reviewer_feedback_not_approved_by_default(self):
        """Test that feedback is not approved by default."""
        provider = MockLLMProvider()
        agent = ReviewerAgent(provider, role="test_reviewer")
        
        result = agent.review("Test content", iteration=0)
        
        assert result.approved is False
        assert result.modified is False
    
    def test_technical_reviewer_initialization(self):
        """Test TechnicalReviewer has correct configuration."""
        provider = MockLLMProvider()
        agent = TechnicalReviewer(provider)
        
        assert agent.role == "technical_reviewer"
        assert "technical" in agent.role_description.lower()
        assert "architectural" in agent.focus_areas.lower() or "architecture" in agent.focus_areas.lower()
    
    def test_clarity_reviewer_initialization(self):
        """Test ClarityReviewer has correct configuration."""
        provider = MockLLMProvider()
        agent = ClarityReviewer(provider)
        
        assert agent.role == "clarity_reviewer"
        assert "clarity" in agent.focus_areas.lower()
    
    def test_security_reviewer_initialization(self):
        """Test SecurityReviewer has correct configuration."""
        provider = MockLLMProvider()
        agent = SecurityReviewer(provider)
        
        assert agent.role == "security_reviewer"
        assert "security" in agent.focus_areas.lower()
    
    def test_business_reviewer_initialization(self):
        """Test BusinessReviewer has correct configuration."""
        provider = MockLLMProvider()
        agent = BusinessReviewer(provider)
        
        assert agent.role == "business_reviewer"
        assert "business" in agent.focus_areas.lower()
    
    def test_ux_reviewer_initialization(self):
        """Test UXReviewer has correct configuration."""
        provider = MockLLMProvider()
        agent = UXReviewer(provider)
        
        assert agent.role == "ux_reviewer"
        assert "ux" in agent.role_description.lower() or "user experience" in agent.role_description.lower()


class TestConfidenceAgentPhase2:
    """Tests for Phase 2 ConfidenceAgent."""
    
    def test_confidence_score_returns_dict(self):
        """Test that score returns a dictionary with required fields."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        feedback = [
            Feedback(
                reviewer_role="technical",
                feedback_points=["Point 1", "Point 2"],
                iteration=0
            )
        ]
        
        result = agent.score("Test content", feedback)
        
        assert isinstance(result, dict)
        assert "score" in result
        assert "reasoning" in result
        assert isinstance(result["score"], (int, float))
    
    def test_confidence_score_with_no_feedback(self):
        """Test confidence scoring with no feedback."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        result = agent.score("Test content", [])
        
        assert isinstance(result, dict)
        assert result["score"] >= 0
    
    def test_confidence_score_range(self):
        """Test that confidence score is in valid range."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        feedback = [
            Feedback(
                reviewer_role="technical",
                feedback_points=["Point 1"],
                iteration=0
            )
        ]
        
        result = agent.score("Test content", feedback)
        
        assert 0 <= result["score"] <= 100
    
    def test_evaluate_convergence(self):
        """Test convergence evaluation."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        # Create feedback history (2 iterations)
        history = [
            [Feedback(reviewer_role="tech", feedback_points=["P1", "P2", "P3"], iteration=0)],
            [Feedback(reviewer_role="tech", feedback_points=["P1", "P2"], iteration=1)]
        ]
        
        result = agent.evaluate_convergence(history)
        
        assert isinstance(result, dict)
        assert "is_converging" in result
        assert "convergence_score" in result
    
    def test_execute_method(self):
        """Test execute method."""
        provider = MockLLMProvider()
        agent = ConfidenceAgent(provider)
        
        feedback = [
            Feedback(
                reviewer_role="technical",
                feedback_points=["Point 1"],
                iteration=0
            )
        ]
        
        result = agent.execute(content="Test", feedback_list=feedback)
        
        assert isinstance(result, dict)
        assert "score" in result

