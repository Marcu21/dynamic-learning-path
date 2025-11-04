"""
Statistics Schemas
==================

Pydantic schemas for user statistics API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class UserStatisticsResponse(BaseModel):
    """Response model for comprehensive user statistics"""

    # Common fields
    user_id: str = Field(..., description="User ID")

    # Streak fields
    streak_days: Optional[int] = Field(None, description="Number of consecutive days the user has been active")
    user_created_at: Optional[str] = Field(None, description="ISO date when the user was created")

    # Content Completion fields
    completed_learning_paths: Optional[int] = Field(None, description="Number of learning paths completed by the user")
    modules_completed: Optional[int] = Field(None, description="Number of modules completed by the user")
    skill_points_earned: Optional[int] = Field(None, description="Total skill points earned by the user")
    quizzes_completed: Optional[int] = Field(None, description="Number of quizzes completed by the user")

    # Where you stand
    user_total_minutes: Optional[float] = Field(None, description="Total minutes spent by the user")
    community_average_minutes: Optional[float] = Field(None, description="Average minutes spent by the community")

    # Daily Learning Data
    learning_time_data: Optional[Dict[str, float]] = Field(
        None,
        description="Maps date (YYYY-MM-DD) to minutes spent learning on that day"
    )

    # Platform Time Summary
    platform_time_summary: Optional[Dict[str, float]] = Field(
        None,
        description="Maps platform name to percentage of time spent on that platform"
    )

    # Key Insights fields
    top_percentile_time: Optional[float] = Field(None, description="Top percentile the user is in based on time spent")
    community_impact: Optional[float] = Field(None, description="User time spent / total time spent by the community")
    content_coverage: Optional[float] = Field(None, description="Percentage of content the user has completed of their own learning paths")

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "streak_days": 5,
                "user_created_at": "2024-01-15T10:30:00Z",
                "completed_learning_paths": 3,
                "modules_completed": 15,
                "skill_points_earned": 1250,
                "quizzes_completed": 8,
                "user_total_minutes": 720.5,
                "community_average_minutes": 545.2,
                "learning_time_data": {
                    "2025-07-28": 120.0,
                    "2025-07-29": 90.5,
                    "2025-07-30": 150.0
                },
                "platform_time_summary": {
                    "youtube": 300.0,
                    "spotify": 180.5,
                    "google_books": 240.0
                },
                "top_percentile_time": 85.5,
                "community_impact": "High",
                "content_coverage": 75.2
            }
        }
