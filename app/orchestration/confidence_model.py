"""Confidence scoring model for multi-agent review convergence."""

from typing import Dict, List, Optional
import re


# Confidence threshold for iteration convergence
CONFIDENCE_THRESHOLD = 0.82


def calculate_confidence(
    reviewer_feedback: Dict[str, str],
    aggregated_feedback: str,
    previous_feedback: Dict[str, str] = None
) -> float:
    """Calculate confidence score based on reviewer agreement and quality.
    
    This function analyzes feedback from all reviewers to determine how
    confident we are in the current iteration's quality. Higher confidence
    indicates better agreement and fewer critical issues.
    
    Scoring factors (when no previous feedback):
    - Agreement ratio: How much reviewers agree (40%)
    - Sentiment consistency: Similar positive/negative tones (25%)
    - Issue severity: Fewer critical issues = higher confidence (25%)
    - Feedback quality: Length and detail level (10%)
    
    Scoring factors (with previous feedback):
    - Agreement ratio: How much reviewers agree (30%)
    - Sentiment consistency: Similar positive/negative tones (20%)
    - Issue severity: Fewer critical issues = higher confidence (20%)
    - Feedback quality: Length and detail level (10%)
    - Improvement tracking: Issues fixed vs new issues (20%)
    
    Args:
        reviewer_feedback: Dictionary mapping reviewer role to feedback string
        aggregated_feedback: Unified feedback from aggregator
        previous_feedback: Optional previous iteration feedback for improvement tracking
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not reviewer_feedback or len(reviewer_feedback) == 0:
        return 0.5  # Neutral confidence with no feedback
    
    # Check if this is an iterative review with improvement tracking
    has_improvement_data = previous_feedback and _has_improvement_tracking(reviewer_feedback)
    
    if has_improvement_data:
        # Iteration 2+: Include improvement tracking
        # Factor 1: Agreement ratio (30% weight - reduced)
        agreement_score = _calculate_agreement_ratio(reviewer_feedback)
        
        # Factor 2: Sentiment consistency (20% weight - reduced)
        sentiment_score = _calculate_sentiment_consistency(reviewer_feedback)
        
        # Factor 3: Issue severity (20% weight - reduced)
        severity_score = _calculate_severity_score(reviewer_feedback)
        
        # Factor 4: Feedback quality (10% weight)
        quality_score = _calculate_feedback_quality(reviewer_feedback)
        
        # Factor 5: Improvement tracking (20% weight - NEW)
        improvement_score = _calculate_improvement_score(reviewer_feedback)
        
        # Weighted average with improvement tracking
        confidence = (
            agreement_score * 0.30 +
            sentiment_score * 0.20 +
            severity_score * 0.20 +
            quality_score * 0.10 +
            improvement_score * 0.20
        )
    else:
        # Iteration 1: Original scoring
        # Factor 1: Agreement ratio (40% weight)
        agreement_score = _calculate_agreement_ratio(reviewer_feedback)
        
        # Factor 2: Sentiment consistency (25% weight)
        sentiment_score = _calculate_sentiment_consistency(reviewer_feedback)
        
        # Factor 3: Issue severity (25% weight)
        severity_score = _calculate_severity_score(reviewer_feedback)
        
        # Factor 4: Feedback quality (10% weight)
        quality_score = _calculate_feedback_quality(reviewer_feedback)
        
        # Weighted average
        confidence = (
            agreement_score * 0.40 +
            sentiment_score * 0.25 +
            severity_score * 0.25 +
            quality_score * 0.10
        )
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, confidence))


def _calculate_agreement_ratio(reviewer_feedback: Dict[str, str]) -> float:
    """Calculate how much reviewers agree with each other.
    
    Uses keyword overlap and verdict similarity.
    
    Args:
        reviewer_feedback: Reviewer feedback dictionary
        
    Returns:
        Agreement score (0.0 to 1.0)
    """
    if len(reviewer_feedback) < 2:
        return 1.0  # Single reviewer = perfect agreement
    
    feedback_list = list(reviewer_feedback.values())
    
    # Extract verdicts
    verdicts = []
    for feedback in feedback_list:
        feedback_upper = feedback.upper()
        if 'APPROVE' in feedback_upper and 'REJECT' not in feedback_upper:
            verdicts.append('approve')
        elif 'REJECT' in feedback_upper:
            verdicts.append('reject')
        elif 'NEEDS REVISION' in feedback_upper or 'NEEDS_REVISION' in feedback_upper:
            verdicts.append('revision')
        else:
            verdicts.append('neutral')
    
    # Calculate verdict agreement
    if verdicts:
        most_common_verdict = max(set(verdicts), key=verdicts.count)
        verdict_agreement = verdicts.count(most_common_verdict) / len(verdicts)
    else:
        verdict_agreement = 0.5
    
    # Calculate keyword overlap
    all_words = set()
    word_sets = []
    
    for feedback in feedback_list:
        words = set(re.findall(r'\b\w{4,}\b', feedback.lower()))  # Words 4+ chars
        word_sets.append(words)
        all_words.update(words)
    
    # Common words across all reviewers
    if len(word_sets) > 1 and all_words:
        common_words = set.intersection(*word_sets)
        keyword_overlap = len(common_words) / len(all_words) if all_words else 0.0
    else:
        keyword_overlap = 0.5
    
    # Combined agreement
    agreement = (verdict_agreement * 0.7) + (keyword_overlap * 0.3)
    
    return agreement


def _calculate_sentiment_consistency(reviewer_feedback: Dict[str, str]) -> float:
    """Calculate sentiment consistency across reviewers.
    
    Args:
        reviewer_feedback: Reviewer feedback dictionary
        
    Returns:
        Sentiment consistency score (0.0 to 1.0)
    """
    if len(reviewer_feedback) == 0:
        return 0.5
    
    # Count positive and negative indicators
    positive_counts = []
    negative_counts = []
    
    positive_keywords = ['good', 'excellent', 'strong', 'clear', 'well', 'approve', 'solid']
    negative_keywords = ['issue', 'problem', 'error', 'missing', 'unclear', 'weak', 'reject', 'critical']
    
    for feedback in reviewer_feedback.values():
        feedback_lower = feedback.lower()
        
        positive_count = sum(1 for word in positive_keywords if word in feedback_lower)
        negative_count = sum(1 for word in negative_keywords if word in feedback_lower)
        
        positive_counts.append(positive_count)
        negative_counts.append(negative_count)
    
    # Calculate variance in sentiment
    if positive_counts and negative_counts:
        avg_positive = sum(positive_counts) / len(positive_counts)
        avg_negative = sum(negative_counts) / len(negative_counts)
        
        # Low variance = high consistency
        positive_variance = sum((x - avg_positive) ** 2 for x in positive_counts) / len(positive_counts)
        negative_variance = sum((x - avg_negative) ** 2 for x in negative_counts) / len(negative_counts)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        max_variance = 10.0
        positive_consistency = 1.0 - min(positive_variance / max_variance, 1.0)
        negative_consistency = 1.0 - min(negative_variance / max_variance, 1.0)
        
        consistency = (positive_consistency + negative_consistency) / 2
        return consistency
    
    return 0.5


def _calculate_severity_score(reviewer_feedback: Dict[str, str]) -> float:
    """Calculate severity score (fewer critical issues = higher score).
    
    Args:
        reviewer_feedback: Reviewer feedback dictionary
        
    Returns:
        Severity score (0.0 to 1.0)
    """
    if len(reviewer_feedback) == 0:
        return 0.5
    
    # Count severity levels
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for feedback in reviewer_feedback.values():
        feedback_upper = feedback.upper()
        critical_count += feedback_upper.count('CRITICAL')
        high_count += feedback_upper.count('HIGH')
        medium_count += feedback_upper.count('MEDIUM')
        low_count += feedback_upper.count('LOW')
    
    # Total issues
    total_issues = critical_count + high_count + medium_count + low_count
    
    if total_issues == 0:
        return 1.0  # No issues = perfect score
    
    # Weighted penalty (critical issues are worse)
    penalty = (
        critical_count * 1.0 +
        high_count * 0.6 +
        medium_count * 0.3 +
        low_count * 0.1
    )
    
    # Normalize by number of reviewers
    avg_penalty = penalty / len(reviewer_feedback)
    
    # Convert penalty to score (less penalty = higher score)
    # Assume max 5 critical issues per reviewer as worst case
    max_penalty = 5.0
    severity_score = 1.0 - min(avg_penalty / max_penalty, 1.0)
    
    return severity_score


def _calculate_feedback_quality(reviewer_feedback: Dict[str, str]) -> float:
    """Calculate feedback quality based on length and detail.
    
    Args:
        reviewer_feedback: Reviewer feedback dictionary
        
    Returns:
        Quality score (0.0 to 1.0)
    """
    if len(reviewer_feedback) == 0:
        return 0.0
    
    quality_scores = []
    
    for feedback in reviewer_feedback.values():
        # Length indicator (not too short, not too verbose)
        length = len(feedback)
        if length < 50:
            length_score = length / 50  # Too short
        elif length > 2000:
            length_score = 1.0 - min((length - 2000) / 2000, 0.5)  # Too verbose
        else:
            length_score = 1.0  # Good length
        
        # Structure indicators
        has_verdict = 'VERDICT' in feedback.upper() or 'APPROVE' in feedback.upper() or 'REJECT' in feedback.upper()
        has_findings = 'FINDING' in feedback.upper() or 'ISSUE' in feedback.upper()
        has_suggestions = 'SUGGEST' in feedback.upper() or 'RECOMMEND' in feedback.upper()
        
        structure_score = (
            (0.4 if has_verdict else 0.0) +
            (0.3 if has_findings else 0.0) +
            (0.3 if has_suggestions else 0.0)
        )
        
        # Combined quality
        quality = (length_score * 0.4) + (structure_score * 0.6)
        quality_scores.append(quality)
    
    # Average quality across all reviewers
    return sum(quality_scores) / len(quality_scores)


def get_confidence_level(confidence: float) -> str:
    """Convert confidence score to human-readable level.
    
    Args:
        confidence: Confidence score (0.0 to 1.0)
        
    Returns:
        Confidence level string
    """
    if confidence >= 0.90:
        return "VERY HIGH"
    elif confidence >= 0.82:
        return "HIGH"
    elif confidence >= 0.70:
        return "MEDIUM"
    elif confidence >= 0.50:
        return "LOW"
    else:
        return "VERY LOW"


def is_ready_for_finalization(confidence: float, threshold: float = CONFIDENCE_THRESHOLD) -> bool:
    """Check if iteration quality is sufficient for finalization.
    
    Args:
        confidence: Current confidence score
        threshold: Minimum confidence required (default 0.82)
        
    Returns:
        True if ready for finalization, False otherwise
    """
    return confidence >= threshold


def _has_improvement_tracking(reviewer_feedback: Dict[str, str]) -> bool:
    """Check if reviewer feedback contains improvement tracking data.
    
    Improvement tracking includes markers like:
    - ✅ FIXED
    - ⚠️ PARTIALLY FIXED
    - ❌ NOT ADDRESSED
    - IMPROVEMENT TRACKING
    
    Args:
        reviewer_feedback: Dictionary of reviewer feedback
        
    Returns:
        True if improvement tracking is present, False otherwise
    """
    improvement_markers = ['FIXED:', 'PARTIALLY FIXED:', 'NOT ADDRESSED:', 'IMPROVEMENT TRACKING']
    
    for feedback in reviewer_feedback.values():
        feedback_upper = feedback.upper()
        if any(marker in feedback_upper for marker in improvement_markers):
            return True
    
    return False


def _calculate_improvement_score(reviewer_feedback: Dict[str, str]) -> float:
    """Calculate improvement score based on issue tracking.
    
    Rewards:
    - Issues marked as "FIXED" (+1.0 per issue)
    - Issues marked as "PARTIALLY FIXED" (+0.5 per issue)
    
    Penalties:
    - Issues marked as "NOT ADDRESSED" (-0.3 per issue)
    - New issues with severity CRITICAL (-0.4 per issue)
    - New issues with severity HIGH (-0.2 per issue)
    
    Args:
        reviewer_feedback: Dictionary of reviewer feedback
        
    Returns:
        Improvement score (0.0 to 1.0)
    """
    fixed_count = 0
    partially_fixed_count = 0
    not_addressed_count = 0
    new_critical_count = 0
    new_high_count = 0
    
    for feedback in reviewer_feedback.values():
        feedback_upper = feedback.upper()
        
        # Count fixed issues
        fixed_count += feedback_upper.count('✅ FIXED')
        fixed_count += feedback_upper.count('FIXED:')
        
        # Count partially fixed issues
        partially_fixed_count += feedback_upper.count('⚠️ PARTIALLY FIXED')
        partially_fixed_count += feedback_upper.count('PARTIALLY FIXED:')
        
        # Count not addressed issues
        not_addressed_count += feedback_upper.count('❌ NOT ADDRESSED')
        not_addressed_count += feedback_upper.count('NOT ADDRESSED:')
        
        # Count new issues by severity
        # Look for "NEW FINDINGS" section and count severities there
        if 'NEW FINDINGS' in feedback_upper:
            new_findings_section = feedback_upper.split('NEW FINDINGS')[1] if len(feedback_upper.split('NEW FINDINGS')) > 1 else ''
            # Only count in new findings section, not in improvement tracking
            new_critical_count += new_findings_section.count('[SEVERITY: CRITICAL')
            new_high_count += new_findings_section.count('[SEVERITY: HIGH')
    
    # Calculate score
    # Positive contributions
    positive_score = (fixed_count * 1.0) + (partially_fixed_count * 0.5)
    
    # Negative contributions
    negative_score = (not_addressed_count * 0.3) + (new_critical_count * 0.4) + (new_high_count * 0.2)
    
    # Net improvement
    net_improvement = positive_score - negative_score
    
    # Normalize to 0-1 scale
    # Assume 5 fixed issues as "excellent improvement" (score 1.0)
    # Assume 5 new critical issues as "no improvement" (score 0.0)
    max_improvement = 5.0
    
    if net_improvement >= max_improvement:
        return 1.0
    elif net_improvement <= -max_improvement:
        return 0.0
    else:
        # Linear scale from 0.5 (no change) to 0-1
        return 0.5 + (net_improvement / (2 * max_improvement))

