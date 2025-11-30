"""Report generation utilities for Agent Review Board sessions."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles non-serializable objects safely.
    
    This encoder converts:
    - datetime objects to ISO format strings
    - dataclasses and custom objects to dicts
    - sets and tuples to lists
    - Any other non-serializable objects to strings
    """
    
    def default(self, obj):
        """Convert non-serializable objects to serializable format.
        
        Args:
            obj: Object to encode
            
        Returns:
            Serializable representation of object
        """
        # Convert datetimes to ISO format
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        
        # Convert dataclasses to dict
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        
        # Convert sets, tuples, other iterables to lists
        if isinstance(obj, (set, tuple)):
            return list(obj)
        
        # Fallback: convert to string
        return str(obj)


def aggregate_reviewer_feedback(reviewer_feedback_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate feedback from multiple reviewers into a summary.
    
    This function analyzes feedback from all reviewers and identifies:
    - Common issues mentioned by multiple reviewers
    - Disagreements between reviewers
    - Consensus recommendations
    - Overall severity distribution
    
    Args:
        reviewer_feedback_list: List of feedback dictionaries from reviewers
        
    Returns:
        Dictionary containing:
            - common_issues: Issues mentioned by 2+ reviewers
            - unique_issues: Issues mentioned by only one reviewer
            - disagreements: Conflicting feedback
            - consensus_items: Items all reviewers agree on
            - severity_breakdown: Count of issues by severity
            - average_confidence: Average confidence across reviewers
    """
    if not reviewer_feedback_list:
        return {
            "common_issues": [],
            "unique_issues": [],
            "disagreements": [],
            "consensus_items": [],
            "severity_breakdown": {},
            "average_confidence": 0.0,
            "total_issues": 0
        }
    
    # Extract all feedback points
    all_issues = []
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    confidence_scores = []
    
    for feedback in reviewer_feedback_list:
        if isinstance(feedback, dict):
            points = feedback.get('feedback_points', [])
        else:
            # Handle Feedback objects
            points = getattr(feedback, 'feedback_points', [])
        
        for point in points:
            all_issues.append({
                "text": point,
                "reviewer": feedback.get('reviewer_role') if isinstance(feedback, dict) else getattr(feedback, 'reviewer_role', 'unknown'),
                "severity": _extract_severity(point)
            })
            
            # Count severity
            severity = _extract_severity(point)
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Extract confidence if available
        if isinstance(feedback, dict) and 'confidence_score' in feedback:
            if feedback['confidence_score'] is not None:
                confidence_scores.append(feedback['confidence_score'])
    
    # Find common issues (mentioned by 2+ reviewers)
    common_issues = _find_common_issues(all_issues)
    
    # Find unique issues
    unique_issues = _find_unique_issues(all_issues, common_issues)
    
    # Detect disagreements (opposite sentiments)
    disagreements = _detect_disagreements(reviewer_feedback_list)
    
    # Find consensus items (all reviewers approve)
    consensus_items = _find_consensus(reviewer_feedback_list)
    
    # Calculate average confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    return {
        "common_issues": common_issues,
        "unique_issues": unique_issues,
        "disagreements": disagreements,
        "consensus_items": consensus_items,
        "severity_breakdown": severity_counts,
        "average_confidence": round(avg_confidence, 2),
        "total_issues": len(all_issues)
    }


def generate_final_report(
    session_data: Dict[str, Any],
    iteration_history: List[Any],
    format: str = "markdown"
) -> str:
    """Generate comprehensive final report for a review session.
    
    Args:
        session_data: Dictionary with session information
        iteration_history: List of IterationResult objects
        format: Output format ('markdown' or 'json')
        
    Returns:
        Formatted report string
    """
    if format == "json":
        return _generate_json_report(session_data, iteration_history)
    else:
        return _generate_markdown_report(session_data, iteration_history)


def _generate_markdown_report(
    session_data: Dict[str, Any],
    iteration_history: List[Any]
) -> str:
    """Generate Markdown format report.
    
    Args:
        session_data: Session information
        iteration_history: List of iteration results
        
    Returns:
        Markdown formatted string
    """
    report_lines = []
    
    # Header
    report_lines.append("# 🤖 Agent Review Board - Final Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Session Information
    report_lines.append("## 📋 Session Information")
    report_lines.append("")
    report_lines.append(f"**Session Name:** {session_data.get('session_name', 'Untitled')}")
    report_lines.append(f"**Total Iterations:** {len(iteration_history)}")
    report_lines.append(f"**Reviewers:** {', '.join(session_data.get('selected_roles', []))}")
    report_lines.append(f"**Provider:** {session_data.get('provider', 'Unknown').upper()}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Requirements
    report_lines.append("## 📝 Original Requirements")
    report_lines.append("")
    report_lines.append(session_data.get('requirements', 'No requirements specified'))
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Iteration Details
    report_lines.append("## 🔄 Iteration History")
    report_lines.append("")
    
    for i, iteration_result in enumerate(iteration_history, 1):
        report_lines.append(f"### Iteration {i}")
        report_lines.append("")
        
        # Presenter Output
        report_lines.append("#### 📤 Presenter Output")
        report_lines.append("")
        report_lines.append("```")
        presenter_output = iteration_result.presenter_output if hasattr(iteration_result, 'presenter_output') else ""
        report_lines.append(presenter_output[:500] + "..." if len(presenter_output) > 500 else presenter_output)
        report_lines.append("```")
        report_lines.append("")
        
        # Reviewer Feedback
        report_lines.append("#### 👥 Reviewer Feedback")
        report_lines.append("")
        
        reviewer_feedback = iteration_result.reviewer_feedback if hasattr(iteration_result, 'reviewer_feedback') else []
        for feedback in reviewer_feedback:
            reviewer_role = feedback.reviewer_role if hasattr(feedback, 'reviewer_role') else 'Unknown'
            feedback_points = feedback.feedback_points if hasattr(feedback, 'feedback_points') else []
            approved = feedback.approved if hasattr(feedback, 'approved') else False
            
            status = "✅ Approved" if approved else "⏸️ Pending"
            report_lines.append(f"**{reviewer_role}** {status}")
            report_lines.append("")
            
            for point in feedback_points:
                report_lines.append(f"- {point}")
            report_lines.append("")
        
        # Aggregated Feedback (if available)
        if hasattr(iteration_result, 'aggregated_feedback') and iteration_result.aggregated_feedback:
            report_lines.append("#### 🎯 Board Decision (Aggregated)")
            report_lines.append("")
            report_lines.append(iteration_result.aggregated_feedback)
            report_lines.append("")
        
        # Confidence Score
        confidence_result = iteration_result.confidence_result if hasattr(iteration_result, 'confidence_result') else {}
        score = confidence_result.get('score', 0)
        reasoning = confidence_result.get('reasoning', 'No reasoning available')
        
        report_lines.append("#### 📊 Confidence Score")
        report_lines.append("")
        report_lines.append(f"**Score:** {score}/100")
        report_lines.append("")
        report_lines.append(f"**Reasoning:** {reasoning}")
        report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
    
    # Final Summary
    if iteration_history:
        last_iteration = iteration_history[-1]
        report_lines.append("## 🎯 Final Summary")
        report_lines.append("")
        report_lines.append("### Final Presenter Output")
        report_lines.append("")
        final_output = last_iteration.presenter_output if hasattr(last_iteration, 'presenter_output') else ""
        report_lines.append(final_output)
        report_lines.append("")
        
        # Aggregate all feedback
        all_feedback = []
        for iteration_result in iteration_history:
            reviewer_feedback = iteration_result.reviewer_feedback if hasattr(iteration_result, 'reviewer_feedback') else []
            all_feedback.extend(reviewer_feedback)
        
        aggregated = aggregate_reviewer_feedback(all_feedback)
        
        report_lines.append("### Key Findings")
        report_lines.append("")
        
        if aggregated.get('common_issues'):
            report_lines.append("**Common Issues (mentioned by multiple reviewers):**")
            for issue in aggregated['common_issues'][:5]:
                report_lines.append(f"- {issue}")
            report_lines.append("")
        
        if aggregated.get('consensus_items'):
            report_lines.append("**Consensus Items (all reviewers agree):**")
            for item in aggregated['consensus_items'][:5]:
                report_lines.append(f"- {item}")
            report_lines.append("")
        
        report_lines.append("### Quality Metrics")
        report_lines.append("")
        report_lines.append(f"**Total Issues Identified:** {aggregated.get('total_issues', 0)}")
        report_lines.append(f"**Average Confidence:** {aggregated.get('average_confidence', 0)}/100")
        
        severity_breakdown = aggregated.get('severity_breakdown', {})
        if any(severity_breakdown.values()):
            report_lines.append("")
            report_lines.append("**Severity Breakdown:**")
            for severity, count in severity_breakdown.items():
                if count > 0:
                    report_lines.append(f"- {severity}: {count}")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("**Report End**")
    
    return "\n".join(report_lines)


def _generate_json_report(
    session_data: Dict[str, Any],
    iteration_history: List[Any]
) -> str:
    """Generate JSON format report.
    
    Args:
        session_data: Session information
        iteration_history: List of iteration results
        
    Returns:
        JSON formatted string
    """
    # Convert iteration objects to dicts
    iterations_data = []
    
    for iteration_result in iteration_history:
        iteration_dict = {
            "iteration": getattr(iteration_result, 'iteration', 0),
            "presenter_output": getattr(iteration_result, 'presenter_output', ''),
            "reviewer_feedback": [],
            "confidence_result": getattr(iteration_result, 'confidence_result', {}),
            "human_approved": getattr(iteration_result, 'human_gate_approved', False),
            "error": getattr(iteration_result, 'error', None)
        }
        
        # Convert feedback objects to dicts
        reviewer_feedback = getattr(iteration_result, 'reviewer_feedback', [])
        for feedback in reviewer_feedback:
            feedback_dict = {
                "reviewer_role": getattr(feedback, 'reviewer_role', ''),
                "feedback_points": getattr(feedback, 'feedback_points', []),
                "iteration": getattr(feedback, 'iteration', 0),
                "approved": getattr(feedback, 'approved', False),
                "modified": getattr(feedback, 'modified', False)
            }
            iteration_dict["reviewer_feedback"].append(feedback_dict)
        
        iterations_data.append(iteration_dict)
    
    # Build complete report
    report = {
        "session_info": {
            "session_name": session_data.get('session_name', 'Untitled'),
            "session_id": session_data.get('session_id', ''),
            "created_at": session_data.get('created_at', ''),
            "requirements": session_data.get('requirements', ''),
            "selected_roles": session_data.get('selected_roles', []),
            "provider": session_data.get('provider', ''),
            "total_iterations": len(iteration_history)
        },
        "iterations": iterations_data,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_version": "1.0"
        }
    }
    
    try:
        return json.dumps(report, indent=2, cls=SafeJSONEncoder)
    except Exception as e:
        # Raise a wrapped error with context
        raise RuntimeError(f"JSON report serialization failed: {e}")


def _extract_severity(text: str) -> str:
    """Extract severity level from feedback text.
    
    Args:
        text: Feedback text
        
    Returns:
        Severity level (CRITICAL, HIGH, MEDIUM, LOW, or NONE)
    """
    text_upper = text.upper()
    
    if 'CRITICAL' in text_upper:
        return 'CRITICAL'
    elif 'HIGH' in text_upper:
        return 'HIGH'
    elif 'MEDIUM' in text_upper:
        return 'MEDIUM'
    elif 'LOW' in text_upper:
        return 'LOW'
    else:
        return 'NONE'


def _find_common_issues(all_issues: List[Dict[str, str]]) -> List[str]:
    """Find issues mentioned by multiple reviewers.
    
    Args:
        all_issues: List of issue dictionaries
        
    Returns:
        List of common issue texts
    """
    # Simple keyword-based similarity
    issue_counts = {}
    
    for issue in all_issues:
        text = issue['text'].lower()
        # Extract key words (simple approach)
        words = set(text.split())
        key = tuple(sorted(words)[:5])  # Use first 5 words as key
        
        if key not in issue_counts:
            issue_counts[key] = []
        issue_counts[key].append(issue['text'])
    
    # Return issues mentioned by 2+ reviewers
    common = []
    for key, texts in issue_counts.items():
        if len(texts) >= 2:
            common.append(texts[0])  # Use first occurrence
    
    return common


def _find_unique_issues(all_issues: List[Dict[str, str]], common_issues: List[str]) -> List[str]:
    """Find issues mentioned by only one reviewer.
    
    Args:
        all_issues: List of all issues
        common_issues: List of common issues
        
    Returns:
        List of unique issue texts
    """
    unique = []
    
    for issue in all_issues:
        if issue['text'] not in common_issues:
            unique.append(issue['text'])
    
    return unique


def _detect_disagreements(reviewer_feedback_list: List[Any]) -> List[str]:
    """Detect disagreements between reviewers.
    
    Args:
        reviewer_feedback_list: List of feedback objects
        
    Returns:
        List of disagreement descriptions
    """
    disagreements = []
    
    # Check for conflicting verdicts
    verdicts = []
    for feedback in reviewer_feedback_list:
        # Try to extract verdict from feedback
        feedback_points = getattr(feedback, 'feedback_points', [])
        for point in feedback_points:
            if 'APPROVE' in point.upper():
                verdicts.append(('approve', getattr(feedback, 'reviewer_role', 'unknown')))
            elif 'REJECT' in point.upper():
                verdicts.append(('reject', getattr(feedback, 'reviewer_role', 'unknown')))
    
    # If we have both approvals and rejections
    approvals = [v for v in verdicts if v[0] == 'approve']
    rejections = [v for v in verdicts if v[0] == 'reject']
    
    if approvals and rejections:
        disagreements.append(
            f"Conflicting verdicts: {len(approvals)} reviewers approve, "
            f"{len(rejections)} reviewers reject"
        )
    
    return disagreements


def _find_consensus(reviewer_feedback_list: List[Any]) -> List[str]:
    """Find items all reviewers agree on.
    
    Args:
        reviewer_feedback_list: List of feedback objects
        
    Returns:
        List of consensus items
    """
    if len(reviewer_feedback_list) < 2:
        return []
    
    # For now, return empty - requires more sophisticated NLP
    # This would need similarity scoring between feedback points
    return []


# Helper functions for report generation

def get_session_summary(iteration_history: List[Any]) -> Dict[str, Any]:
    """Get high-level session summary.
    
    Args:
        iteration_history: List of iteration results
        
    Returns:
        Summary dictionary
    """
    if not iteration_history:
        return {
            "total_iterations": 0,
            "final_confidence": 0.0,
            "total_feedback_points": 0,
            "approved_iterations": 0
        }
    
    total_feedback = 0
    approved_count = 0
    
    for iteration_result in iteration_history:
        reviewer_feedback = getattr(iteration_result, 'reviewer_feedback', [])
        total_feedback += sum(len(getattr(f, 'feedback_points', [])) for f in reviewer_feedback)
        
        if getattr(iteration_result, 'human_gate_approved', False):
            approved_count += 1
    
    last_confidence = 0.0
    if iteration_history:
        last_result = iteration_history[-1]
        confidence_result = getattr(last_result, 'confidence_result', {})
        last_confidence = confidence_result.get('score', 0.0)
    
    return {
        "total_iterations": len(iteration_history),
        "final_confidence": last_confidence,
        "total_feedback_points": total_feedback,
        "approved_iterations": approved_count
    }


def export_session_to_dict(
    session_data: Dict[str, Any],
    iteration_history: List[Any]
) -> Dict[str, Any]:
    """Export complete session to dictionary for JSON export.
    
    Args:
        session_data: Session information
        iteration_history: List of iteration results
        
    Returns:
        Complete session dictionary
    """
    return {
        "session": session_data,
        "iterations": [
            {
                "iteration": getattr(result, 'iteration', 0),
                "presenter_output": getattr(result, 'presenter_output', ''),
                "reviewer_feedback": [
                    {
                        "role": getattr(f, 'reviewer_role', ''),
                        "points": getattr(f, 'feedback_points', []),
                        "approved": getattr(f, 'approved', False)
                    }
                    for f in getattr(result, 'reviewer_feedback', [])
                ],
                "confidence": getattr(result, 'confidence_result', {}),
                "approved": getattr(result, 'human_gate_approved', False)
            }
            for result in iteration_history
        ],
        "summary": get_session_summary(iteration_history),
        "exported_at": datetime.now().isoformat()
    }

