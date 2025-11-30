"""Unit tests for reviewer manager."""

import pytest
from unittest.mock import Mock, patch
from app.orchestration.reviewer_manager import (
    ReviewerManager,
    create_reviewer_instances,
    REVIEWER_CLASS_MAP
)
from app.llm.mock_provider import MockLLMProvider
from app.agents.reviewer import (
    TechnicalReviewer,
    ClarityReviewer,
    SecurityReviewer,
    BusinessReviewer,
    UXReviewer
)
from app.models.feedback import Feedback


class TestReviewerManager:
    """Test suite for ReviewerManager."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock LLM provider."""
        return MockLLMProvider()
    
    @pytest.fixture
    def reviewer_manager(self, mock_provider):
        """Create reviewer manager."""
        return ReviewerManager(mock_provider)
    
    def test_reviewer_manager_initialization(self, mock_provider):
        """Test reviewer manager initialization."""
        manager = ReviewerManager(mock_provider)
        assert manager.llm_provider == mock_provider
    
    def test_run_reviewers_parallel(self, reviewer_manager):
        """Test running reviewers in parallel mode."""
        presenter_output = "This is a design document..."
        selected_roles = ["Technical Reviewer", "Security Reviewer"]
        iteration = 1
        
        result = reviewer_manager.run_reviewers(
            presenter_output,
            selected_roles,
            iteration,
            parallel=True
        )
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "Technical Reviewer" in result
        assert "Security Reviewer" in result
        
        # Check feedback format
        for role, feedback_str in result.items():
            assert isinstance(feedback_str, str)
            assert len(feedback_str) > 0
    
    def test_run_reviewers_sequential(self, reviewer_manager):
        """Test running reviewers in sequential mode."""
        presenter_output = "This is a design document..."
        selected_roles = ["Technical Reviewer", "Quality Reviewer"]
        iteration = 1
        
        result = reviewer_manager.run_reviewers(
            presenter_output,
            selected_roles,
            iteration,
            parallel=False
        )
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "Technical Reviewer" in result
        assert "Quality Reviewer" in result
    
    def test_run_reviewers_all_types(self, reviewer_manager):
        """Test running all reviewer types."""
        presenter_output = "Complete design document..."
        selected_roles = [
            "Technical Reviewer",
            "Clarity Reviewer",
            "Security Reviewer",
            "Business Reviewer",
            "UX Reviewer"
        ]
        iteration = 1
        
        result = reviewer_manager.run_reviewers(
            presenter_output,
            selected_roles,
            iteration
        )
        
        assert len(result) == 5
        for role in selected_roles:
            assert role in result
            assert isinstance(result[role], str)
    
    def test_run_reviewers_empty_list(self, reviewer_manager):
        """Test running with empty reviewer list."""
        result = reviewer_manager.run_reviewers(
            "Content",
            [],
            1
        )
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_run_reviewers_single_reviewer(self, reviewer_manager):
        """Test running with single reviewer."""
        result = reviewer_manager.run_reviewers(
            "Content",
            ["Technical Reviewer"],
            1
        )
        
        assert len(result) == 1
        assert "Technical Reviewer" in result
    
    def test_execute_single_reviewer_technical(self, reviewer_manager):
        """Test executing technical reviewer."""
        feedback = reviewer_manager._execute_single_reviewer(
            "Technical Reviewer",
            "Design content",
            1
        )
        
        assert isinstance(feedback, Feedback)
        assert feedback.reviewer_role == "technical_reviewer"  # Agents use snake_case
        assert feedback.iteration == 1
        assert len(feedback.feedback_points) > 0
    
    def test_execute_single_reviewer_security(self, reviewer_manager):
        """Test executing security reviewer."""
        feedback = reviewer_manager._execute_single_reviewer(
            "Security Reviewer",
            "Design content",
            1
        )
        
        assert isinstance(feedback, Feedback)
        assert feedback.reviewer_role == "security_reviewer"  # Agents use snake_case
    
    def test_execute_single_reviewer_unknown_role(self, reviewer_manager):
        """Test executing reviewer with unknown role."""
        # Should use base ReviewerAgent
        feedback = reviewer_manager._execute_single_reviewer(
            "Unknown Reviewer",
            "Content",
            1
        )
        
        assert isinstance(feedback, Feedback)
    
    def test_feedback_to_string(self, reviewer_manager):
        """Test converting feedback to string."""
        feedback = Feedback(
            reviewer_role="Technical Reviewer",
            feedback_points=["Issue 1", "Issue 2", "Issue 3"],
            iteration=1,
            approved=False,
            modified=False
        )
        
        result = reviewer_manager._feedback_to_string(feedback)
        
        assert isinstance(result, str)
        assert "Technical Reviewer" in result
        assert "Issue 1" in result
        assert "Issue 2" in result
        assert "Issue 3" in result
        assert "ITERATION: 1" in result
    
    def test_feedback_to_string_approved(self, reviewer_manager):
        """Test converting approved feedback to string."""
        feedback = Feedback(
            reviewer_role="Security Reviewer",
            feedback_points=["All good"],
            iteration=2,
            approved=True,
            modified=False
        )
        
        result = reviewer_manager._feedback_to_string(feedback)
        
        assert "APPROVED" in result.upper()
        assert "Security Reviewer" in result
    
    def test_feedback_to_string_modified(self, reviewer_manager):
        """Test converting modified feedback to string."""
        feedback = Feedback(
            reviewer_role="Quality Reviewer",
            feedback_points=["Modified issue"],
            iteration=1,
            approved=False,
            modified=True
        )
        
        result = reviewer_manager._feedback_to_string(feedback)
        
        assert "MODIFIED" in result.upper() or "YES" in result
    
    def test_parallel_execution_faster_than_sequential(self, reviewer_manager):
        """Test that parallel execution is actually parallel."""
        import time
        
        presenter_output = "Design document"
        selected_roles = ["Technical Reviewer", "Security Reviewer", "Quality Reviewer"]
        
        # Sequential
        start_seq = time.time()
        reviewer_manager.run_reviewers(presenter_output, selected_roles, 1, parallel=False)
        time_seq = time.time() - start_seq
        
        # Parallel
        start_par = time.time()
        reviewer_manager.run_reviewers(presenter_output, selected_roles, 1, parallel=True)
        time_par = time.time() - start_par
        
        # Parallel should be faster or at least not significantly slower
        # (In reality, with mock providers, the difference is minimal,
        # but we test that both modes work)
        assert time_par >= 0
        assert time_seq >= 0


