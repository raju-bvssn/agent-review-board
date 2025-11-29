"""Base agent class."""

from abc import ABC, abstractmethod
from typing import Optional
from app.llm.base_provider import BaseLLMProvider


class BaseAgent(ABC):
    """Abstract base class for all agents.
    
    All agent implementations (Presenter, Reviewer, Confidence) must inherit
    from this class and implement the required methods.
    """
    
    def __init__(self, llm_provider: BaseLLMProvider, role: str = "base", **kwargs):
        """Initialize the agent.
        
        Args:
            llm_provider: LLM provider instance (dependency injection)
            role: Role identifier for this agent
            **kwargs: Additional configuration
        """
        self.llm_provider = llm_provider
        self.role = role
        self.config = kwargs
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        """Execute the agent's main function.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Agent output as string
        """
        pass
    
    def get_role(self) -> str:
        """Get the agent's role.
        
        Returns:
            Role identifier string
        """
        return self.role

