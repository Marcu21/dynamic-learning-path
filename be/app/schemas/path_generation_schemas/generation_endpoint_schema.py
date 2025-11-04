"""
Path Generation Schemas for Chat Endpoints
This module defines schemas for handling location-aware chat requests and streaming chat responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator

from app.models.enums import ExperienceLevel, LearningStyle


class PathGenerationRequest(BaseModel):
    """Request schema for learning path generation."""

    subject: str = Field(..., min_length=2, max_length=200, description="Learning subject")
    experience_level: ExperienceLevel = Field(..., description="Learner's experience level")
    learning_styles: List[LearningStyle] = Field(..., description="Preferred learning styles")
    preferred_platforms: List[str] = Field(..., description="Preferred learning platforms")
    study_time_minutes: int = Field(..., ge=15, le=480, description="Daily study time (15-480 minutes)")
    goals: str = Field(..., min_length=10, max_length=1000, description="Learning goals")
    team_id: Optional[str] = Field(None, description="Optional team ID for team learning paths")

    @field_validator('preferred_platforms')
    def validate_platforms(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one preferred platform must be specified")
        if len(v) > 10:
            raise ValueError("Too many platforms specified (max 10)")
        return v

    @field_validator('learning_styles')
    def validate_learning_styles(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one learning style must be specified")
        return v

    class Config:
        json_encoders = {
            ExperienceLevel: lambda v: v.value,
            LearningStyle: lambda v: v.value,
        }


class PathGenerationResponse(BaseModel):
    """Response schema for learning path generation request."""

    task_id: str = Field(..., description="Celery task ID for tracking")
    stream_channel: str = Field(..., description="Redis channel for real-time updates")
    status: str = Field(..., description="Initial task status")
    user_id: str = Field(..., description="User ID who requested generation")
    subject: str = Field(..., description="Learning subject")
    estimated_duration_minutes: int = Field(..., description="Estimated completion time")
    created_at: datetime = Field(default_factory=datetime.now, description="Request timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class UserTasksResponse(BaseModel):
    """Response schema for user's active tasks."""

    active_tasks: List[Dict[str, Any]]
    total_count: int
    running_count: int
    completed_count: int
    failed_count: int
