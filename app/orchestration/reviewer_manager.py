"""Reviewer manager for parallel multi-agent execution."""

import asyncio
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.agents.reviewer import (
    ReviewerAgent,
    TechnicalReviewer,
    ClarityReviewer,
    SecurityReviewer,
    BusinessReviewer,
    UXReviewer
)
from app.llm.base_provider import BaseLLMProvider
from app.models.feedback import Feedback


# Map role names to reviewer classes
REVIEWER_CLASS_MAP = {
    'Technical Reviewer': TechnicalReviewer,
    'Clarity Reviewer': ClarityReviewer,
    'Security Reviewer': SecurityReviewer,
    'Business Reviewer': BusinessReviewer,
    'UX Reviewer': UXReviewer,
}


class ReviewerManager:
    """Manages parallel execution of multiple reviewer agents.
    
    This class coordinates the execution of multiple specialized reviewer agents,
    running them in parallel when possible to improve performance.
    """
    
    def __init__(self, llm_provider: BaseLLMProvider):
        """Initialize reviewer manager.
        
        Args:
            llm_provider: LLM provider for all reviewers
        """
        self.llm_provider = llm_provider
    
    def run_reviewers(
        self,
        presenter_output: str,
        selected_roles: List[str],
        iteration: int,
        parallel: bool = True,
        previous_feedback: Dict[str, str] = None
    ) -> Dict[str, str]:
        """Run multiple reviewers and collect their feedback.
        
        Args:
            presenter_output: Content to review from presenter
            selected_roles: List of reviewer role names
            iteration: Current iteration number
            parallel: Whether to run reviewers in parallel (default True)
            previous_feedback: Optional dict of previous feedback by role for iteration tracking
            
        Returns:
            Dictionary mapping reviewer role to feedback string
        """
        if parallel:
            return self._run_reviewers_parallel(presenter_output, selected_roles, iteration, previous_feedback)
        else:
            return self._run_reviewers_sequential(presenter_output, selected_roles, iteration, previous_feedback)
    
    def _run_reviewers_parallel(
        self,
        presenter_output: str,
        selected_roles: List[str],
        iteration: int,
        previous_feedback: Dict[str, str] = None
    ) -> Dict[str, str]:
        """Run reviewers in parallel using thread pool.
        
        Args:
            presenter_output: Content to review
            selected_roles: List of reviewer roles
            iteration: Iteration number
            previous_feedback: Optional dict of previous feedback by role
            
        Returns:
            Dictionary of reviewer feedback
        """
        feedback_dict = {}
        
        # Handle empty list
        if len(selected_roles) == 0:
            return feedback_dict
        
        # Use thread pool for parallel execution
        with ThreadPoolExecutor(max_workers=min(len(selected_roles), 5)) as executor:
            # Submit all reviewer tasks
            future_to_role = {}
            
            for role in selected_roles:
                # Get previous feedback for this role
                prev_fb = previous_feedback.get(role) if previous_feedback else None
                
                future = executor.submit(
                    self._execute_single_reviewer,
                    role,
                    presenter_output,
                    iteration,
                    prev_fb
                )
                future_to_role[future] = role
            
            # Collect results as they complete
            for future in as_completed(future_to_role):
                role = future_to_role[future]
                try:
                    feedback = future.result()
                    feedback_dict[role] = self._feedback_to_string(feedback)
                except Exception as e:
                    feedback_dict[role] = f"Review failed: {str(e)}"
        
        return feedback_dict
    
    def _run_reviewers_sequential(
        self,
        presenter_output: str,
        selected_roles: List[str],
        iteration: int,
        previous_feedback: Dict[str, str] = None
    ) -> Dict[str, str]:
        """Run reviewers sequentially (fallback for debugging).
        
        Args:
            presenter_output: Content to review
            selected_roles: List of reviewer roles
            iteration: Iteration number
            previous_feedback: Optional dict of previous feedback by role
            
        Returns:
            Dictionary of reviewer feedback
        """
        feedback_dict = {}
        
        for role in selected_roles:
            try:
                # Get previous feedback for this role
                prev_fb = previous_feedback.get(role) if previous_feedback else None
                
                feedback = self._execute_single_reviewer(role, presenter_output, iteration, prev_fb)
                feedback_dict[role] = self._feedback_to_string(feedback)
            except Exception as e:
                feedback_dict[role] = f"Review failed: {str(e)}"
        
        return feedback_dict
    
    def _execute_single_reviewer(
        self,
        role: str,
        content: str,
        iteration: int,
        previous_feedback: str = None
    ) -> Feedback:
        """Execute a single reviewer agent.
        
        Args:
            role: Reviewer role name
            content: Content to review
            iteration: Iteration number
            previous_feedback: Optional previous feedback from this reviewer for iteration tracking
            
        Returns:
            Feedback object from reviewer
        """
        # Get reviewer class
        reviewer_class = REVIEWER_CLASS_MAP.get(role, ReviewerAgent)
        
        # Create reviewer instance
        reviewer = reviewer_class(self.llm_provider)
        
        # Execute review with previous feedback context
        feedback = reviewer.review(content, iteration, previous_feedback=previous_feedback)
        
        return feedback
    
    def _feedback_to_string(self, feedback: Feedback) -> str:
        """Convert Feedback object to formatted string.
        
        Args:
            feedback: Feedback object
            
        Returns:
            Formatted feedback string
        """
        lines = []
        
        lines.append(f"REVIEWER: {feedback.reviewer_role}")
        lines.append(f"ITERATION: {feedback.iteration}")
        lines.append("")
        
        lines.append("FINDINGS:")
        for i, point in enumerate(feedback.feedback_points, 1):
            lines.append(f"{i}. {point}")
        
        lines.append("")
        
        if feedback.approved:
            lines.append("STATUS: ✅ APPROVED BY HUMAN")
        else:
            lines.append("STATUS: ⏸️ PENDING APPROVAL")
        
        if feedback.modified:
            lines.append("MODIFIED: ✏️ YES")
        
        return "\n".join(lines)


def create_reviewer_instances(
    llm_provider: BaseLLMProvider,
    selected_roles: List[str]
) -> List[ReviewerAgent]:
    """Create reviewer agent instances for selected roles.
    
    Args:
        llm_provider: LLM provider for agents
        selected_roles: List of reviewer role names
        
    Returns:
        List of ReviewerAgent instances
    """
    reviewers = []
    
    for role in selected_roles:
        reviewer_class = REVIEWER_CLASS_MAP.get(role, ReviewerAgent)
        reviewer = reviewer_class(llm_provider)
        reviewers.append(reviewer)
    
    return reviewers