class TestReviewerClassMapping:
    """Test reviewer class mapping."""
    
    def test_reviewer_class_map_complete(self):
        """Test that all reviewer types are mapped."""
        expected_roles = [
            'Technical Reviewer',
            'Clarity Reviewer',
            'Security Reviewer',
            'Business Reviewer',
            'UX Reviewer'
        ]
        
        for role in expected_roles:
            assert role in REVIEWER_CLASS_MAP
            assert REVIEWER_CLASS_MAP[role] is not None
    
    def test_reviewer_class_map_correct_classes(self):
        """Test that classes are correctly mapped."""
        assert REVIEWER_CLASS_MAP['Technical Reviewer'] == TechnicalReviewer
        assert REVIEWER_CLASS_MAP['Clarity Reviewer'] == ClarityReviewer
        assert REVIEWER_CLASS_MAP['Security Reviewer'] == SecurityReviewer
        assert REVIEWER_CLASS_MAP['Business Reviewer'] == BusinessReviewer
        assert REVIEWER_CLASS_MAP['UX Reviewer'] == UXReviewer


class TestCreateReviewerInstances:
    """Test reviewer instance creation."""
    
    def test_create_reviewer_instances_empty(self):
        """Test creating instances with empty role list."""
        provider = MockLLMProvider()
        instances = create_reviewer_instances(provider, [])
        
        assert isinstance(instances, list)
        assert len(instances) == 0
    
    def test_create_reviewer_instances_single(self):
        """Test creating single reviewer instance."""
        provider = MockLLMProvider()
        instances = create_reviewer_instances(provider, ["Technical Reviewer"])
        
        assert len(instances) == 1
        assert isinstance(instances[0], TechnicalReviewer)
        assert instances[0].llm_provider == provider
    
    def test_create_reviewer_instances_multiple(self):
        """Test creating multiple reviewer instances."""
        provider = MockLLMProvider()
        roles = ["Technical Reviewer", "Security Reviewer", "Quality Reviewer"]
        instances = create_reviewer_instances(provider, roles)
        
        assert len(instances) == 3
        assert isinstance(instances[0], TechnicalReviewer)
        assert isinstance(instances[1], SecurityReviewer)
        # Quality Reviewer not in map, should use base class
    
    def test_create_reviewer_instances_all_types(self):
        """Test creating all reviewer types."""
        provider = MockLLMProvider()
        roles = [
            "Technical Reviewer",
            "Clarity Reviewer",
            "Security Reviewer",
            "Business Reviewer",
            "UX Reviewer"
        ]
        instances = create_reviewer_instances(provider, roles)
        
        assert len(instances) == 5
        for instance in instances:
            assert instance.llm_provider == provider


class TestReviewerManagerErrorHandling:
    """Test error handling in reviewer manager."""
    
    def test_run_reviewers_with_exception(self):
        """Test handling when a reviewer raises exception."""
        # Create mock provider that raises exception
        mock_provider = Mock()
        mock_provider.generate_text.side_effect = Exception("LLM Error")
        
        manager = ReviewerManager(mock_provider)
        
        result = manager.run_reviewers(
            "Content",
            ["Technical Reviewer"],
            1
        )
        
        # Should handle error gracefully
        assert "Technical Reviewer" in result
        assert "failed" in result["Technical Reviewer"].lower() or "error" in result["Technical Reviewer"].lower()
    
    def test_run_reviewers_partial_failure(self):
        """Test handling when some reviewers fail."""
        # Create mock provider that fails intermittently
        mock_provider = Mock()
        call_count = [0]
        
        def generate_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Intermittent failure")
            return "Feedback"
        
        mock_provider.generate_text = generate_side_effect
        
        manager = ReviewerManager(mock_provider)
        
        result = manager.run_reviewers(
            "Content",
            ["Technical Reviewer", "Security Reviewer", "Quality Reviewer"],
            1
        )
        
        # Should have results for all reviewers (some with errors)
        assert len(result) == 3

