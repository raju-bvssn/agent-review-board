"""Feedback models for reviewer output."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


class Feedback(BaseModel):
    """Represents feedback from a reviewer agent.
    
    Attributes:
        reviewer_role: Role of the reviewer providing feedback
        feedback_points: List of feedback bullet points (max 5-8)
        iteration: Iteration number
        approved: Whether feedback has been approved by human
        modified: Whether feedback was modified by human
        timestamp: When feedback was created
        confidence_score: Optional confidence score for this feedback
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    reviewer_role: str = Field(..., description="Reviewer role identifier")
    feedback_points: List[str] = Field(..., description="Feedback bullet points")
    iteration: int = Field(..., description="Iteration number")
    approved: bool = Field(default=False, description="Human approved flag")
    modified: bool = Field(default=False, description="Modified by human flag")
    timestamp: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score")
    
    @field_validator('feedback_points')
    @classmethod
    def validate_feedback_count(cls, v):
        """Validate that feedback points are between 1 and 8."""
        if len(v) < 1:
            raise ValueError("Must have at least 1 feedback point")
        if len(v) > 8:
            raise ValueError("Maximum 8 feedback points allowed")
        return v


class ReviewerFeedbackCollection(BaseModel):
    """Collection of feedback from all reviewers for an iteration.
    
    Attributes:
        iteration: Iteration number
        feedbacks: List of feedback from all reviewers
        all_approved: Whether all feedback has been approved
        timestamp: When collection was created
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    iteration: int = Field(..., description="Iteration number")
    feedbacks: List[Feedback] = Field(default_factory=list, description="All reviewer feedback")
    all_approved: bool = Field(default=False, description="All approved flag")
    timestamp: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

