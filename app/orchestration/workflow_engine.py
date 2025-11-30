"""Workflow engine for multi-agent iterative review process."""

from typing import List, Optional, Dict, Any
from app.orchestration.iteration_state import IterationState
from app.orchestration.reviewer_manager import ReviewerManager
from app.orchestration.aggregator_agent import AggregatorAgent
from app.orchestration.confidence_model import calculate_confidence, CONFIDENCE_THRESHOLD
from app.agents.presenter import PresenterAgent
from app.llm.base_provider import BaseLLMProvider
from app.core.session_manager import SessionManager


class WorkflowEngine:
    """Orchestrates the complete multi-agent iterative workflow.
    
    This engine coordinates:
    1. Presenter generation
    2. Parallel reviewer execution
    3. Feedback aggregation
    4. Confidence calculation
    5. HITL approval gates
    6. Iteration state management
    7. Refinement loops
    
    The workflow continues until:
    - Confidence threshold reached (0.82)
    - Human finalizes session
    - Maximum iterations reached
    """
    
    MAX_ITERATIONS = 10
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        session_manager: SessionManager
    ):
        """Initialize workflow engine.
        
        Args:
            llm_provider: LLM provider for all agents
            session_manager: Session manager instance
        """
        self.llm_provider = llm_provider
        self.session_manager = session_manager
        
        # Initialize sub-components
        self.presenter = PresenterAgent(llm_provider)
        self.reviewer_manager = ReviewerManager(llm_provider)
        self.aggregator = AggregatorAgent(llm_provider)
        
        # Iteration history (stored in memory)
        self.iteration_history: List[IterationState] = []
    
    def run_iteration(
        self,
        requirements: str,
        selected_roles: List[str],
        file_summaries: Optional[List[str]] = None,
        use_parallel: bool = True
    ) -> IterationState:
        """Run a complete iteration cycle.
        
        Steps:
        1. Generate content with presenter
        2. Run reviewers in parallel
        3. Aggregate feedback
        4. Calculate confidence
        5. Create and store iteration state
        
        Args:
            requirements: User requirements
            selected_roles: List of reviewer roles to use
            file_summaries: Optional file context
            use_parallel: Whether to run reviewers in parallel (default True)
            
        Returns:
            IterationState object for this iteration
            
        Raises:
            ValueError: If session is finalized or max iterations reached
        """
        # Check if session is finalized
        if self.session_manager.is_session_finalized():
            raise ValueError("Cannot run iteration: session is finalized")
        
        # Check iteration limit
        current_iteration = len(self.iteration_history) + 1
        if current_iteration > self.MAX_ITERATIONS:
            raise ValueError(f"Maximum iterations ({self.MAX_ITERATIONS}) reached")
        
        try:
            # Step 1: Run Presenter
            print(f"[WorkflowEngine] Starting iteration {current_iteration}")
            print(f"[WorkflowEngine] Step 1: Running Presenter...")
            
            presenter_output = self._run_presenter(
                requirements,
                file_summaries
            )
            
            # Step 2: Run Reviewers in Parallel
            print(f"[WorkflowEngine] Step 2: Running {len(selected_roles)} Reviewers...")
            
            # Get previous feedback for iteration tracking
            previous_feedback = None
            if self.iteration_history:
                last_iteration = self.iteration_history[-1]
                previous_feedback = last_iteration.reviewer_feedback
            
            reviewer_feedback = self.reviewer_manager.run_reviewers(
                presenter_output,
                selected_roles,
                current_iteration,
                parallel=use_parallel,
                previous_feedback=previous_feedback
            )
            
            # Step 3: Aggregate Feedback
            print(f"[WorkflowEngine] Step 3: Aggregating Feedback...")
            
            aggregated_feedback = self.aggregator.aggregate(
                reviewer_feedback,
                presenter_output
            )
            
            # Step 4: Calculate Confidence
            print(f"[WorkflowEngine] Step 4: Calculating Confidence...")
            
            confidence = calculate_confidence(
                reviewer_feedback,
                aggregated_feedback
            )
            
            print(f"[WorkflowEngine] Confidence: {confidence:.2f}")
            
            # Step 5: Create Iteration State
            iteration_state = IterationState(
                iteration=current_iteration,
                presenter_output=presenter_output,
                reviewer_feedback=reviewer_feedback,
                aggregated_feedback=aggregated_feedback,
                confidence=confidence,
                approved=False,
                error=None
            )
            
            # Store iteration
            self.iteration_history.append(iteration_state)
            
            # Record in session manager
            self.session_manager.record_iteration(iteration_state)
            
            print(f"[WorkflowEngine] Iteration {current_iteration} complete")
            
            return iteration_state
        
        except Exception as e:
            # Create error iteration state
            error_state = IterationState(
                iteration=current_iteration,
                presenter_output="",
                reviewer_feedback={},
                aggregated_feedback="",
                confidence=0.0,
                approved=False,
                error=str(e)
            )
            
            self.iteration_history.append(error_state)
            
            print(f"[WorkflowEngine] Iteration {current_iteration} failed: {str(e)}")
            
            return error_state
    
    def _run_presenter(
        self,
        requirements: str,
        file_summaries: Optional[List[str]]
    ) -> str:
        """Run presenter agent with refinement if applicable.
        
        Args:
            requirements: User requirements
            file_summaries: Optional file summaries
            
        Returns:
            Presenter output string
        """
        # Get previous iteration for refinement
        previous_output = None
        approved_feedback = None
        
        if self.iteration_history:
            last_iteration = self.iteration_history[-1]
            
            if last_iteration.approved:
                previous_output = last_iteration.presenter_output
                
                # Use aggregated feedback as refinement guidance
                if last_iteration.aggregated_feedback:
                    approved_feedback = [last_iteration.aggregated_feedback]
        
        # Generate
        output = self.presenter.generate(
            requirements=requirements,
            feedback=approved_feedback,
            previous_output=previous_output,
            file_summaries=file_summaries
        )
        
        return output
    
    def approve_iteration(self, iteration_number: int) -> bool:
        """Approve a specific iteration (HITL gate).
        
        Args:
            iteration_number: Iteration to approve (1-indexed)
            
        Returns:
            True if successful, False if iteration not found
        """
        for iteration in self.iteration_history:
            if iteration.iteration == iteration_number:
                iteration.approved = True
                
                # Update session manager
                self.session_manager.increment_iteration()
                
                return True
        
        return False
    
    def get_current_iteration(self) -> Optional[IterationState]:
        """Get the most recent iteration state.
        
        Returns:
            Latest IterationState or None
        """
        if self.iteration_history:
            return self.iteration_history[-1]
        return None
    
    def get_iteration_count(self) -> int:
        """Get total number of iterations run.
        
        Returns:
            Number of iterations
        """
        return len(self.iteration_history)
    
    def get_all_iterations(self) -> List[IterationState]:
        """Get complete iteration history.
        
        Returns:
            List of all IterationState objects
        """
        return self.iteration_history.copy()
    
    def is_ready_for_finalization(self) -> bool:
        """Check if workflow is ready for finalization.
        
        Ready when:
        - At least one iteration completed
        - Latest iteration approved by human
        - Confidence meets threshold (0.82)
        
        Returns:
            True if ready for finalization, False otherwise
        """
        if not self.iteration_history:
            return False
        
        last_iteration = self.iteration_history[-1]
        
        return (
            last_iteration.approved and
            last_iteration.meets_confidence_threshold(CONFIDENCE_THRESHOLD)
        )
    
    def can_run_next_iteration(self) -> bool:
        """Check if next iteration can be run.
        
        Can run if:
        - Session not finalized
        - Previous iteration approved (if exists)
        - Under max iteration limit
        
        Returns:
            True if can run next iteration, False otherwise
        """
        # Check finalization
        if self.session_manager.is_session_finalized():
            return False
        
        # Check iteration limit
        if len(self.iteration_history) >= self.MAX_ITERATIONS:
            return False
        
        # Check previous approval (except for first iteration)
        if self.iteration_history:
            last_iteration = self.iteration_history[-1]
            return last_iteration.approved
        
        # First iteration - always allowed
        return True
    
    def reset(self):
        """Reset workflow engine (clear iteration history).
        
        Used when starting a new session.
        """
        self.iteration_history = []

