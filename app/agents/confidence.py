"""Confidence agent implementation."""

from typing import List, Dict
import re
from app.agents.base_agent import BaseAgent
from app.llm.base_provider import BaseLLMProvider
from app.models.feedback import Feedback


class ConfidenceAgent(BaseAgent):
    """Confidence agent that evaluates quality and convergence.
    
    The confidence agent analyzes the review process to determine if
    the content has reached sufficient quality and if reviewers are
    converging on approval.
    """
    
    SCORING_PROMPT_TEMPLATE = """You are an expert evaluator assessing the quality and readiness of reviewed content.

PRESENTER CONTENT:
{content}

REVIEWER FEEDBACK SUMMARY:
{feedback_summary}

Analyze the content and feedback to determine:
1. Overall quality of the content
2. Severity and quantity of issues raised
3. Whether the content is ready for approval

Provide a score from 0-100 where:
- 0-40: Major issues, significant work needed
- 41-60: Moderate issues, revision needed
- 61-80: Minor issues, close to ready
- 81-100: Excellent quality, ready for approval

Respond in this format:
SCORE: [number 0-100]
REASONING: [2-3 sentences explaining the score]"""
    
    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize confidence agent.
        
        Args:
            llm_provider: LLM provider instance
            **kwargs: Additional configuration
                - temperature: LLM temperature (default: 0.3)
                - max_tokens: Maximum tokens (default: 500)
        """
        super().__init__(llm_provider, role="confidence", **kwargs)
        self.temperature = kwargs.get('temperature', 0.3)
        self.max_tokens = kwargs.get('max_tokens', 500)
    
    def score(self, content: str, feedback_list: List[Feedback]) -> Dict[str, any]:
        """Calculate confidence score for the current state.
        
        Args:
            content: Current content from presenter
            feedback_list: All feedback from current iteration
            
        Returns:
            Dictionary with:
                - score: Confidence score (0-100)
                - reasoning: Explanation of the score
        """
        if not feedback_list or len(feedback_list) == 0:
            return {
                "score": 50.0,
                "reasoning": "No reviewer feedback available yet"
            }
        
        # Build feedback summary
        feedback_summary = self._build_feedback_summary(feedback_list)
        
        # Use LLM to evaluate
        prompt = self.SCORING_PROMPT_TEMPLATE.format(
            content=content[:1000],  # Limit content length
            feedback_summary=feedback_summary
        )
        
        try:
            result = self.llm_provider.generate_text(
                prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse score and reasoning
            score, reasoning = self._parse_score_result(result)
            
            # Apply penalty for conflicts
            penalty = self._calculate_conflict_penalty(feedback_list)
            final_score = max(0.0, score - penalty)
            
            return {
                "score": final_score,
                "reasoning": reasoning,
                "conflict_penalty": penalty
            }
        
        except Exception as e:
            # Fallback to heuristic scoring
            return self._heuristic_score(feedback_list)
    
    def _build_feedback_summary(self, feedback_list: List[Feedback]) -> str:
        """Build a summary of all feedback.
        
        Args:
            feedback_list: List of Feedback objects
            
        Returns:
            Summary string
        """
        summary = []
        for feedback in feedback_list:
            summary.append(f"\n{feedback.reviewer_role.upper()}:")
            for i, point in enumerate(feedback.feedback_points[:5], 1):  # Max 5 per reviewer
                summary.append(f"  {i}. {point}")
        
        return "\n".join(summary)
    
    def _parse_score_result(self, result: str) -> tuple:
        """Parse LLM result to extract score and reasoning.
        
        Args:
            result: LLM output
            
        Returns:
            Tuple of (score, reasoning)
        """
        score = 50.0
        reasoning = "Unable to parse evaluation"
        
        # Extract score
        score_match = re.search(r'SCORE:\s*(\d+)', result, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))
        
        # Extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?:\n\n|\Z)', result, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        return score, reasoning
    
    def _calculate_conflict_penalty(self, feedback_list: List[Feedback]) -> float:
        """Calculate penalty for conflicting feedback.
        
        Args:
            feedback_list: List of Feedback objects
            
        Returns:
            Penalty value (0-20 points)
        """
        if len(feedback_list) < 2:
            return 0.0
        
        # Simple heuristic: more feedback points = more concerns = higher penalty
        total_points = sum(len(f.feedback_points) for f in feedback_list)
        avg_points = total_points / len(feedback_list)
        
        # If average is > 6 points, apply penalty
        if avg_points > 6:
            return min(20.0, (avg_points - 6) * 5)
        
        return 0.0
    
    def _heuristic_score(self, feedback_list: List[Feedback]) -> Dict[str, any]:
        """Calculate confidence score using heuristics (fallback).
        
        Args:
            feedback_list: List of Feedback objects
            
        Returns:
            Dictionary with score and reasoning
        """
        # Simple heuristic based on feedback quantity
        total_points = sum(len(f.feedback_points) for f in feedback_list)
        avg_points = total_points / len(feedback_list) if feedback_list else 0
        
        # Fewer points = higher confidence
        if avg_points <= 2:
            score = 85.0
            reasoning = "Very few issues raised by reviewers"
        elif avg_points <= 4:
            score = 70.0
            reasoning = "Some issues raised but manageable"
        elif avg_points <= 6:
            score = 55.0
            reasoning = "Several issues need to be addressed"
        else:
            score = 40.0
            reasoning = "Many issues raised, significant revision needed"
        
        return {
            "score": score,
            "reasoning": reasoning,
            "conflict_penalty": 0.0
        }
    
    def evaluate_convergence(self, feedback_history: List[List[Feedback]]) -> Dict[str, any]:
        """Evaluate if reviewers are converging across iterations.
        
        Args:
            feedback_history: List of feedback lists (one per iteration)
            
        Returns:
            Dictionary with convergence metrics
        """
        if len(feedback_history) < 2:
            return {
                "is_converging": False,
                "convergence_score": 0.0,
                "iterations_to_convergence": None,
                "trend": "insufficient_data"
            }
        
        # Calculate average feedback points per iteration
        points_per_iteration = [
            sum(len(f.feedback_points) for f in iteration_feedback) / len(iteration_feedback)
            if iteration_feedback else 0
            for iteration_feedback in feedback_history
        ]
        
        # Check if trending downward (converging)
        if len(points_per_iteration) >= 2:
            recent_trend = points_per_iteration[-1] - points_per_iteration[-2]
            is_converging = recent_trend < 0  # Decreasing is good
            
            convergence_score = max(0.0, min(1.0, 1.0 - (points_per_iteration[-1] / 8.0)))
            
            return {
                "is_converging": is_converging,
                "convergence_score": convergence_score,
                "iterations_to_convergence": None,  # Hard to predict
                "trend": "improving" if is_converging else "not_improving",
                "feedback_trend": points_per_iteration
            }
        
        return {
            "is_converging": False,
            "convergence_score": 0.5,
            "iterations_to_convergence": None,
            "trend": "unknown"
        }
    
    def execute(self, *args, **kwargs) -> Dict[str, any]:
        """Execute the confidence agent.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
                - content: Current content
                - feedback_list: Current iteration feedback
                
        Returns:
            Dictionary with score and reasoning
        """
        content = kwargs.get('content', '')
        feedback_list = kwargs.get('feedback_list', [])
        return self.score(content, feedback_list)

