"""Aggregator agent for synthesizing multi-reviewer feedback."""

from typing import Dict, List, Optional
from app.llm.base_provider import BaseLLMProvider


class AggregatorAgent:
    """Aggregator agent that synthesizes feedback from multiple reviewers.
    
    This agent takes feedback from all reviewers and produces:
    - Unified list of recommended changes
    - Conflict detection and resolution
    - Consensus identification
    - Priority assignment
    - Risk assessment
    
    This represents the "Board Decision" from the Architecture Review Board.
    """
    
    AGGREGATION_PROMPT_TEMPLATE = """You are the Board Chair of an Architecture Review Board.

You have received feedback from multiple specialized reviewers about the same content.
Your job is to synthesize their feedback into a unified, actionable recommendation.

REVIEWER FEEDBACK:
{reviewer_feedback}

Your task:

1. **Identify Common Issues**: What do multiple reviewers agree on?
2. **Detect Conflicts**: Where do reviewers disagree? How should we resolve?
3. **Prioritize Changes**: What must be fixed vs what's optional?
4. **Assess Risks**: What are the biggest concerns?
5. **Highlight Strengths**: What did reviewers approve?

Provide your unified board decision in this format:

BOARD DECISION
==============

CONSENSUS ISSUES (mentioned by 2+ reviewers):
- [Priority: CRITICAL/HIGH/MEDIUM/LOW] Issue description
- ...

UNIQUE CONCERNS:
- [Reviewer: Name] Concern description
- ...

CONFLICTING OPINIONS:
- Conflict: Description
- Resolution: Recommended approach
- ...

REQUIRED CHANGES:
1. [Priority: CRITICAL] Change description with rationale
2. [Priority: HIGH] Change description with rationale
...

OPTIONAL IMPROVEMENTS:
1. [Priority: MEDIUM] Improvement description
2. [Priority: LOW] Improvement description
...

IDENTIFIED STRENGTHS:
- Strength 1
- Strength 2
...

RISK ASSESSMENT:
- [Risk Level: HIGH/MEDIUM/LOW] Risk description
- ...

RECOMMENDATION:
[APPROVE / APPROVE WITH CHANGES / NEEDS MAJOR REVISION / REJECT]

Be concise, specific, and actionable. Focus on creating a clear action plan."""
    
    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize aggregator agent.
        
        Args:
            llm_provider: LLM provider for aggregation
            **kwargs: Additional configuration
                - temperature: Generation temperature (default 0.3 for consistency)
                - max_tokens: Maximum tokens (default 2000)
        """
        self.llm_provider = llm_provider
        self.temperature = kwargs.get('temperature', 0.3)  # Lower temp for consistency
        self.max_tokens = kwargs.get('max_tokens', 2000)
    
    def aggregate(
        self,
        reviewer_feedback: Dict[str, str],
        presenter_output: Optional[str] = None
    ) -> str:
        """Aggregate feedback from multiple reviewers into unified decision.
        
        Args:
            reviewer_feedback: Dictionary mapping reviewer role to feedback string
            presenter_output: Optional presenter output for context
            
        Returns:
            Unified aggregated feedback string (board decision)
        """
        if not reviewer_feedback or len(reviewer_feedback) == 0:
            return "No reviewer feedback available. Cannot aggregate."
        
        # Build feedback summary
        feedback_text = self._format_reviewer_feedback(reviewer_feedback)
        
        # Build prompt
        prompt = self.AGGREGATION_PROMPT_TEMPLATE.format(
            reviewer_feedback=feedback_text
        )
        
        # Generate aggregated feedback using LLM
        try:
            result = self.llm_provider.generate_text(
                prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return result.strip()
        
        except Exception as e:
            # Fallback to simple aggregation if LLM fails
            return self._fallback_aggregation(reviewer_feedback)
    
    def _format_reviewer_feedback(self, reviewer_feedback: Dict[str, str]) -> str:
        """Format reviewer feedback for aggregation prompt.
        
        Args:
            reviewer_feedback: Dictionary of feedback
            
        Returns:
            Formatted feedback string
        """
        lines = []
        
        for role, feedback in reviewer_feedback.items():
            lines.append(f"=== {role} ===")
            lines.append(feedback)
            lines.append("")
        
        return "\n".join(lines)
    
    def _fallback_aggregation(self, reviewer_feedback: Dict[str, str]) -> str:
        """Fallback aggregation when LLM is unavailable.
        
        Uses deterministic rules to combine feedback.
        
        Args:
            reviewer_feedback: Dictionary of feedback
            
        Returns:
            Basic aggregated feedback string
        """
        lines = []
        
        lines.append("BOARD DECISION (Fallback Mode)")
        lines.append("=" * 50)
        lines.append("")
        
        lines.append(f"TOTAL REVIEWERS: {len(reviewer_feedback)}")
        lines.append("")
        
        # Count approvals and rejections
        approvals = 0
        rejections = 0
        revisions = 0
        
        for feedback in reviewer_feedback.values():
            feedback_upper = feedback.upper()
            if 'APPROVE' in feedback_upper and 'REJECT' not in feedback_upper:
                approvals += 1
            elif 'REJECT' in feedback_upper:
                rejections += 1
            elif 'REVISION' in feedback_upper:
                revisions += 1
        
        lines.append("VERDICT SUMMARY:")
        lines.append(f"- Approvals: {approvals}")
        lines.append(f"- Needs Revision: {revisions}")
        lines.append(f"- Rejections: {rejections}")
        lines.append("")
        
        # Extract all issues
        all_issues = []
        for role, feedback in reviewer_feedback.items():
            # Simple extraction
            for line in feedback.split('\n'):
                line = line.strip()
                if line and (
                    line.startswith('-') or 
                    line.startswith('•') or 
                    any(c.isdigit() and '.' in line[:5] for c in line[:5])
                ):
                    all_issues.append(f"[{role}] {line}")
        
        if all_issues:
            lines.append("ALL IDENTIFIED ISSUES:")
            for issue in all_issues[:15]:  # Limit to 15
                lines.append(issue)
            lines.append("")
        
        # Simple recommendation
        if rejections > len(reviewer_feedback) / 2:
            lines.append("RECOMMENDATION: NEEDS MAJOR REVISION")
        elif approvals > len(reviewer_feedback) / 2:
            lines.append("RECOMMENDATION: APPROVE WITH MINOR CHANGES")
        else:
            lines.append("RECOMMENDATION: NEEDS REVISION")
        
        return "\n".join(lines)


def detect_conflicts(reviewer_feedback: Dict[str, str]) -> List[str]:
    """Detect conflicts between reviewers.
    
    Args:
        reviewer_feedback: Dictionary of reviewer feedback
        
    Returns:
        List of conflict descriptions
    """
    conflicts = []
    
    # Check for opposing verdicts
    approvals = []
    rejections = []
    
    for role, feedback in reviewer_feedback.items():
        feedback_upper = feedback.upper()
        if 'APPROVE' in feedback_upper and 'REJECT' not in feedback_upper:
            approvals.append(role)
        elif 'REJECT' in feedback_upper:
            rejections.append(role)
    
    if approvals and rejections:
        conflicts.append(
            f"Verdict Conflict: {len(approvals)} reviewer(s) approve "
            f"({', '.join(approvals)}), while {len(rejections)} reject "
            f"({', '.join(rejections)})"
        )
    
    return conflicts


def identify_consensus(reviewer_feedback: Dict[str, str]) -> List[str]:
    """Identify consensus items across reviewers.
    
    Args:
        reviewer_feedback: Dictionary of reviewer feedback
        
    Returns:
        List of consensus items
    """
    if len(reviewer_feedback) < 2:
        return []
    
    consensus_items = []
    
    # Extract key phrases from each feedback
    all_phrases = {}
    
    for role, feedback in reviewer_feedback.items():
        # Simple phrase extraction (words 4+ chars)
        import re
        words = re.findall(r'\b\w{4,}\b', feedback.lower())
        
        for word in words:
            if word not in all_phrases:
                all_phrases[word] = []
            all_phrases[word].append(role)
    
    # Find phrases mentioned by multiple reviewers
    for phrase, roles in all_phrases.items():
        if len(roles) >= 2:
            consensus_items.append(f"{phrase} (mentioned by {len(roles)} reviewers)")
    
    # Return top 10 consensus items
    return consensus_items[:10]


def extract_required_changes(aggregated_feedback: str) -> List[str]:
    """Extract required changes from aggregated feedback.
    
    Args:
        aggregated_feedback: Aggregated feedback string
        
    Returns:
        List of required change descriptions
    """
    changes = []
    
    lines = aggregated_feedback.split('\n')
    in_required_section = False
    
    for line in lines:
        line_strip = line.strip()
        
        if 'REQUIRED CHANGES' in line_strip.upper():
            in_required_section = True
            continue
        
        if in_required_section:
            # Stop at next section
            if line_strip and line_strip.isupper() and ':' in line_strip:
                break
            
            # Extract change item
            if line_strip and (
                line_strip[0].isdigit() or 
                line_strip.startswith('-') or 
                line_strip.startswith('•')
            ):
                changes.append(line_strip)
    
    return changes

