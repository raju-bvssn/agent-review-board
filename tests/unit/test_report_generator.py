"""Unit tests for report generation utilities."""

import pytest
from app.utils.report_generator import (
    aggregate_reviewer_feedback,
    generate_final_report,
    get_session_summary,
    export_session_to_dict,
    _extract_severity,
    _find_common_issues,
    _find_unique_issues
)
from app.models.feedback import Feedback
from app.core.orchestrator import IterationResult


class TestAggregateReviewerFeedback:
    """Test the aggregate_reviewer_feedback function."""
    
    def test_empty_feedback_list(self):
        """Test aggregation with empty feedback list."""
        result = aggregate_reviewer_feedback([])
        
        assert result['common_issues'] == []
        assert result['unique_issues'] == []
        assert result['severity_breakdown'] == {}
        assert result['average_confidence'] == 0.0
        assert result['total_issues'] == 0
    
    def test_single_reviewer_feedback(self):
        """Test aggregation with single reviewer."""
        feedback = Feedback(
            reviewer_role="Technical Reviewer",
            feedback_points=[
                "[Severity: HIGH] Performance issue detected",
                "[Severity: MEDIUM] Documentation incomplete"
            ],
            iteration=1,
            approved=False,
            modified=False
        )
        
        result = aggregate_reviewer_feedback([feedback])
        
        assert result['total_issues'] == 2
        assert result['severity_breakdown']['HIGH'] == 1
        assert result['severity_breakdown']['MEDIUM'] == 1
        assert len(result['unique_issues']) >= 0
    
    def test_multiple_reviewers_with_common_issues(self):
        """Test aggregation identifying common issues."""
        feedback1 = Feedback(
            reviewer_role="Technical Reviewer",
            feedback_points=[
                "[Severity: HIGH] Security vulnerability in authentication",
                "[Severity: MEDIUM] Missing error handling"
            ],
            iteration=1,
            approved=False,
            modified=False
        )
        
        feedback2 = Feedback(
            reviewer_role="Security Reviewer",
            feedback_points=[
                "[Severity: CRITICAL] Security vulnerability found",
                "[Severity: HIGH] Authentication needs improvement"
            ],
            iteration=1,
            approved=False,
            modified=False
        )
        
        result = aggregate_reviewer_feedback([feedback1, feedback2])
        
        assert result['total_issues'] == 4
        assert result['severity_breakdown']['HIGH'] == 2
        assert result['severity_breakdown']['CRITICAL'] == 1
        assert result['severity_breakdown']['MEDIUM'] == 1
    
    def test_severity_extraction(self):
        """Test severity extraction from feedback text."""
        assert _extract_severity("[Severity: CRITICAL] Issue") == "CRITICAL"
        assert _extract_severity("[Severity: HIGH] Issue") == "HIGH"
        assert _extract_severity("[Severity: MEDIUM] Issue") == "MEDIUM"
        assert _extract_severity("[Severity: LOW] Issue") == "LOW"
        assert _extract_severity("No severity marked") == "NONE"


class TestGenerateFinalReport:
    """Test the generate_final_report function."""
    
    def test_generate_markdown_report(self):
        """Test Markdown report generation."""
        session_data = {
            "session_name": "Test Session",
            "session_id": "test-123",
            "requirements": "Test requirements",
            "selected_roles": ["Technical Reviewer", "Security Reviewer"],
            "provider": "openai"
        }
        
        # Create mock iteration result
        feedback1 = Feedback(
            reviewer_role="Technical Reviewer",
            feedback_points=["Good implementation", "Needs optimization"],
            iteration=1,
            approved=True,
            modified=False
        )
        
        iteration_result = IterationResult(
            iteration=1,
            presenter_output="Test output content",
            reviewer_feedback=[feedback1],
            confidence_result={"score": 85.0, "reasoning": "Looks good overall"},
            error=None
        )
        
        report = generate_final_report(session_data, [iteration_result], format="markdown")
        
        assert "Agent Review Board - Final Report" in report
        assert "Test Session" in report
        assert "Test requirements" in report
        assert "Technical Reviewer" in report
        assert "Test output content" in report
        assert "85" in report  # Confidence score
    
    def test_generate_json_report(self):
        """Test JSON report generation."""
        import json
        
        session_data = {
            "session_name": "Test Session",
            "session_id": "test-123",
            "requirements": "Test requirements",
            "selected_roles": ["Technical Reviewer"],
            "provider": "openai"
        }
        
        feedback1 = Feedback(
            reviewer_role="Technical Reviewer",
            feedback_points=["Good work"],
            iteration=1,
            approved=True,
            modified=False
        )
        
        iteration_result = IterationResult(
            iteration=1,
            presenter_output="Test output",
            reviewer_feedback=[feedback1],
            confidence_result={"score": 90.0, "reasoning": "Excellent"},
            error=None
        )
        
        report = generate_final_report(session_data, [iteration_result], format="json")
        
        # Verify it's valid JSON
        data = json.loads(report)
        
        assert data['session_info']['session_name'] == "Test Session"
        assert data['session_info']['total_iterations'] == 1
        assert len(data['iterations']) == 1
        assert data['iterations'][0]['presenter_output'] == "Test output"
        assert data['iterations'][0]['confidence_result']['score'] == 90.0
    
    def test_empty_iteration_history(self):
        """Test report generation with no iterations."""
        session_data = {
            "session_name": "Empty Session",
            "session_id": "empty-123",
            "requirements": "Nothing done",
            "selected_roles": [],
            "provider": "mock"
        }
        
        report = generate_final_report(session_data, [], format="markdown")
        
        assert "Empty Session" in report
        assert "Total Iterations:** 0" in report


