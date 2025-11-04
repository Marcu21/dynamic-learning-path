"""
Learning Path Schemas
"""

from pydantic import BaseModel, Field, RootModel
from typing import Optional, List
from datetime import datetime

from app.schemas.core_schemas.module_schema import ModuleResponse


class LearningPathResponse(BaseModel):
    """Base learning path response model"""
    id: int
    user_id: str
    title: str
    description: str
    estimated_days: int
    completion_percentage: float = Field(..., ge=0.0, le=100.0)
    preferences_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamLearningPathResponse(BaseModel):
    """Team learning path response model"""
    id: int
    title: str
    description: str
    user_id: str  # Creator/owner
    team_id: str
    estimated_days: int
    is_public: bool
    total_modules: int
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearningPathDetailResponse(BaseModel):
    """Response for GET /learning-paths/{learning_path_id}"""
    learning_path: LearningPathResponse
    modules: List[ModuleResponse]


class LearningPathCreate(BaseModel):
    """Learning path creation request"""
    user_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=1000)
    estimated_days: int = Field(..., ge=1, le=365)
    team_id: Optional[str] = None
    preferences_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserLearningPathsResponse(RootModel[List[LearningPathResponse]]):
    """Response for GET /learning-paths/user/{user_id}"""
    root: List[LearningPathResponse]


class TeamLearningPathsResponse(RootModel[List[TeamLearningPathResponse]]):
    """Response for GET /learning-paths/team/{team_id}"""
    root: List[TeamLearningPathResponse]


class LearningPathDeletionResponse(BaseModel):
    """Response for DELETE /learning-paths/{learning_path_id}"""
    success: bool
    message: str
    deleted_learning_path_id: int
    deleted_modules_count: int
    deleted_quizzes_count: int
    affected_users: List[str]


class ModuleProgressInfo(BaseModel):
    id: int
    title: str
    order_index: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    time_spent_minutes: Optional[int] = None
    difficulty: str
    learning_style: str


class LearningPathProgressResponse(BaseModel):
    learning_path_id: int
    user_id: str
    completion_percentage: float
    completed_modules: List[int]
    total_modules: int
    modules: List[ModuleProgressInfo]
    total_time_spent_minutes: int
    skill_points_earned: int
    questions_answered: int = 0
    started_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
