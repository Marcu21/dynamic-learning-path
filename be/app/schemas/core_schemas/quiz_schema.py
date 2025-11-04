"""
Quiz Schema Definitions
======================

Pydantic schemas for quiz-related API endpoints including quiz creation,
attempts, submissions, and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.quiz import QuestionType, QuizStatus


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class QuizGenerationRequest(BaseModel):
    """Request schema for generating a quiz for a module"""
    module_id: int = Field(..., description="Module ID", ge=1)
    num_questions: int = Field(default=10, description="Number of questions to generate", ge=1, le=50)


class QuizSubmissionAnswer(BaseModel):
    """Schema for a single answer in a quiz submission"""
    question_id: int = Field(..., description="Question ID", ge=1)
    answer_text: str = Field(..., description="User's answer")


class QuizSubmission(BaseModel):
    """Schema for submitting quiz answers"""
    attempt_id: int = Field(..., description="Quiz attempt ID", ge=1)
    answers: List[QuizSubmissionAnswer] = Field(..., description="List of answers")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class QuizGenerationResponse(BaseModel):
    """Response schema for quiz generation"""
    message: str = Field(..., description="Status message")
    task_id: str = Field(..., description="Background task ID")
    status: str = Field(..., description="Task status")
    module_id: int = Field(..., description="Module ID")


class QuestionOption(BaseModel):
    """Schema for multiple choice question options"""
    label: str = Field(..., description="Option label (A, B, C, D)")
    text: str = Field(..., description="Option text")


class QuestionResponse(BaseModel):
    """Schema for quiz question response"""
    id: int = Field(..., description="Question ID")
    question_text: str = Field(..., description="Question text")
    question_type: QuestionType = Field(..., description="Question type")
    options: Optional[List[QuestionOption]] = Field(None, description="Multiple choice options")
    points: int = Field(..., description="Points for this question")
    order_index: int = Field(..., description="Question order")


class QuizForTaking(BaseModel):
    """Schema for quiz information when taking the quiz"""
    id: int = Field(..., description="Quiz ID")
    title: str = Field(..., description="Quiz title")
    description: Optional[str] = Field(None, description="Quiz description")
    total_questions: int = Field(..., description="Total number of questions")
    passing_score: float = Field(..., description="Passing score percentage")
    estimated_completion_time: int = Field(..., description="Estimated time in minutes")
    questions: List[QuestionResponse] = Field(..., description="Quiz questions")


class QuizInfoResponse(BaseModel):
    """Response schema for quiz information"""
    quiz: QuizForTaking = Field(..., description="Quiz details")


class QuizAttemptResponse(BaseModel):
    """Response schema for quiz attempts"""
    id: int = Field(..., description="Attempt ID")
    quiz_id: int = Field(..., description="Quiz ID")
    user_id: str = Field(..., description="User ID")
    status: QuizStatus = Field(..., description="Attempt status")
    score: float = Field(..., description="Quiz score percentage")
    total_points: int = Field(..., description="Total possible points")
    earned_points: int = Field(..., description="Points earned")
    passed: bool = Field(..., description="Whether the quiz was passed")
    feedback: Optional[str] = Field(None, description="AI-generated feedback")
    skill_points_awarded: bool = Field(..., description="Whether skill points were awarded")
    started_at: datetime = Field(..., description="When the attempt was started")
    completed_at: Optional[datetime] = Field(None, description="When the attempt was completed")
    time_taken: Optional[int] = Field(None, description="Time taken in seconds")


class AnswerResult(BaseModel):
    """Schema for individual answer results"""
    question_id: int = Field(..., description="Question ID")
    question_text: str = Field(..., description="Question text")
    user_answer: str = Field(..., description="User's answer")
    correct_answer: str = Field(..., description="Correct answer")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    points_earned: int = Field(..., description="Points earned for this answer")
    ai_feedback: Optional[str] = Field(None, description="AI-generated feedback")


class QuizResult(BaseModel):
    """Schema for quiz submission results"""
    attempt_id: int = Field(..., description="Attempt ID")
    quiz_id: int = Field(..., description="Quiz ID")
    user_id: str = Field(..., description="User ID")
    score: float = Field(..., description="Final score percentage")
    total_points: int = Field(..., description="Total possible points")
    earned_points: int = Field(..., description="Points earned")
    passed: bool = Field(..., description="Whether the quiz was passed")
    skill_points_awarded: int = Field(..., description="Skill points awarded (0 if none)")
    feedback: str = Field(..., description="Overall feedback")
    started_at: datetime = Field(..., description="When the attempt was started")
    completed_at: datetime = Field(..., description="Completion timestamp")
    time_taken: int = Field(..., description="Time taken in seconds")
    answers: List[AnswerResult] = Field(..., description="Detailed answer results")


# =============================================================================
# INTERNAL SCHEMAS (for database operations)
# =============================================================================

class QuizCreate(BaseModel):
    """Schema for creating a quiz"""
    module_id: int = Field(..., description="Module ID")
    title: str = Field(..., description="Quiz title")
    description: Optional[str] = Field(None, description="Quiz description")
    total_questions: int = Field(..., description="Total number of questions")
    passing_score: float = Field(default=0.66, description="Passing score (66%)")
    estimated_completion_time: int = Field(default=30, description="Estimated time in minutes")


class QuestionCreate(BaseModel):
    """Schema for creating a question"""
    quiz_id: int = Field(..., description="Quiz ID")
    question_text: str = Field(..., description="Question text")
    question_type: QuestionType = Field(..., description="Question type")
    options: Optional[Dict[str, Any]] = Field(None, description="Question options")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: Optional[str] = Field(None, description="Answer explanation")
    points: int = Field(default=1, description="Points for this question")
    order_index: int = Field(..., description="Question order")


class QuizAttemptCreate(BaseModel):
    """Schema for creating a quiz attempt"""
    quiz_id: int = Field(..., description="Quiz ID")
    user_id: str = Field(..., description="User ID")


class AnswerCreate(BaseModel):
    """Schema for creating an answer"""
    attempt_id: int = Field(..., description="Attempt ID")
    question_id: int = Field(..., description="Question ID")
    answer_text: str = Field(..., description="User's answer")
    is_correct: bool = Field(default=False, description="Whether the answer is correct")
    points_earned: int = Field(default=0, description="Points earned")
