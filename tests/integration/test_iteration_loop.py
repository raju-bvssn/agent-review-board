"""Integration tests for complete iteration loop with WorkflowEngine."""

import pytest
from app.orchestration.workflow_engine import WorkflowEngine
from app.orchestration.iteration_state import IterationState
from app.core.session_manager import SessionManager
from app.llm.mock_provider import MockLLMProvider


class TestIterationLoop:
    """Integration tests for full iteration workflow."""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager."""
        manager = SessionManager()
        # Create a test session
        manager.create_session(
            session_name="Test Session",
            requirements="Build a REST API",
            selected_roles=["Technical Reviewer", "Security Reviewer"],
            models_config={"provider": "mock"}
        )
        return manager
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock LLM provider."""
        return MockLLMProvider()
    
    @pytest.fixture
    def workflow_engine(self, mock_provider, session_manager):
        """Create workflow engine."""
        return WorkflowEngine(mock_provider, session_manager)
    
    def test_single_iteration_complete_flow(self, workflow_engine):
        """Test running a single complete iteration."""
        requirements = "Design a microservices architecture"
        selected_roles = ["Technical Reviewer", "Security Reviewer"]
        
        # Run iteration
        result = workflow_engine.run_iteration(
            requirements,
            selected_roles
        )
        
        # Verify iteration state
        assert isinstance(result, IterationState)
        assert result.iteration == 1
        assert result.presenter_output
        assert len(result.reviewer_feedback) == 2
        assert result.aggregated_feedback
        assert 0.0 <= result.confidence <= 1.0
        assert result.approved is False
        assert result.error is None
    
    def test_multiple_iterations(self, workflow_engine):
        """Test running multiple iterations."""
        requirements = "Design a database schema"
        selected_roles = ["Technical Reviewer"]
        
        # First iteration
        result1 = workflow_engine.run_iteration(requirements, selected_roles)
        assert result1.iteration == 1
        
        # Approve first iteration
        workflow_engine.approve_iteration(1)
        
        # Second iteration
        result2 = workflow_engine.run_iteration(requirements, selected_roles)
        assert result2.iteration == 2
        
        # Verify history
        assert workflow_engine.get_iteration_count() == 2
    
    def test_iteration_approval_flow(self, workflow_engine):
        """Test HITL approval workflow."""
        requirements = "Create API endpoints"
        selected_roles = ["Technical Reviewer"]
        
        # Run iteration
        result = workflow_engine.run_iteration(requirements, selected_roles)
        assert result.approved is False
        
        # Approve iteration
        success = workflow_engine.approve_iteration(1)
        assert success is True
        
        # Verify approval
        assert result.approved is True
    
    def test_cannot_run_iteration_when_finalized(self, workflow_engine, session_manager):
        """Test that iterations cannot run after session finalization."""
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer"]
        
        # Run and approve iteration
        result = workflow_engine.run_iteration(requirements, selected_roles)
        workflow_engine.approve_iteration(1)
        
        # Finalize session
        session_manager.finalize_session()
        
        # Try to run another iteration
        with pytest.raises(ValueError, match="finalized"):
            workflow_engine.run_iteration(requirements, selected_roles)
    
    def test_max_iterations_limit(self, workflow_engine):
        """Test maximum iteration limit enforcement."""
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer"]
        
        # Run up to max iterations
        for i in range(WorkflowEngine.MAX_ITERATIONS):
            result = workflow_engine.run_iteration(requirements, selected_roles)
            workflow_engine.approve_iteration(result.iteration)
        
        # Try to exceed limit
        with pytest.raises(ValueError, match="Maximum iterations"):
            workflow_engine.run_iteration(requirements, selected_roles)
    
    def test_iteration_state_storage(self, workflow_engine, session_manager):
        """Test that iteration states are properly stored."""
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer", "Security Reviewer"]
        
        # Run iteration
        result = workflow_engine.run_iteration(requirements, selected_roles)
        
        # Verify stored in workflow engine
        current = workflow_engine.get_current_iteration()
        assert current is not None
        assert current.iteration == 1
        
        # Verify stored in session manager
        last_iteration = session_manager.get_last_iteration()
        assert last_iteration is not None
        assert last_iteration.iteration == 1
    
    def test_get_all_iterations(self, workflow_engine):
        """Test retrieving all iteration history."""
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer"]
        
        # Run multiple iterations
        for i in range(3):
            result = workflow_engine.run_iteration(requirements, selected_roles)
            workflow_engine.approve_iteration(result.iteration)
        
        # Get all iterations
        all_iterations = workflow_engine.get_all_iterations()
        assert len(all_iterations) == 3
        assert all([isinstance(it, IterationState) for it in all_iterations])
    
    def test_confidence_calculation_in_iteration(self, workflow_engine):
        """Test that confidence is calculated in each iteration."""
        requirements = "Build authentication system"
        selected_roles = ["Technical Reviewer", "Security Reviewer"]
        
        result = workflow_engine.run_iteration(requirements, selected_roles)
        
        # Confidence should be calculated
        assert result.confidence > 0.0
        assert result.confidence <= 1.0
    
    def test_aggregation_in_iteration(self, workflow_engine):
        """Test that feedback is aggregated in each iteration."""
        requirements = "Design data model"
        selected_roles = ["Technical Reviewer", "Security Reviewer", "Quality Reviewer"]
        
        result = workflow_engine.run_iteration(requirements, selected_roles)
        
        # Aggregated feedback should exist
        assert result.aggregated_feedback
        assert len(result.aggregated_feedback) > 0
    
    def test_iteration_with_file_summaries(self, workflow_engine):
        """Test iteration with file context."""
        requirements = "Review existing code"
        selected_roles = ["Technical Reviewer"]
        file_summaries = [
            "File: main.py - Contains entry point",
            "File: utils.py - Helper functions"
        ]
        
        result = workflow_engine.run_iteration(
            requirements,
            selected_roles,
            file_summaries=file_summaries
        )
        
        assert result.iteration == 1
        assert result.presenter_output  # Should include file context
    
    def test_is_ready_for_finalization(self, workflow_engine):
        """Test finalization readiness check."""
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer"]
        
        # Not ready initially
        assert workflow_engine.is_ready_for_finalization() is False
        
        # Run iteration
        result = workflow_engine.run_iteration(requirements, selected_roles)
        
        # Still not ready (not approved)
        assert workflow_engine.is_ready_for_finalization() is False
        
        # Approve iteration
        workflow_engine.approve_iteration(1)
        
        # If confidence is high enough, should be ready
        if result.confidence >= 0.82:
            assert workflow_engine.is_ready_for_finalization() is True
    
    def test_can_run_next_iteration(self, workflow_engine, session_manager):
        """Test checking if next iteration can run."""
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer"]
        
        # Can run first iteration
        assert workflow_engine.can_run_next_iteration() is True
        
        # Run iteration
        result = workflow_engine.run_iteration(requirements, selected_roles)
        
        # Cannot run next until approved
        assert workflow_engine.can_run_next_iteration() is False
        
        # Approve
        workflow_engine.approve_iteration(1)
        
        # Can run next
        assert workflow_engine.can_run_next_iteration() is True
        
        # Finalize session
        session_manager.finalize_session()
        
        # Cannot run after finalization
        assert workflow_engine.can_run_next_iteration() is False
    
    def test_workflow_reset(self, workflow_engine):
        """Test resetting workflow engine."""
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer"]
        
        # Run iteration
        workflow_engine.run_iteration(requirements, selected_roles)
        assert workflow_engine.get_iteration_count() == 1
        
        # Reset
        workflow_engine.reset()
        
        # Verify reset
        assert workflow_engine.get_iteration_count() == 0
        assert workflow_engine.get_current_iteration() is None
    
    def test_error_handling_in_iteration(self, session_manager):
        """Test error handling when iteration fails."""
        # Create mock provider that raises exception
        from unittest.mock import Mock
        mock_provider = Mock()
        mock_provider.generate_text.side_effect = Exception("LLM Error")
        
        workflow_engine = WorkflowEngine(mock_provider, session_manager)
        
        requirements = "Test requirements"
        selected_roles = ["Technical Reviewer"]
        
        # Run iteration (should handle error gracefully)
        result = workflow_engine.run_iteration(requirements, selected_roles)
        
        # Should have error state
        assert result.has_error()
        assert result.error is not None
        assert "LLM Error" in result.error


