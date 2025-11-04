"""
Module Schemas
"""

from pydantic import BaseModel, Field, RootModel
from typing import Optional, List
from datetime import datetime
from app.models.enums import DifficultyLevel, LearningStyle


class ModuleResponse(BaseModel):
    """Module response model"""
    id: int
    learning_path_id: int
    platform_id: int
    platform_name: str
    title: str
    description: str
    learning_objectives: Optional[List[str]] = None
    duration: int = Field(..., description="Duration in minutes")
    order_index: int
    content_url: str
    difficulty: DifficultyLevel
    learning_style: LearningStyle
    completed: Optional[bool] = None
    created_at: Optional[datetime] = None
    is_inserted: Optional[bool] = None

    class Config:
        from_attributes = True


class ModulesListResponse(RootModel[List[ModuleResponse]]):
    """Response for getting multiple modules"""
    root: List[ModuleResponse]


class ModuleDeletionResponse(BaseModel):
    """Response for module deletion"""
    success: bool
    message: str
    deleted_module_id: int
    affected_learning_path_id: int
    deleted_quizzes_count: int


class ModuleCompletionRequest(BaseModel):
    user_id: str
    completion_notes: Optional[str] = None
    time_spent_minutes: Optional[int] = None


class ModuleCompletionResponse(BaseModel):
    success: bool
    message: str
    module_id: int
    user_id: str
    completed_at: datetime
    skill_points_awarded: int
    learning_path_progress_updated: bool
    new_completion_percentage: float


class ModuleCreate(BaseModel):
    """Schema for creating a module"""
    learning_path_id: int = Field(..., description="ID of the learning path")
    platform_id: int = Field(..., description="ID of the platform")
    title: str = Field(..., min_length=1, max_length=255, description="Module title")
    description: str = Field(..., min_length=1, max_length=2000, description="Module description")
    learning_objectives: Optional[List[str]] = Field(None, description="Learning objectives")
    duration: int = Field(..., ge=1, description="Duration in minutes")
    order_index: int = Field(..., ge=0, description="Order position in learning path")
    content_url: str = Field(..., description="URL to module content")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    learning_style: List[LearningStyle] = Field(default=[LearningStyle.VISUAL], description="Learning styles")
    is_inserted: Optional[bool] = Field(False, description="Flag indicating if the module is inserted into the system")

    class Config:
        from_attributes = True
