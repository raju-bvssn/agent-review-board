"""Unit tests for confidence model."""

import pytest
from app.orchestration.confidence_model import (
    calculate_confidence,
    get_confidence_level,
    is_ready_for_finalization,
    CONFIDENCE_THRESHOLD,
    _calculate_agreement_ratio,
    _calculate_sentiment_consistency,
    _calculate_severity_score,
    _calculate_feedback_quality
)


class TestConfidenceCalculation:
    """Test suite for confidence score calculation."""
    
    def test_calculate_confidence_empty_feedback(self):
        """Test confidence calculation with no feedback."""
        result = calculate_confidence({}, "")
        assert result == 0.5  # Neutral confidence
    
    def test_calculate_confidence_single_reviewer(self):
        """Test confidence calculation with single reviewer."""
        feedback = {
            "Technical Reviewer": "APPROVE: The design is solid and well-structured."
        }
        result = calculate_confidence(feedback, "Approved")
        assert 0.0 <= result <= 1.0
        assert result > 0.5  # Should be positive
    
    def test_calculate_confidence_high_agreement(self):
        """Test confidence with high reviewer agreement."""
        feedback = {
            "Technical Reviewer": "APPROVE: Excellent design, no issues found.",
            "Security Reviewer": "APPROVE: Security measures are good.",
            "Quality Reviewer": "APPROVE: Code quality is high."
        }
        result = calculate_confidence(feedback, "Approved")
        assert result > 0.7  # High agreement = high confidence
    
    def test_calculate_confidence_with_conflicts(self):
        """Test confidence with conflicting reviewers."""
        feedback = {
            "Technical Reviewer": "APPROVE: Design is good.",
            "Security Reviewer": "REJECT: Major security vulnerabilities found.",
            "Quality Reviewer": "APPROVE: Quality is acceptable."
        }
        result = calculate_confidence(feedback, "Mixed")
        assert result < 0.8  # Conflicts = lower confidence (but still moderate)
    
    def test_calculate_confidence_with_critical_issues(self):
        """Test confidence with critical issues."""
        feedback = {
            "Technical Reviewer": "CRITICAL: Database connection leak found. HIGH: Poor error handling.",
            "Security Reviewer": "CRITICAL: SQL injection vulnerability. MEDIUM: Missing input validation."
        }
        result = calculate_confidence(feedback, "Issues")
        assert result < 0.9  # Critical issues reduce confidence somewhat
    
    def test_calculate_confidence_with_minor_issues(self):
        """Test confidence with only minor issues."""
        feedback = {
            "Technical Reviewer": "LOW: Minor typo in comments.",
            "Quality Reviewer": "LOW: Could add more test coverage."
        }
        result = calculate_confidence(feedback, "Minor issues")
        assert result > 0.7  # Minor issues = still high confidence


class TestAgreementRatio:
    """Test agreement ratio calculation."""
    
    def test_agreement_single_reviewer(self):
        """Test agreement with single reviewer."""
        feedback = {"Reviewer1": "APPROVE"}
        result = _calculate_agreement_ratio(feedback)
        assert result == 1.0  # Single reviewer = perfect agreement
    
    def test_agreement_all_approve(self):
        """Test agreement when all approve."""
        feedback = {
            "Reviewer1": "APPROVE: Good",
            "Reviewer2": "APPROVE: Excellent",
            "Reviewer3": "APPROVE: Great"
        }
        result = _calculate_agreement_ratio(feedback)
        assert result > 0.7  # High agreement expected
    
    def test_agreement_all_reject(self):
        """Test agreement when all reject."""
        feedback = {
            "Reviewer1": "REJECT: Bad design",
            "Reviewer2": "REJECT: Poor quality",
            "Reviewer3": "REJECT: Major issues"
        }
        result = _calculate_agreement_ratio(feedback)
        assert result > 0.7  # High agreement (even if negative)
    
    def test_agreement_mixed_verdicts(self):
        """Test agreement with mixed verdicts."""
        feedback = {
            "Reviewer1": "APPROVE: Good",
            "Reviewer2": "REJECT: Bad",
            "Reviewer3": "NEEDS REVISION: Ok but needs work"
        }
        result = _calculate_agreement_ratio(feedback)
        assert result < 0.7  # Low agreement


