"""Unit tests for Pydantic models."""

import pytest
from datetime import datetime
from app.models.session_state import SessionState, LLMConfig, AgentConfig
from app.models.message import Message
from app.models.feedback import Feedback, ReviewerFeedbackCollection


class TestSessionState:
    """Tests for SessionState model."""
    
    def test_session_state_creation(self):
        """Test that SessionState can be created with required fields."""
        session = SessionState(
            session_id="test-123",
            session_name="Test Session",
            requirements="Test requirements"
        )
        
        assert session.session_id == "test-123"
        assert session.session_name == "Test Session"
        assert session.requirements == "Test requirements"
        assert session.iteration == 0
        assert isinstance(session.created_at, datetime)
    
    def test_session_state_with_optional_fields(self):
        """Test SessionState with optional fields."""
        session = SessionState(
            session_id="test-456",
            session_name="Test Session 2",
            requirements="Test requirements 2",
            selected_roles=["technical", "clarity"],
            iteration=5
        )
        
        assert len(session.selected_roles) == 2
        assert session.iteration == 5


class TestLLMConfig:
    """Tests for LLMConfig model."""
    
    def test_llm_config_creation(self):
        """Test LLMConfig creation."""
        config = LLMConfig(
            provider="mock",
            model_name="mock-model-small"
        )
        
        assert config.provider == "mock"
        assert config.model_name == "mock-model-small"
        assert config.temperature == 0.7  # default
        assert config.max_tokens == 1000  # default
    
    def test_llm_config_validation(self):
        """Test LLMConfig validation."""
        # Temperature should be between 0 and 2
        with pytest.raises(ValueError):
            LLMConfig(
                provider="mock",
                model_name="test",
                temperature=3.0  # invalid
            )


class TestAgentConfig:
    """Tests for AgentConfig model."""
    
    def test_agent_config_creation(self):
        """Test AgentConfig creation."""
        config = AgentConfig(
            agent_type="presenter",
            role="main_presenter",
            model_name="mock-model-medium"
        )
        
        assert config.agent_type == "presenter"
        assert config.role == "main_presenter"
        assert config.model_name == "mock-model-medium"


class TestMessage:
    """Tests for Message model."""
    
    def test_message_creation(self):
        """Test Message creation."""
        msg = Message(
            sender="presenter",
            content="Test message",
            message_type="response"
        )
        
        assert msg.sender == "presenter"
        assert msg.content == "Test message"
        assert msg.message_type == "response"
        assert isinstance(msg.timestamp, datetime)


class TestFeedback:
    """Tests for Feedback model."""
    
    def test_feedback_creation(self):
        """Test Feedback creation."""
        feedback = Feedback(
            reviewer_role="technical",
            feedback_points=["Point 1", "Point 2", "Point 3"],
            iteration=1
        )
        
        assert feedback.reviewer_role == "technical"
        assert len(feedback.feedback_points) == 3
        assert feedback.iteration == 1
        assert feedback.approved is False
    
    def test_feedback_validation_max_points(self):
        """Test that feedback validates max 8 points."""
        with pytest.raises(ValueError):
            Feedback(
                reviewer_role="technical",
                feedback_points=["Point"] * 9,  # too many
                iteration=1
            )
    
    def test_feedback_validation_min_points(self):
        """Test that feedback requires at least 1 point."""
        with pytest.raises(ValueError):
            Feedback(
                reviewer_role="technical",
                feedback_points=[],  # too few
                iteration=1
            )


class TestReviewerFeedbackCollection:
    """Tests for ReviewerFeedbackCollection model."""
    
    def test_collection_creation(self):
        """Test ReviewerFeedbackCollection creation."""
        collection = ReviewerFeedbackCollection(
            iteration=1,
            feedbacks=[]
        )
        
        assert collection.iteration == 1
        assert len(collection.feedbacks) == 0
        assert collection.all_approved is False

