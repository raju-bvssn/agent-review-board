"""Integration tests for component interactions."""

import pytest
from app.core.session_manager import SessionManager
from app.agents.presenter import PresenterAgent
from app.agents.reviewer import TechnicalReviewer, ClarityReviewer
from app.agents.confidence import ConfidenceAgent
from app.llm.mock_provider import MockLLMProvider


class TestComponentIntegration:
    """Integration tests for component interactions."""
    
    def test_session_manager_and_agents(self):
        """Test SessionManager working with agents."""
        # Create provider and agents
        provider = MockLLMProvider()
        presenter = PresenterAgent(provider)
        technical_reviewer = TechnicalReviewer(provider)
        
        # Create session
        manager = SessionManager()
        session = manager.create_session(
            session_name="Integration Test",
            requirements="Test requirements",
            selected_roles=["technical"],
            models_config={"presenter": "mock-model"}
        )
        
        assert session is not None
        assert manager.get_current_session() is not None
        
        # Generate content
        content = presenter.generate(session.requirements)
        assert isinstance(content, str)
        
        # Get review
        feedback = technical_reviewer.review(content, manager.get_iteration())
        assert feedback is not None
        assert feedback.iteration == 0
        
        # Cleanup
        manager.end_session()
    
    def test_full_iteration_cycle(self):
        """Test a full iteration cycle with multiple reviewers."""
        # Setup
        provider = MockLLMProvider()
        presenter = PresenterAgent(provider)
        technical = TechnicalReviewer(provider)
        clarity = ClarityReviewer(provider)
        confidence = ConfidenceAgent(provider)
        
        manager = SessionManager()
        session = manager.create_session(
            session_name="Full Cycle Test",
            requirements="Create a test document",
            selected_roles=["technical", "clarity"],
            models_config={}
        )
        
        # Iteration 0
        content = presenter.generate(session.requirements)
        assert len(content) > 0
        
        # Get reviews
        feedback1 = technical.review(content, manager.get_iteration())
        feedback2 = clarity.review(content, manager.get_iteration())
        
        assert feedback1.reviewer_role == "technical_reviewer"
        assert feedback2.reviewer_role == "clarity_reviewer"
        
        # Get confidence score
        all_feedback = [feedback1, feedback2]
        score_result = confidence.score(content, all_feedback)
        
        assert isinstance(score_result, dict)
        assert "score" in score_result
        assert 0.0 <= score_result["score"] <= 100.0
        
        # Move to next iteration
        manager.increment_iteration()
        assert manager.get_iteration() == 1
        
        # Cleanup
        manager.end_session()
    
    def test_mock_provider_with_multiple_agents(self):
        """Test MockLLMProvider working with multiple agents."""
        provider = MockLLMProvider()
        
        # Create multiple agents sharing the same provider
        presenter = PresenterAgent(provider)
        reviewer1 = TechnicalReviewer(provider)
        reviewer2 = ClarityReviewer(provider)
        confidence = ConfidenceAgent(provider)
        
        # All should have the same provider instance
        assert presenter.llm_provider is provider
        assert reviewer1.llm_provider is provider
        assert reviewer2.llm_provider is provider
        assert confidence.llm_provider is provider
        
        # All agents should work (even if they're stubs in Phase 1)
        result1 = presenter.generate("test")
        result2 = reviewer1.review("test", 0)
        result3 = reviewer2.review("test", 0)
        result4 = confidence.score("test", [])
        
        # Verify agents return appropriate types
        assert isinstance(result1, str)
        assert hasattr(result2, 'reviewer_role')
        assert hasattr(result3, 'reviewer_role')
        assert isinstance(result4, dict)
        assert "score" in result4
    
    def test_session_state_persistence_in_memory(self):
        """Test that session state persists correctly in memory."""
        manager = SessionManager()
        
        session = manager.create_session(
            session_name="Persistence Test",
            requirements="Test persistence",
            selected_roles=["technical"],
            models_config={"presenter": "mock-model"}
        )
        
        session_id = session.session_id
        
        # Session should be in history
        assert session_id in manager.session_history
        
        # Should be able to retrieve it
        assert manager.session_history[session_id] == session
        
        # Should be current session
        assert manager.get_current_session().session_id == session_id
        
        # Cleanup
        manager.end_session()

