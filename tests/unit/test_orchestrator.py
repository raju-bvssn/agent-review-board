"""Unit tests for Orchestrator."""

import pytest
from app.core.orchestrator import Orchestrator, IterationResult
from app.core.session_manager import SessionManager
from app.llm.mock_provider import MockLLMProvider


class TestOrchestrator:
    """Tests for Orchestrator."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a session manager with active session."""
        manager = SessionManager()
        manager.create_session(
            session_name="Test Session",
            requirements="Test requirements",
            selected_roles=["Technical Reviewer", "Clarity Reviewer"],
            models_config={}
        )
        yield manager
        manager.end_session()
    
    @pytest.fixture
    def orchestrator(self, session_manager):
        """Create an orchestrator instance."""
        provider = MockLLMProvider()
        return Orchestrator(session_manager, provider)
    
    def test_orchestrator_initialization(self, session_manager):
        """Test that orchestrator can be initialized."""
        provider = MockLLMProvider()
        orchestrator = Orchestrator(session_manager, provider)
        
        assert orchestrator is not None
        assert orchestrator.session_manager is session_manager
        assert orchestrator.llm_provider is provider
        assert len(orchestrator.iteration_history) == 0
    
    def test_run_iteration_creates_result(self, orchestrator):
        """Test that run_iteration creates an IterationResult."""
        result = orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        assert isinstance(result, IterationResult)
        assert result.iteration == 0
        assert result.presenter_output is not None
        assert len(result.reviewer_feedback) > 0
        assert result.confidence_result is not None
    
    def test_run_iteration_stores_in_history(self, orchestrator):
        """Test that iterations are stored in history."""
        orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        assert len(orchestrator.iteration_history) == 1
        assert orchestrator.current_iteration_result is not None
    
    def test_run_multiple_iterations(self, orchestrator):
        """Test running multiple iterations."""
        # First iteration
        result1 = orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        orchestrator.approve_current_iteration()
        
        # Second iteration
        result2 = orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        assert len(orchestrator.iteration_history) == 2
        assert result1.iteration == 0
        assert result2.iteration == 1
    
    def test_approve_current_iteration(self, orchestrator):
        """Test approving current iteration."""
        result = orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        assert result.human_gate_approved is False
        
        orchestrator.approve_current_iteration()
        
        assert result.human_gate_approved is True
        assert all(f.approved for f in result.reviewer_feedback)
    
    def test_reject_current_iteration(self, orchestrator):
        """Test rejecting current iteration."""
        result = orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        orchestrator.approve_current_iteration()
        assert result.human_gate_approved is True
        
        orchestrator.reject_current_iteration()
        assert result.human_gate_approved is False
    
    def test_can_proceed_to_next_iteration(self, orchestrator):
        """Test checking if can proceed to next iteration."""
        # No iteration yet
        assert orchestrator.can_proceed_to_next_iteration() is False
        
        # Run iteration but don't approve
        orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        assert orchestrator.can_proceed_to_next_iteration() is False
        
        # Approve iteration
        orchestrator.approve_current_iteration()
        assert orchestrator.can_proceed_to_next_iteration() is True
    
    def test_get_approved_feedback(self, orchestrator):
        """Test getting approved feedback."""
        orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        orchestrator.approve_current_iteration()
        
        approved_feedback = orchestrator.get_approved_feedback()
        
        assert isinstance(approved_feedback, list)
        assert len(approved_feedback) > 0
    
    def test_get_iteration_history(self, orchestrator):
        """Test getting iteration history."""
        orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        history = orchestrator.get_iteration_history()
        
        assert isinstance(history, list)
        assert len(history) == 1
        assert isinstance(history[0], IterationResult)
    
    def test_get_current_result(self, orchestrator):
        """Test getting current result."""
        assert orchestrator.get_current_result() is None
        
        orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        current = orchestrator.get_current_result()
        assert current is not None
        assert isinstance(current, IterationResult)
    
    def test_reset(self, orchestrator):
        """Test resetting orchestrator."""
        orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        assert len(orchestrator.iteration_history) > 0
        assert orchestrator.current_iteration_result is not None
        
        orchestrator.reset()
        
        assert len(orchestrator.iteration_history) == 0
        assert orchestrator.current_iteration_result is None
    
    def test_run_iteration_with_multiple_reviewers(self, orchestrator):
        """Test running iteration with multiple reviewers."""
        result = orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer", "Clarity Reviewer", "Security Reviewer"]
        )
        
        assert len(result.reviewer_feedback) == 3
        assert all(f.reviewer_role for f in result.reviewer_feedback)
    
    def test_approve_with_modified_feedback(self, orchestrator):
        """Test approving with modified feedback."""
        result = orchestrator.run_iteration(
            requirements="Test requirements",
            selected_roles=["Technical Reviewer"]
        )
        
        # Get the actual role name from feedback
        actual_role = result.reviewer_feedback[0].reviewer_role if result.reviewer_feedback else "technical_reviewer"
        
        modified = {
            actual_role: ["Modified point 1", "Modified point 2"]
        }
        
        orchestrator.approve_current_iteration(modified_feedback=modified)
        
        # Check that feedback was modified
        tech_feedback = result.reviewer_feedback[0]
        assert tech_feedback.modified is True
        assert tech_feedback.feedback_points == modified[actual_role]


class TestIterationResult:
    """Tests for IterationResult."""
    
    def test_iteration_result_creation(self):
        """Test creating an IterationResult."""
        result = IterationResult(
            iteration=0,
            presenter_output="Test output",
            reviewer_feedback=[],
            confidence_result={"score": 75.0}
        )
        
        assert result.iteration == 0
        assert result.presenter_output == "Test output"
        assert result.reviewer_feedback == []
        assert result.confidence_result == {"score": 75.0}
        assert result.error is None
        assert result.human_gate_approved is False
    
    def test_iteration_result_with_error(self):
        """Test creating an IterationResult with error."""
        result = IterationResult(
            iteration=0,
            presenter_output="",
            reviewer_feedback=[],
            confidence_result={},
            error="Test error"
        )
        
        assert result.error == "Test error"