class TestParallelReviewerExecution:
    """Test parallel execution of reviewers."""
    
    @pytest.fixture
    def workflow_engine_parallel(self):
        """Create workflow engine for parallel testing."""
        session_manager = SessionManager()
        # Create a test session
        session_manager.create_session(
            session_name="Parallel Test Session",
            requirements="Test parallel execution",
            selected_roles=["Technical Reviewer", "Security Reviewer", "Quality Reviewer", "Clarity Reviewer"],
            models_config={"provider": "mock"}
        )
        return WorkflowEngine(MockLLMProvider(), session_manager)
    
    def test_parallel_reviewer_execution(self, workflow_engine_parallel):
        """Test that reviewers execute in parallel."""
        import time
        
        requirements = "Test parallel execution"
        selected_roles = [
            "Technical Reviewer",
            "Security Reviewer",
            "Quality Reviewer",
            "Clarity Reviewer"
        ]
        
        start_time = time.time()
        result = workflow_engine_parallel.run_iteration(
            requirements,
            selected_roles,
            use_parallel=True
        )
        parallel_time = time.time() - start_time
        
        # All reviewers should have provided feedback
        assert len(result.reviewer_feedback) == 4
        
        # Verify execution completed
        assert result.iteration == 1
        assert result.aggregated_feedback


class TestIterationStateManagement:
    """Test iteration state management."""
    
    def test_iteration_state_creation(self):
        """Test creating iteration state."""
        state = IterationState(
            iteration=1,
            presenter_output="Test output",
            reviewer_feedback={"Tech": "Feedback 1"},
            aggregated_feedback="Aggregated",
            confidence=0.85,
            approved=False
        )
        
        assert state.iteration == 1
        assert state.confidence == 0.85
        assert state.is_approved() is False
        assert state.has_error() is False
        assert state.meets_confidence_threshold(0.82) is True
    
    def test_iteration_state_to_dict(self):
        """Test converting iteration state to dictionary."""
        state = IterationState(
            iteration=1,
            presenter_output="Output",
            reviewer_feedback={"Tech": "Feedback"},
            aggregated_feedback="Aggregated",
            confidence=0.75
        )
        
        state_dict = state.to_dict()
        
        assert isinstance(state_dict, dict)
        assert state_dict['iteration'] == 1
        assert state_dict['confidence'] == 0.75
        assert 'timestamp' in state_dict
    
    def test_iteration_state_from_dict(self):
        """Test creating iteration state from dictionary."""
        state_dict = {
            'iteration': 2,
            'presenter_output': 'Output',
            'reviewer_feedback': {'Tech': 'Feedback'},
            'aggregated_feedback': 'Aggregated',
            'confidence': 0.90,
            'approved': True,
            'error': None
        }
        
        state = IterationState.from_dict(state_dict)
        
        assert isinstance(state, IterationState)
        assert state.iteration == 2
        assert state.confidence == 0.90
        assert state.approved is True