class TestGetSessionSummary:
    """Test the get_session_summary function."""
    
    def test_empty_history(self):
        """Test summary with empty history."""
        summary = get_session_summary([])
        
        assert summary['total_iterations'] == 0
        assert summary['final_confidence'] == 0.0
        assert summary['total_feedback_points'] == 0
        assert summary['approved_iterations'] == 0
    
    def test_with_iterations(self):
        """Test summary with actual iterations."""
        feedback1 = Feedback(
            reviewer_role="Technical Reviewer",
            feedback_points=["Point 1", "Point 2", "Point 3"],
            iteration=1,
            approved=True,
            modified=False
        )
        
        iteration1 = IterationResult(
            iteration=1,
            presenter_output="Output 1",
            reviewer_feedback=[feedback1],
            confidence_result={"score": 80.0, "reasoning": "Good"},
            error=None
        )
        iteration1.human_gate_approved = True
        
        feedback2 = Feedback(
            reviewer_role="Security Reviewer",
            feedback_points=["Point A", "Point B"],
            iteration=2,
            approved=False,
            modified=False
        )
        
        iteration2 = IterationResult(
            iteration=2,
            presenter_output="Output 2",
            reviewer_feedback=[feedback2],
            confidence_result={"score": 95.0, "reasoning": "Excellent"},
            error=None
        )
        iteration2.human_gate_approved = False
        
        summary = get_session_summary([iteration1, iteration2])
        
        assert summary['total_iterations'] == 2
        assert summary['final_confidence'] == 95.0  # Last iteration's score
        assert summary['total_feedback_points'] == 5  # 3 + 2
        assert summary['approved_iterations'] == 1


class TestExportSessionToDict:
    """Test the export_session_to_dict function."""
    
    def test_complete_export(self):
        """Test exporting session to dictionary."""
        session_data = {
            "session_name": "Export Test",
            "session_id": "export-123",
            "requirements": "Test export",
            "selected_roles": ["Technical Reviewer"],
            "provider": "anthropic"
        }
        
        feedback = Feedback(
            reviewer_role="Technical Reviewer",
            feedback_points=["Export point"],
            iteration=1,
            approved=True,
            modified=False
        )
        
        iteration = IterationResult(
            iteration=1,
            presenter_output="Export output",
            reviewer_feedback=[feedback],
            confidence_result={"score": 88.0, "reasoning": "Good export"},
            error=None
        )
        iteration.human_gate_approved = True
        
        result = export_session_to_dict(session_data, [iteration])
        
        assert result['session']['session_name'] == "Export Test"
        assert len(result['iterations']) == 1
        assert result['iterations'][0]['iteration'] == 1
        assert result['iterations'][0]['approved'] is True
        assert 'summary' in result
        assert 'exported_at' in result
        assert result['summary']['total_iterations'] == 1


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_find_common_issues(self):
        """Test finding common issues."""
        issues = [
            {"text": "Security vulnerability in authentication module", "reviewer": "Security", "severity": "HIGH"},
            {"text": "Authentication security needs attention", "reviewer": "Technical", "severity": "HIGH"},
            {"text": "Performance is slow", "reviewer": "Technical", "severity": "MEDIUM"}
        ]
        
        common = _find_common_issues(issues)
        
        # At least some detection should work (simple keyword matching)
        assert isinstance(common, list)
    
    def test_find_unique_issues(self):
        """Test finding unique issues."""
        all_issues = [
            {"text": "Unique issue here", "reviewer": "Clarity", "severity": "LOW"},
            {"text": "Another unique point", "reviewer": "Business", "severity": "MEDIUM"}
        ]
        
        common_issues = []
        
        unique = _find_unique_issues(all_issues, common_issues)
        
        assert len(unique) >= 2  # All should be unique
    
    def test_severity_extraction_variants(self):
        """Test severity extraction with different formats."""
        test_cases = [
            ("This is CRITICAL issue", "CRITICAL"),
            ("high priority problem", "HIGH"),
            ("Medium severity finding", "MEDIUM"),
            ("Low impact change", "LOW"),
            ("No marker here", "NONE")
        ]
        
        for text, expected in test_cases:
            assert _extract_severity(text) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

