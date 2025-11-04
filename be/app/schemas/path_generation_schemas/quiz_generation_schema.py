"""
Quiz Generation Schemas
This module defines schemas for handling quiz generation requests,
responses, and metrics tracking in the application.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.core.config import settings


@dataclass
class QuizGenerationMetrics:
    """
    Metrics tracking for quiz generation performance and quality.

    Used for monitoring generation efficiency, AI response quality,
    and overall service performance analytics.
    """
    generation_start_time: datetime
    ai_request_time_seconds: float
    json_parsing_time_seconds: float
    database_persistence_time_seconds: float
    total_generation_time_seconds: float
    questions_generated: int
    ai_model_used: str
    generation_success: bool
    retry_count: int
    error_message: Optional[str] = None


class QuizContentResponse(BaseModel):
    """
    Pydantic model for validating AI-generated quiz content responses.

    Ensures the AI response contains all required fields in the correct format
    and validates question structure before database persistence.
    """

    title: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Clear, engaging title for the quiz"
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Brief description of what this quiz tests"
    )

    passing_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Minimum score required to pass (0.0 to 1.0)"
    )

    questions: List[Dict[str, Any]] = Field(
        ...,
        min_items=settings.min_quiz_questions,
        max_items=settings.max_quiz_questions,
        description="List of quiz questions with all required fields"
    )

class QuizGradingMetrics:
    """
    Metrics tracking for quiz grading performance and accuracy.

    Used for monitoring grading efficiency, AI accuracy for subjective questions,
    and overall service performance analytics.
    """

    def __init__(self):
        self.grading_start_time = datetime.now()
        self.objective_questions_graded = 0
        self.subjective_questions_graded = 0
        self.ai_grading_time_seconds = 0.0
        self.total_grading_time_seconds = 0.0
        self.grading_success = True
        self.error_message = None
