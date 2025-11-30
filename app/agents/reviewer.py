"""Reviewer agent implementation."""

from typing import List, Dict
from app.agents.base_agent import BaseAgent
from app.llm.base_provider import BaseLLMProvider
from app.models.feedback import Feedback


class ReviewerAgent(BaseAgent):
    """Base reviewer agent that provides feedback on content.
    
    Reviewers analyze content from the presenter and provide structured
    feedback (5-8 bullet points maximum).
    """
    
    # Base review prompt template (initial iteration)
    REVIEW_PROMPT_TEMPLATE = """You are a {role_description}.

CONTENT TO REVIEW:
{content}

Your task is to review this content from your specialized perspective and provide structured feedback.

Provide your feedback in the following format:

VERDICT: [Choose ONE: APPROVE / NEEDS REVISION / REJECT]

FINDINGS:
1. [Severity: CRITICAL/HIGH/MEDIUM/LOW] Finding description and specific issue
2. [Severity: CRITICAL/HIGH/MEDIUM/LOW] Finding description and specific issue
...
(Provide 5-8 specific, actionable findings)

SUGGESTED IMPROVEMENTS:
- Specific improvement 1
- Specific improvement 2
...

Be specific, actionable, and constructive. Focus on {focus_areas}."""
    
    # Iterative review prompt template (for iterations after the first)
    ITERATIVE_REVIEW_PROMPT_TEMPLATE = """You are a {role_description}.

ITERATION {iteration}: REVIEWING UPDATED CONTENT

PREVIOUS FEEDBACK (from iteration {previous_iteration}):
{previous_feedback}

UPDATED CONTENT TO REVIEW:
{content}

Your task is to:
1. Check if the previous issues were addressed
2. Identify any NEW issues introduced
3. Recognize improvements made
4. Provide updated feedback

Provide your feedback in the following format:

VERDICT: [Choose ONE: APPROVE / NEEDS REVISION / REJECT]

IMPROVEMENT TRACKING:
- ✅ FIXED: [List issues from previous iteration that were successfully addressed]
- ⚠️ PARTIALLY FIXED: [List issues that were partially addressed but need more work]
- ❌ NOT ADDRESSED: [List issues from previous iteration that still exist]

NEW FINDINGS (issues not present in previous iteration):
1. [Severity: CRITICAL/HIGH/MEDIUM/LOW] Finding description and specific issue
2. [Severity: CRITICAL/HIGH/MEDIUM/LOW] Finding description and specific issue
...

SUGGESTED IMPROVEMENTS:
- Specific improvement 1
- Specific improvement 2
...

Be specific about what improved and what didn't. Focus on {focus_areas}."""
    
    def __init__(self, llm_provider: BaseLLMProvider, role: str = "reviewer", **kwargs):
        """Initialize reviewer agent.
        
        Args:
            llm_provider: LLM provider instance
            role: Specific reviewer role (e.g., 'technical', 'clarity', 'security')
            **kwargs: Additional configuration
                - role_description: Description of this reviewer's role
                - focus_areas: What this reviewer should focus on
                - temperature: LLM temperature (default: 0.5)
                - max_tokens: Maximum tokens (default: 1500)
        """
        super().__init__(llm_provider, role=role, **kwargs)
        self.role_description = kwargs.get('role_description', 'professional reviewer')
        self.focus_areas = kwargs.get('focus_areas', 'quality and accuracy')
        self.temperature = kwargs.get('temperature', 0.5)
        self.max_tokens = kwargs.get('max_tokens', 1500)
    
    def review(self, content: str, iteration: int, previous_feedback: str = None) -> Feedback:
        """Review content and provide feedback.
        
        Args:
            content: Content to review (from presenter)
            iteration: Current iteration number
            previous_feedback: Optional feedback from previous iteration for tracking improvements
            
        Returns:
            Feedback object with review points
        """
        # Dynamic token scaling based on iteration
        # Iteration 1: Standard tokens (1500)
        # Iteration 2+: Increased tokens for improvement tracking (5000)
        # This ensures reviewers can provide complete feedback even with:
        # - Previous feedback context (adds ~1000 tokens to prompt)
        # - Improvement tracking output (adds ~500 tokens to response)
        # - Gemini's thinking tokens (~3000 tokens)
        if previous_feedback and iteration > 1:
            # Iterative review needs more tokens
            max_tokens = max(self.max_tokens, 5000)
            
            prompt = self.ITERATIVE_REVIEW_PROMPT_TEMPLATE.format(
                role_description=self.role_description,
                iteration=iteration,
                previous_iteration=iteration - 1,
                previous_feedback=previous_feedback,
                content=content,
                focus_areas=self.focus_areas
            )
        else:
            # Initial review uses standard token allocation
            max_tokens = self.max_tokens
            
            prompt = self.REVIEW_PROMPT_TEMPLATE.format(
                role_description=self.role_description,
                content=content,
                focus_areas=self.focus_areas
            )
        
        # Generate review using LLM
        try:
            result = self.llm_provider.generate_text(
                prompt,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            
            # Parse the result
            feedback_points = self._parse_review_result(result)
            
            # Validate we have 5-8 points (or at least some points)
            if len(feedback_points) < 1:
                feedback_points = ["No specific feedback provided"]
            elif len(feedback_points) > 8:
                feedback_points = feedback_points[:8]  # Trim to max 8
            
            return Feedback(
                reviewer_role=self.role,
                feedback_points=feedback_points,
                iteration=iteration,
                approved=False,
                modified=False
            )
        
        except Exception as e:
            # Return error feedback if generation fails
            return Feedback(
                reviewer_role=self.role,
                feedback_points=[f"Review failed: {str(e)}"],
                iteration=iteration,
                approved=False,
                modified=False
            )
    
    def _parse_review_result(self, result: str) -> List[str]:
        """Parse the LLM result into feedback points.
        
        Args:
            result: Raw LLM output
            
        Returns:
            List of feedback points
        """
        feedback_points = []
        
        # Extract findings section
        lines = result.split('\n')
        in_findings = False
        
        for line in lines:
            line = line.strip()
            
            if 'FINDINGS:' in line.upper():
                in_findings = True
                continue
            
            if 'SUGGESTED IMPROVEMENTS:' in line.upper():
                in_findings = False
            
            if in_findings and line:
                # Remove numbering and add to feedback
                clean_line = line.lstrip('0123456789.-) ')
                if clean_line and len(clean_line) > 10:  # Minimum meaningful length
                    feedback_points.append(clean_line)
        
        return feedback_points
    
    def execute(self, *args, **kwargs) -> Feedback:
        """Execute the reviewer agent.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments (should include 'content' and 'iteration')
            
        Returns:
            Feedback object
        """
        content = kwargs.get('content', '')
        iteration = kwargs.get('iteration', 0)
        return self.review(content, iteration)


class TechnicalReviewer(ReviewerAgent):
    """Technical reviewer specialized in technical accuracy and best practices."""
    
    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize technical reviewer.
        
        Args:
            llm_provider: LLM provider instance
            **kwargs: Additional configuration
        """
        kwargs['role_description'] = (
            "senior technical reviewer with expertise in software architecture, "
            "system design, and engineering best practices"
        )
        kwargs['focus_areas'] = (
            "technical accuracy, architectural soundness, scalability, "
            "maintainability, performance considerations, and technical feasibility"
        )
        super().__init__(llm_provider, role="technical_reviewer", **kwargs)


class ClarityReviewer(ReviewerAgent):
    """Clarity reviewer specialized in readability and comprehension."""
    
    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize clarity reviewer.
        
        Args:
            llm_provider: LLM provider instance
            **kwargs: Additional configuration
        """
        kwargs['role_description'] = (
            "professional editor specialized in technical communication, "
            "clarity, and audience comprehension"
        )
        kwargs['focus_areas'] = (
            "readability, clarity of expression, logical flow, completeness, "
            "consistency, and accessibility to the target audience"
        )
        super().__init__(llm_provider, role="clarity_reviewer", **kwargs)


class SecurityReviewer(ReviewerAgent):
    """Security reviewer specialized in security and privacy concerns."""
    
    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize security reviewer.
        
        Args:
            llm_provider: LLM provider instance
            **kwargs: Additional configuration
        """
        kwargs['role_description'] = (
            "security and privacy expert specializing in threat modeling, "
            "data protection, and security best practices"
        )
        kwargs['focus_areas'] = (
            "security vulnerabilities, data privacy, authentication and authorization, "
            "encryption, compliance requirements, and potential attack vectors"
        )
        super().__init__(llm_provider, role="security_reviewer", **kwargs)


class BusinessReviewer(ReviewerAgent):
    """Business reviewer specialized in business value and feasibility."""
    
    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize business reviewer.
        
        Args:
            llm_provider: LLM provider instance
            **kwargs: Additional configuration
        """
        kwargs['role_description'] = (
            "business analyst with expertise in product strategy, "
            "market analysis, and business value assessment"
        )
        kwargs['focus_areas'] = (
            "business value, ROI, market fit, user needs, competitive positioning, "
            "resource requirements, and strategic alignment"
        )
        super().__init__(llm_provider, role="business_reviewer", **kwargs)


class UXReviewer(ReviewerAgent):
    """UX reviewer specialized in user experience and usability."""
    
    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize UX reviewer.
        
        Args:
            llm_provider: LLM provider instance
            **kwargs: Additional configuration
        """
        kwargs['role_description'] = (
            "UX designer with expertise in user experience, usability, "
            "and human-centered design principles"
        )
        kwargs['focus_areas'] = (
            "user experience, usability, accessibility, user workflows, "
            "interaction design, and user satisfaction"
        )
        super().__init__(llm_provider, role="ux_reviewer", **kwargs)

