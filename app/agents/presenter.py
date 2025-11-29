"""Presenter agent implementation."""

from typing import List, Optional, Dict
from app.agents.base_agent import BaseAgent
from app.llm.base_provider import BaseLLMProvider


class PresenterAgent(BaseAgent):
    """Presenter agent that generates content based on requirements.
    
    The presenter is responsible for creating the initial content and
    refining it based on approved feedback from reviewers.
    """
    
    INITIAL_PROMPT_TEMPLATE = """You are a professional technical writer tasked with creating a clear, comprehensive problem summary.

USER REQUIREMENTS:
{requirements}

{file_context}

Your task is to analyze these requirements and create a structured problem summary that will be reviewed by multiple expert reviewers.

Generate a response in the following format:

# TITLE
[A clear, concise title for this problem/project]

## EXECUTIVE SUMMARY
[2-3 sentences summarizing the core problem and proposed solution]

## DETAILED DESCRIPTION
[Comprehensive description of the problem, context, and current situation]

## KEY REQUIREMENTS
[Bulleted list of specific requirements]
- Requirement 1
- Requirement 2
- ...

## CONSTRAINTS
[Any technical, business, or resource constraints]
- Constraint 1
- Constraint 2
- ...

## OPEN QUESTIONS
[Questions that need to be answered]
- Question 1
- Question 2
- ...

Be thorough, clear, and professional. This summary will be used by reviewers to provide feedback."""

    REFINEMENT_PROMPT_TEMPLATE = """You are a professional technical writer refining a problem summary based on reviewer feedback.

PREVIOUS VERSION:
{previous_output}

APPROVED REVIEWER FEEDBACK:
{feedback}

Your task is to revise the problem summary to address the feedback while maintaining the same structure:

# TITLE
[Updated title if needed]

## EXECUTIVE SUMMARY
[Updated summary addressing feedback]

## DETAILED DESCRIPTION
[Updated description addressing feedback]

## KEY REQUIREMENTS
[Updated requirements list]
- Requirement 1
- Requirement 2
- ...

## CONSTRAINTS
[Updated constraints]
- Constraint 1
- Constraint 2
- ...

## OPEN QUESTIONS
[Updated or new questions]
- Question 1
- Question 2
- ...

Address all feedback points while maintaining clarity and professionalism."""

    def __init__(self, llm_provider: BaseLLMProvider, **kwargs):
        """Initialize presenter agent.
        
        Args:
            llm_provider: LLM provider instance
            **kwargs: Additional configuration
                - temperature: LLM temperature (default: 0.7)
                - max_tokens: Maximum tokens to generate (default: 3000)
        """
        super().__init__(llm_provider, role="presenter", **kwargs)
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 3000)
    
    def generate(
        self,
        requirements: str,
        feedback: Optional[List[str]] = None,
        previous_output: Optional[str] = None,
        file_summaries: Optional[List[str]] = None
    ) -> str:
        """Generate content based on requirements and optional feedback.
        
        Args:
            requirements: User requirements and description
            feedback: Optional list of approved feedback from reviewers
            previous_output: Previous presenter output (for refinement)
            file_summaries: Optional summaries of uploaded files
            
        Returns:
            Generated content string (structured summary)
        """
        # Build file context
        file_context = ""
        if file_summaries and len(file_summaries) > 0:
            file_context = "UPLOADED FILES CONTEXT:\n"
            for i, summary in enumerate(file_summaries, 1):
                file_context += f"{i}. {summary}\n"
            file_context += "\n"
        
        # Choose prompt based on whether this is initial or refinement
        if feedback and previous_output:
            # Refinement iteration
            feedback_text = "\n".join([f"- {f}" for f in feedback])
            prompt = self.REFINEMENT_PROMPT_TEMPLATE.format(
                previous_output=previous_output,
                feedback=feedback_text
            )
        else:
            # Initial generation
            prompt = self.INITIAL_PROMPT_TEMPLATE.format(
                requirements=requirements,
                file_context=file_context
            )
        
        # Generate using LLM
        try:
            result = self.llm_provider.generate_text(
                prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return result.strip()
        except Exception as e:
            raise Exception(f"Presenter generation failed: {str(e)}")
    
    def execute(self, *args, **kwargs) -> str:
        """Execute the presenter agent.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
                - requirements: User requirements (required)
                - feedback: Optional approved feedback
                - previous_output: Optional previous output
                - file_summaries: Optional file summaries
            
        Returns:
            Generated content
        """
        requirements = kwargs.get('requirements', '')
        if not requirements:
            raise ValueError("Requirements are required for presenter")
        
        feedback = kwargs.get('feedback', None)
        previous_output = kwargs.get('previous_output', None)
        file_summaries = kwargs.get('file_summaries', None)
        
        return self.generate(
            requirements,
            feedback=feedback,
            previous_output=previous_output,
            file_summaries=file_summaries
        )

