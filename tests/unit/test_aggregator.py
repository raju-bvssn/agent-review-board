"""Unit tests for aggregator agent."""

import pytest
from unittest.mock import Mock, MagicMock
from app.orchestration.aggregator_agent import (
    AggregatorAgent,
    detect_conflicts,
    identify_consensus,
    extract_required_changes
)
from app.llm.mock_provider import MockLLMProvider


class TestAggregatorAgent:
    """Test suite for AggregatorAgent."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock LLM provider."""
        return MockLLMProvider()
    
    @pytest.fixture
    def aggregator(self, mock_provider):
        """Create aggregator agent."""
        return AggregatorAgent(mock_provider)
    
    def test_aggregator_initialization(self, mock_provider):
        """Test aggregator initialization."""
        aggregator = AggregatorAgent(mock_provider)
        assert aggregator.llm_provider == mock_provider
        assert aggregator.temperature == 0.3
        assert aggregator.max_tokens == 2000
    
    def test_aggregator_custom_params(self, mock_provider):
        """Test aggregator with custom parameters."""
        aggregator = AggregatorAgent(
            mock_provider,
            temperature=0.5,
            max_tokens=1500
        )
        assert aggregator.temperature == 0.5
        assert aggregator.max_tokens == 1500
    
    def test_aggregate_empty_feedback(self, aggregator):
        """Test aggregation with empty feedback."""
        result = aggregator.aggregate({})
        assert "No reviewer feedback available" in result
    
    def test_aggregate_single_reviewer(self, aggregator):
        """Test aggregation with single reviewer."""
        feedback = {
            "Technical Reviewer": "APPROVE: Design is solid."
        }
        result = aggregator.aggregate(feedback)
        assert result  # Should return something
        assert isinstance(result, str)
    
    def test_aggregate_multiple_reviewers(self, aggregator):
        """Test aggregation with multiple reviewers."""
        feedback = {
            "Technical Reviewer": "APPROVE: Architecture is sound.",
            "Security Reviewer": "NEEDS REVISION: Add input validation.",
            "Quality Reviewer": "APPROVE: Code quality is good."
        }
        result = aggregator.aggregate(feedback)
        assert result
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_aggregate_with_presenter_output(self, aggregator):
        """Test aggregation with presenter output for context."""
        feedback = {
            "Technical Reviewer": "Good design"
        }
        presenter_output = "This is a microservices architecture..."
        result = aggregator.aggregate(feedback, presenter_output)
        assert result
        assert isinstance(result, str)
    
    def test_fallback_aggregation_empty(self, aggregator):
        """Test fallback aggregation with empty feedback."""
        result = aggregator._fallback_aggregation({})
        assert "BOARD DECISION" in result
        assert "TOTAL REVIEWERS: 0" in result
    
    def test_fallback_aggregation_with_approvals(self, aggregator):
        """Test fallback aggregation with approvals."""
        feedback = {
            "Reviewer1": "APPROVE: Excellent work",
            "Reviewer2": "APPROVE: Well done",
            "Reviewer3": "APPROVE: Great job"
        }
        result = aggregator._fallback_aggregation(feedback)
        assert "BOARD DECISION" in result
        assert "Approvals: 3" in result
        assert "APPROVE" in result.upper()
    
    def test_fallback_aggregation_with_rejections(self, aggregator):
        """Test fallback aggregation with rejections."""
        feedback = {
            "Reviewer1": "REJECT: Major issues found",
            "Reviewer2": "REJECT: Unacceptable quality",
            "Reviewer3": "NEEDS REVISION: Many problems"
        }
        result = aggregator._fallback_aggregation(feedback)
        assert "BOARD DECISION" in result
        assert "Rejections:" in result or "REVISION" in result.upper()
    
    def test_fallback_aggregation_mixed_verdicts(self, aggregator):
        """Test fallback aggregation with mixed verdicts."""
        feedback = {
            "Reviewer1": "APPROVE: Good",
            "Reviewer2": "REJECT: Bad",
            "Reviewer3": "NEEDS REVISION: Ok"
        }
        result = aggregator._fallback_aggregation(feedback)
        assert "BOARD DECISION" in result
        assert "Approvals: 1" in result
        assert "Rejections: 1" in result


