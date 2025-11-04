"""
Quiz API Endpoints

This module provides comprehensive API endpoints for quiz management including:
- Quiz creation and generation using AI services
- Quiz attempts and submissions with automatic grading
- Real-time streaming for quiz operations
- Background processing for quiz generation and grading
- Analytics and quiz management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db_session
from app.schemas.core_schemas.quiz_schema import (
    QuizGenerationRequest, QuizGenerationResponse, QuizInfoResponse,
    QuizAttemptResponse, QuizSubmission, QuizResult
)
from app.services.core_services import quiz_service
from app.core.dependencies import get_current_active_user
from app.core.logger import get_logger
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/quizzes",
    tags=["Quiz"]
)


# =============================================================================
# QUIZ CREATION AND GENERATION ENDPOINTS
# =============================================================================

@router.post("/generate", response_model=QuizGenerationResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate a quiz for a module using background task
    """
    try:
        # Start quiz generation task
        task_result = await quiz_service.generate_quiz_for_module(
            db=db,
            module_id=request.module_id,
            num_questions=request.num_questions,
            user_id=current_user.id
        )

        return QuizGenerationResponse(
            message="Quiz generation started",
            task_id=task_result["task_id"],
            status="background_task_scheduled",
            module_id=request.module_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz for module {request.module_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# QUIZ RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/module/{module_id}", response_model=QuizInfoResponse)
async def get_quiz_info(
    module_id: int = Path(..., description="Module ID", ge=1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get quiz information for taking the quiz
    """
    try:
        quiz = await quiz_service.get_quiz_by_module_id(module_id=module_id, db=db)
        quiz_id = getattr(quiz, 'id')

        # Get quiz
        quiz = await quiz_service.get_quiz_for_taking(
            db=db,
            quiz_id=quiz_id
        )

        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        return QuizInfoResponse(quiz=quiz)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz info for Module {module_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# QUIZ ATTEMPT ENDPOINTS
# =============================================================================

@router.post("/{quiz_id}/start-quiz", response_model=QuizAttemptResponse)
async def start_quiz_attempt_endpoint(
    quiz_id: int = Path(..., description="Quiz ID", ge=1),
    user_id: str = Query(..., description="User ID starting the attempt"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Start a quiz attempt for a user
    """
    try:
        # Authorization: users can only start attempts for themselves or team leads can start for others
        if current_user.id != user_id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Access denied")

        # Start quiz attempt
        attempt = await quiz_service.start_quiz_attempt(
            db=db,
            quiz_id=quiz_id,
            user_id=user_id
        )

        return attempt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting quiz attempt for quiz {quiz_id}, user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz_attempt(
    submission: QuizSubmission,
    quiz_id: int = Path(..., description="Quiz ID", ge=1),
    user_id: str = Query(..., description="User ID submitting the attempt"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submit a quiz attempt for grading
    """
    try:
        # Authorization: users can only submit their own attempts
        if current_user.id != user_id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Access denied")

        # Submit and grade the quiz
        quiz_result = await quiz_service.submit_and_grade_quiz(
            db=db,
            quiz_id=quiz_id,
            user_id=user_id,
            submission=submission
        )

        return quiz_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz {quiz_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/attempts/{attempt_id}/details", response_model=QuizResult)
async def get_quiz_attempt_details(
    attempt_id: int = Path(..., description="Quiz attempt ID", ge=1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed quiz attempt results including answers, explanations, and AI feedback
    """
    try:
        # Get the detailed attempt results
        attempt_details = await quiz_service.get_quiz_attempt_details(
            db=db,
            attempt_id=attempt_id,
            user_id=current_user.id
        )

        if not attempt_details:
            raise HTTPException(status_code=404, detail="Quiz attempt not found")

        return attempt_details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz attempt details for attempt {attempt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/attempts/module/{module_id}", response_model=List[QuizAttemptResponse])
async def get_user_quiz_attempts_by_quiz(
    module_id: int = Path(..., description="Module ID", ge=1),
    user_id: str = Query(..., description="User ID to get attempts for"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all quiz attempts for a specific user and quiz, based on module ID
    """
    try:
        # Authorization: users can only access their own attempts or team leads can access any
        if current_user.id != user_id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Access denied")

        # Get attempts using the correct service method for module-based queries
        attempts = await quiz_service.get_user_quiz_attempts_by_module(
            db=db,
            module_id=module_id,
            user_id=user_id
        )

        return attempts

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz attempts for module {module_id}, user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/module/{module_id}/attempts", response_model=List[QuizAttemptResponse])
async def get_user_quiz_attempts_by_module(
    module_id: int = Path(..., description="Module ID", ge=1),
    user_id: str = Query(..., description="User ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all quiz attempts for a specific user and module
    """
    try:
        # Authorization: users can only access their own attempts or team leads can access any
        if current_user.id != user_id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Access denied")

        # Get attempts
        attempts = await quiz_service.get_user_quiz_attempts_by_module(
            db=db,
            module_id=module_id,
            user_id=user_id
        )

        return attempts

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz attempts for module {module_id}, user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
