"""Message models for agent communication."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class Message(BaseModel):
    """Represents a message in the agent communication flow.
    
    Attributes:
        sender: Agent or user identifier
        content: Message content
        message_type: Type of message (request, response, feedback, etc.)
        timestamp: When the message was created
        iteration: Associated iteration number
        metadata: Additional metadata
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    sender: str = Field(..., description="Message sender identifier")
    content: str = Field(..., description="Message content")
    message_type: str = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    iteration: int = Field(default=0, description="Associated iteration")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