class TestConflictDetection:
    """Test conflict detection functionality."""
    
    def test_detect_conflicts_no_conflict(self):
        """Test conflict detection with no conflicts."""
        feedback = {
            "Reviewer1": "APPROVE: Good design",
            "Reviewer2": "APPROVE: Excellent work",
            "Reviewer3": "APPROVE: Well done"
        }
        conflicts = detect_conflicts(feedback)
        assert len(conflicts) == 0
    
    def test_detect_conflicts_with_conflict(self):
        """Test conflict detection with conflicts."""
        feedback = {
            "Reviewer1": "APPROVE: Design is solid",
            "Reviewer2": "REJECT: Major architectural flaws"
        }
        conflicts = detect_conflicts(feedback)
        assert len(conflicts) > 0
        assert "Conflict" in conflicts[0]
    
    def test_detect_conflicts_mixed_verdicts(self):
        """Test conflict detection with mixed verdicts."""
        feedback = {
            "Technical": "APPROVE: Architecture is good",
            "Security": "REJECT: Security vulnerabilities found",
            "Quality": "APPROVE: Code quality acceptable"
        }
        conflicts = detect_conflicts(feedback)
        assert len(conflicts) > 0


class TestConsensusIdentification:
    """Test consensus identification functionality."""
    
    def test_identify_consensus_single_reviewer(self):
        """Test consensus with single reviewer."""
        feedback = {
            "Reviewer1": "Good design with clear architecture"
        }
        consensus = identify_consensus(feedback)
        assert isinstance(consensus, list)
        # Single reviewer = no consensus possible
        assert len(consensus) == 0
    
    def test_identify_consensus_multiple_reviewers(self):
        """Test consensus with multiple reviewers."""
        feedback = {
            "Reviewer1": "Good design and architecture",
            "Reviewer2": "Well designed system with good architecture",
            "Reviewer3": "Solid architecture and design patterns"
        }
        consensus = identify_consensus(feedback)
        assert isinstance(consensus, list)
        # Should find common words like "design" and "architecture"
        # (implementation may vary)
    
    def test_identify_consensus_no_overlap(self):
        """Test consensus with no word overlap."""
        feedback = {
            "Reviewer1": "Database schema needs work",
            "Reviewer2": "API endpoints are unclear",
            "Reviewer3": "Frontend responsiveness poor"
        }
        consensus = identify_consensus(feedback)
        assert isinstance(consensus, list)


class TestRequiredChangesExtraction:
    """Test required changes extraction."""
    
    def test_extract_required_changes_none(self):
        """Test extraction when no required changes section."""
        feedback = "This is general feedback without structure."
        changes = extract_required_changes(feedback)
        assert isinstance(changes, list)
        assert len(changes) == 0
    
    def test_extract_required_changes_with_list(self):
        """Test extraction with required changes list."""
        feedback = """
        REQUIRED CHANGES:
        1. Add input validation
        2. Implement error handling
        3. Update documentation
        
        OPTIONAL IMPROVEMENTS:
        - Could add caching
        """
        changes = extract_required_changes(feedback)
        assert isinstance(changes, list)
        assert len(changes) >= 3
        assert any("validation" in change.lower() for change in changes)
    
    def test_extract_required_changes_with_bullets(self):
        """Test extraction with bullet points."""
        feedback = """
        REQUIRED CHANGES:
        - Fix SQL injection vulnerability
        - Add authentication middleware
        - Implement rate limiting
        """
        changes = extract_required_changes(feedback)
        assert isinstance(changes, list)
        assert len(changes) >= 3
    
    def test_extract_required_changes_stops_at_next_section(self):
        """Test extraction stops at next section."""
        feedback = """
        REQUIRED CHANGES:
        1. First change
        2. Second change
        
        OPTIONAL IMPROVEMENTS:
        1. This should not be included
        """
        changes = extract_required_changes(feedback)
        assert isinstance(changes, list)
        # Should only include required changes, not optional ones
        assert len(changes) == 2


class TestAggregatorLLMFallback:
    """Test aggregator behavior when LLM fails."""
    
    def test_aggregate_llm_failure_uses_fallback(self):
        """Test that aggregator uses fallback when LLM fails."""
        # Create mock provider that raises exception
        mock_provider = Mock()
        mock_provider.generate_text.side_effect = Exception("LLM Error")
        
        aggregator = AggregatorAgent(mock_provider)
        
        feedback = {
            "Reviewer1": "APPROVE: Good work",
            "Reviewer2": "APPROVE: Well done"
        }
        
        result = aggregator.aggregate(feedback)
        
        # Should use fallback, not raise exception
        assert result
        assert "BOARD DECISION" in result
        assert "Fallback Mode" in result

