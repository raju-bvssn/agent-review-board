"""Session state Pydantic models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SessionState(BaseModel):
    """Represents the state of a review session.
    
    Attributes:
        session_id: Unique identifier for the session
        session_name: Human-readable name
        requirements: User-provided requirements/description
        uploaded_files: List of uploaded file paths (in temp folder)
        selected_roles: List of selected reviewer roles
        models_config: Configuration for models per agent
        iteration: Current iteration number
        created_at: Session creation timestamp
        temp_folder: Path to temporary session folder
        is_finalized: Whether session is marked as complete
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    session_id: str = Field(..., description="Unique session identifier")
    session_name: str = Field(..., description="Human-readable session name")
    requirements: str = Field(..., description="User requirements and description")
    uploaded_files: List[str] = Field(default_factory=list, description="Uploaded file paths")
    selected_roles: List[str] = Field(default_factory=list, description="Selected reviewer roles")
    models_config: Dict[str, str] = Field(default_factory=dict, description="Model assignments per agent")
    iteration: int = Field(default=0, description="Current iteration number")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    temp_folder: Optional[str] = Field(default=None, description="Temporary folder path")
    is_finalized: bool = Field(default=False, description="Session finalization status")


class LLMConfig(BaseModel):
    """Configuration for LLM provider.
    
    Attributes:
        provider: Provider name (e.g., 'openai', 'anthropic', 'mock')
        api_key: API key (stored in memory only)
        model_name: Selected model name
        temperature: Generation temperature
        max_tokens: Maximum tokens to generate
        additional_params: Additional provider-specific parameters
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    provider: str = Field(..., description="LLM provider name")
    api_key: Optional[str] = Field(default=None, description="API key (memory only)")
    model_name: str = Field(..., description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")
    max_tokens: int = Field(default=1000, gt=0, description="Maximum tokens")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Extra parameters")


class AgentConfig(BaseModel):
    """Configuration for an agent.
    
    Attributes:
        agent_type: Type of agent (presenter, reviewer, confidence)
        role: Specific role (e.g., 'technical_reviewer', 'clarity_reviewer')
        model_name: LLM model to use
        temperature: Generation temperature
        max_tokens: Maximum tokens
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    agent_type: str = Field(..., description="Agent type")
    role: str = Field(..., description="Agent role")
    model_name: str = Field(..., description="LLM model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")
    max_tokens: int = Field(default=1000, gt=0, description="Maximum tokens")

