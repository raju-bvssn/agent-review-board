"""Session manager for handling session state and lifecycle."""

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from app.models.session_state import SessionState
from app.utils.file_utils import create_session_temp_folder, cleanup_session_temp_folder

if TYPE_CHECKING:
    from app.orchestration.iteration_state import IterationState


class SessionManager:
    """Manages session lifecycle and state.
    
    This class is responsible for:
    - Creating and initializing sessions
    - Managing session state (in-memory only)
    - Creating and cleaning up temporary folders
    - Coordinating session lifecycle
    - Storing iteration history
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.current_session: Optional[SessionState] = None
        self.session_history: Dict[str, SessionState] = {}
        self.iteration_data: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> list of iterations
        self.iteration_states: Dict[str, List[Any]] = {}  # session_id -> list of IterationState objects
    
    def create_session(
        self,
        session_name: str,
        requirements: str,
        selected_roles: List[str],
        models_config: Dict[str, str]
    ) -> SessionState:
        """Create a new session.
        
        Args:
            session_name: Human-readable session name
            requirements: User requirements/description
            selected_roles: List of selected reviewer roles
            models_config: Model assignments per agent
            
        Returns:
            Created SessionState object
        """
        session_id = str(uuid.uuid4())
        
        # Create temporary folder for this session
        temp_folder = create_session_temp_folder(session_id)
        
        # Create session state
        session_state = SessionState(
            session_id=session_id,
            session_name=session_name,
            requirements=requirements,
            selected_roles=selected_roles,
            models_config=models_config,
            temp_folder=temp_folder
        )
        
        self.current_session = session_state
        self.session_history[session_id] = session_state
        
        return session_state
    
    def get_current_session(self) -> Optional[SessionState]:
        """Get the current active session.
        
        Returns:
            Current SessionState or None if no active session
        """
        return self.current_session
    
    def finalize_session(self) -> bool:
        """Mark current session as complete and finalized.
        
        This does NOT end the session or clean up resources,
        it just marks it as finished so reports can be generated.
        
        Returns:
            True if successful, False if no active session
        """
        if self.current_session is None:
            return False
        
        # Mark session as finalized
        self.current_session.is_finalized = True
        
        return True
    
    def is_session_finalized(self) -> bool:
        """Check if current session is finalized.
        
        Returns:
            True if finalized, False otherwise
        """
        if self.current_session is None:
            return False
        
        return getattr(self.current_session, 'is_finalized', False)
    
    def end_session(self) -> bool:
        """End the current session and cleanup resources.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        if self.current_session is None:
            return True
        
        # Cleanup temporary folder
        success = True
        if self.current_session.temp_folder:
            success = cleanup_session_temp_folder(self.current_session.temp_folder)
        
        # Clear current session
        self.current_session = None
        
        return success
    
    def increment_iteration(self) -> int:
        """Increment the iteration counter for current session.
        
        Returns:
            New iteration number
            
        Raises:
            ValueError: If no active session
        """
        if self.current_session is None:
            raise ValueError("No active session")
        
        self.current_session.iteration += 1
        return self.current_session.iteration
    
    def get_iteration(self) -> int:
        """Get current iteration number.
        
        Returns:
            Current iteration number
            
        Raises:
            ValueError: If no active session
        """
        if self.current_session is None:
            raise ValueError("No active session")
        
        return self.current_session.iteration
    
    def store_iteration_data(
        self,
        presenter_output: str,
        reviewer_feedback: List[Dict[str, Any]],
        confidence_result: Dict[str, Any]
    ) -> None:
        """Store data from an iteration.
        
        Args:
            presenter_output: Content generated by presenter
            reviewer_feedback: List of reviewer feedback dictionaries
            confidence_result: Confidence evaluation result
            
        Raises:
            ValueError: If no active session
        """
        if self.current_session is None:
            raise ValueError("No active session")
        
        session_id = self.current_session.session_id
        
        # Initialize iteration data list for this session if needed
        if session_id not in self.iteration_data:
            self.iteration_data[session_id] = []
        
        # Store iteration data
        iteration_record = {
            "iteration": self.current_session.iteration,
            "presenter_output": presenter_output,
            "reviewer_feedback": reviewer_feedback,
            "confidence_result": confidence_result
        }
        
        self.iteration_data[session_id].append(iteration_record)
    
    def get_iteration_history(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get iteration history for a session.
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            List of iteration data dictionaries
            
        Raises:
            ValueError: If no session ID provided and no active session
        """
        if session_id is None:
            if self.current_session is None:
                raise ValueError("No active session")
            session_id = self.current_session.session_id
        
        return self.iteration_data.get(session_id, [])
    
    def get_latest_presenter_output(self) -> Optional[str]:
        """Get the latest presenter output from current session.
        
        Returns:
            Latest presenter output or None
        """
        history = self.get_iteration_history()
        if history:
            return history[-1].get("presenter_output")
        return None
    
    def get_session_data(self) -> Optional[Dict[str, Any]]:
        """Get current session data as dictionary.
        
        Returns:
            Dictionary with session information or None if no active session
        """
        if self.current_session is None:
            return None
        
        return {
            "session_id": self.current_session.session_id,
            "session_name": self.current_session.session_name,
            "requirements": self.current_session.requirements,
            "selected_roles": self.current_session.selected_roles,
            "models_config": self.current_session.models_config,
            "iteration": self.current_session.iteration,
            "temp_folder": self.current_session.temp_folder,
            "uploaded_files": self.current_session.uploaded_files,
            "created_at": getattr(self.current_session, 'created_at', ''),
            "is_finalized": getattr(self.current_session, 'is_finalized', False),
            "provider": self.current_session.models_config.get('provider', 'Unknown')
        }
    
    def save_uploaded_file(self, filename: str, content: bytes) -> str:
        """Save an uploaded file to session temp folder.
        
        Args:
            filename: Original filename
            content: File content as bytes
            
        Returns:
            Path to saved file
            
        Raises:
            ValueError: If no active session
        """
        if self.current_session is None:
            raise ValueError("No active session")
        
        from app.utils.file_utils import save_uploaded_file
        
        file_path = save_uploaded_file(
            content,
            filename,
            self.current_session.temp_folder
        )
        
        # Track uploaded file
        if file_path not in self.current_session.uploaded_files:
            self.current_session.uploaded_files.append(file_path)
        
        return file_path
    
    def record_iteration(self, iteration_state: 'IterationState') -> None:
        """Record an iteration state object.
        
        This is used by the WorkflowEngine to store complete iteration states
        including presenter output, reviewer feedback, aggregation, and confidence.
        
        Args:
            iteration_state: IterationState object to record
            
        Raises:
            ValueError: If no active session
        """
        if self.current_session is None:
            raise ValueError("No active session")
        
        session_id = self.current_session.session_id
        
        # Initialize iteration states list for this session if needed
        if session_id not in self.iteration_states:
            self.iteration_states[session_id] = []
        
        # Store iteration state
        self.iteration_states[session_id].append(iteration_state)
    
    def get_last_iteration(self) -> Optional['IterationState']:
        """Get the most recent iteration state.
        
        Returns:
            Latest IterationState or None if no iterations exist
        """
        if self.current_session is None:
            return None
        
        session_id = self.current_session.session_id
        states = self.iteration_states.get(session_id, [])
        
        if states:
            return states[-1]
        
        return None
    
    def get_iteration_count(self) -> int:
        """Get total number of recorded iterations.
        
        Returns:
            Number of iterations (0 if no active session)
        """
        if self.current_session is None:
            return 0
        
        session_id = self.current_session.session_id
        return len(self.iteration_states.get(session_id, []))
    
    def is_ready_for_finalization(self) -> bool:
        """Check if session is ready for finalization.
        
        Ready when:
        - At least one iteration completed
        - Latest iteration approved
        - Confidence meets threshold (0.82)
        
        Returns:
            True if ready, False otherwise
        """
        if self.current_session is None:
            return False
        
        last_iteration = self.get_last_iteration()
        
        if last_iteration is None:
            return False
        
        return (
            last_iteration.approved and
            last_iteration.confidence >= 0.82
        )
    
    def get_all_iteration_states(self) -> List['IterationState']:
        """Get all iteration states for current session.
        
        Returns:
            List of IterationState objects (empty list if none)
        """
        if self.current_session is None:
            return []
        
        session_id = self.current_session.session_id
        return self.iteration_states.get(session_id, []).copy()