class TestSentimentConsistency:
    """Test sentiment consistency calculation."""
    
    def test_sentiment_all_positive(self):
        """Test sentiment with all positive feedback."""
        feedback = {
            "Reviewer1": "Excellent design, good architecture, strong implementation",
            "Reviewer2": "Good structure, clear code, well documented"
        }
        result = _calculate_sentiment_consistency(feedback)
        assert result > 0.5  # Consistent positive sentiment
    
    def test_sentiment_all_negative(self):
        """Test sentiment with all negative feedback."""
        feedback = {
            "Reviewer1": "Issue with error handling, missing validations, unclear logic",
            "Reviewer2": "Problem with security, weak authentication, critical bug"
        }
        result = _calculate_sentiment_consistency(feedback)
        assert result > 0.5  # Consistent negative sentiment
    
    def test_sentiment_mixed(self):
        """Test sentiment with mixed feedback."""
        feedback = {
            "Reviewer1": "Excellent design but critical security issue",
            "Reviewer2": "Good approach"
        }
        result = _calculate_sentiment_consistency(feedback)
        assert 0.0 <= result <= 1.0


class TestSeverityScore:
    """Test severity score calculation."""
    
    def test_severity_no_issues(self):
        """Test severity with no issues."""
        feedback = {
            "Reviewer1": "All good, no issues found",
            "Reviewer2": "Everything looks perfect"
        }
        result = _calculate_severity_score(feedback)
        assert result == 1.0  # No issues = perfect score
    
    def test_severity_only_low_issues(self):
        """Test severity with only low severity issues."""
        feedback = {
            "Reviewer1": "LOW: Minor formatting issue",
            "Reviewer2": "LOW: Small optimization possible"
        }
        result = _calculate_severity_score(feedback)
        assert result > 0.8  # Low issues = still high score
    
    def test_severity_critical_issues(self):
        """Test severity with critical issues."""
        feedback = {
            "Reviewer1": "CRITICAL: Data corruption risk",
            "Reviewer2": "CRITICAL: Security vulnerability"
        }
        result = _calculate_severity_score(feedback)
        assert result < 0.9  # Critical issues reduce score
    
    def test_severity_mixed_levels(self):
        """Test severity with mixed issue levels."""
        feedback = {
            "Reviewer1": "CRITICAL: Major bug. HIGH: Performance issue. MEDIUM: Code smell.",
            "Reviewer2": "LOW: Minor typo. MEDIUM: Could be refactored."
        }
        result = _calculate_severity_score(feedback)
        assert 0.5 <= result <= 0.9  # Mixed severity


class TestFeedbackQuality:
    """Test feedback quality calculation."""
    
    def test_quality_too_short(self):
        """Test quality with very short feedback."""
        feedback = {"Reviewer1": "Ok"}
        result = _calculate_feedback_quality(feedback)
        assert result < 0.5  # Too short = low quality
    
    def test_quality_well_structured(self):
        """Test quality with well-structured feedback."""
        feedback = {
            "Reviewer1": """
            VERDICT: APPROVE
            FINDINGS: The design is solid and follows best practices.
            SUGGESTIONS: Consider adding more error handling for edge cases.
            """
        }
        result = _calculate_feedback_quality(feedback)
        assert result > 0.7  # Well structured = high quality
    
    def test_quality_missing_verdict(self):
        """Test quality with missing verdict."""
        feedback = {
            "Reviewer1": "The code looks okay but could use some improvements here and there."
        }
        result = _calculate_feedback_quality(feedback)
        assert result < 0.8  # Missing structure = lower quality


class TestConfidenceLevel:
    """Test confidence level conversion."""
    
    def test_confidence_level_very_high(self):
        """Test very high confidence level."""
        assert get_confidence_level(0.95) == "VERY HIGH"
    
    def test_confidence_level_high(self):
        """Test high confidence level."""
        assert get_confidence_level(0.85) == "HIGH"
    
    def test_confidence_level_medium(self):
        """Test medium confidence level."""
        assert get_confidence_level(0.75) == "MEDIUM"
    
    def test_confidence_level_low(self):
        """Test low confidence level."""
        assert get_confidence_level(0.55) == "LOW"
    
    def test_confidence_level_very_low(self):
        """Test very low confidence level."""
        assert get_confidence_level(0.30) == "VERY LOW"


class TestFinalizationReadiness:
    """Test finalization readiness check."""
    
    def test_ready_for_finalization_above_threshold(self):
        """Test readiness when confidence above threshold."""
        assert is_ready_for_finalization(0.85) is True
    
    def test_ready_for_finalization_at_threshold(self):
        """Test readiness when confidence at threshold."""
        assert is_ready_for_finalization(CONFIDENCE_THRESHOLD) is True
    
    def test_ready_for_finalization_below_threshold(self):
        """Test readiness when confidence below threshold."""
        assert is_ready_for_finalization(0.75) is False
    
    def test_ready_for_finalization_custom_threshold(self):
        """Test readiness with custom threshold."""
        assert is_ready_for_finalization(0.75, threshold=0.70) is True
        assert is_ready_for_finalization(0.65, threshold=0.70) is False

