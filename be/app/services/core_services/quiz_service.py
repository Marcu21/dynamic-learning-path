"""
Quiz Service
===========

Core service for quiz operations including quiz generation, attempt management,
grading, and skill point awards. Integrates with AI services for generation
and grading, and progress service for skill point management.
"""
from datetime import timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.utils import get_current_utc_plus_2_time
from app.repositories import quiz_repository
from app.models.quiz import Quiz, QuizStatus, QuestionType
from app.schemas.core_schemas.quiz_schema import (
    QuizAttemptCreate, AnswerCreate,
    QuizSubmission, QuizResult, QuizAttemptResponse, QuizForTaking,
    QuestionResponse, QuestionOption, AnswerResult
)
from app.services.ai_services.quiz_services.quiz_generation_service import QuizGenerationService
from app.services.ai_services.quiz_services.quiz_grading_service import QuizGradingService

logger = get_logger(__name__)


async def generate_quiz_for_module(
    db: AsyncSession,
    module_id: int,
    num_questions: int,
    user_id: str
) -> Dict[str, Any]:
    """
    Generate a quiz for a module using AI service
    Returns task information for background processing
    """
    try:
        # Check if quiz already exists for this module
        existing_quiz = await quiz_repository.get_quiz_by_module_id(db, module_id)
        if existing_quiz:
            logger.info(f"Quiz already exists for module {module_id}")
            return {
                "task_id": f"existing_quiz_{existing_quiz.id}",
                "status": "completed",
                "message": "Quiz already exists for this module"
            }

        # Generate quiz using AI service
        quiz_generation_service = QuizGenerationService(db)
        await quiz_generation_service.generate_quiz_for_module(
            module_id=module_id,
            num_questions=num_questions
        )

        # The quiz generation service returns a QuizCreate object and handles persistence
        # So we return success information
        logger.info(f"Successfully generated quiz for module {module_id}")
        return {
            "task_id": f"quiz_generated_{module_id}",
            "status": "completed",
            "message": "Quiz generated successfully"
        }

    except Exception as e:
        logger.error(f"Error generating quiz for module {module_id}: {str(e)}")
        return {
            "task_id": f"quiz_failed_{module_id}",
            "status": "failed",
            "message": f"Quiz generation failed: {str(e)}"
        }


async def get_quiz_by_module_id(module_id: int, db: AsyncSession) -> Optional[Quiz]:
    """Get quiz by module ID"""
    try:
        return await quiz_repository.get_quiz_by_module_id(db, module_id)
    except Exception as e:
        logger.error(f"Error getting quiz for module {module_id}: {str(e)}")
        raise


async def get_quiz_for_taking(db: AsyncSession, quiz_id: int) -> Optional[QuizForTaking]:
    """
    Get quiz information for taking (questions without correct answers)
    """
    try:
        quiz = await quiz_repository.get_quiz_for_taking(db, quiz_id)
        if not quiz:
            return None

        # Convert questions to response format (without correct answers)
        questions = []
        for question in sorted(quiz.questions, key=lambda q: q.order_index):
            question_response = QuestionResponse(
                id=question.id,
                question_text=question.question_text,
                question_type=question.question_type,
                points=question.points,
                order_index=question.order_index,
                options= await _format_question_options(question) if question.question_type == QuestionType.MULTIPLE_CHOICE else None
            )
            questions.append(question_response)

        quiz_for_taking = QuizForTaking(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            total_questions=quiz.total_questions,
            passing_score=quiz.passing_score,
            estimated_completion_time=quiz.estimated_completion_time,
            questions=questions
        )

        return quiz_for_taking

    except Exception as e:
        logger.error(f"Error getting quiz {quiz_id} for taking: {str(e)}")
        raise


async def start_quiz_attempt(db: AsyncSession, quiz_id: int, user_id: str) -> QuizAttemptResponse:
    """Start a new quiz attempt"""
    try:
        # Verify quiz exists
        quiz = await quiz_repository.get_quiz_by_id(db, quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")

        if not quiz.is_active:
            raise ValueError(f"Quiz {quiz_id} is not active")

        # Create quiz attempt
        attempt_data = QuizAttemptCreate(
            quiz_id=quiz_id,
            user_id=user_id
        )

        attempt = await quiz_repository.create_quiz_attempt(db, attempt_data)

        # Convert to response format
        response = QuizAttemptResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            status=attempt.status,
            score=attempt.score,
            total_points=attempt.total_points,
            earned_points=attempt.earned_points,
            passed=attempt.passed,
            feedback=attempt.feedback,
            skill_points_awarded=attempt.skill_points_awarded,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            time_taken=attempt.time_taken
        )

        logger.info(f"Started quiz attempt {attempt.id} for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error starting quiz attempt for quiz {quiz_id}, user {user_id}: {str(e)}")
        raise


async def submit_and_grade_quiz(
    db: AsyncSession,
    quiz_id: int,
    user_id: str,
    submission: QuizSubmission
) -> QuizResult:
    """
    Submit and grade a quiz attempt, award skill points if passed
    """
    try:
        # Get the attempt
        attempt = await quiz_repository.get_quiz_attempt_by_id(db, submission.attempt_id)
        if not attempt:
            raise ValueError(f"Quiz attempt {submission.attempt_id} not found")

        if attempt.user_id != user_id:
            raise ValueError("User can only submit their own attempts")

        if attempt.status == QuizStatus.COMPLETED:
            raise ValueError("Quiz attempt already completed")

        # Get quiz and questions
        quiz = await quiz_repository.get_quiz_by_id(db, quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")

        # Create answer records
        answer_records = []
        for submission_answer in submission.answers:
            answer_data = AnswerCreate(
                attempt_id=submission.attempt_id,
                question_id=submission_answer.question_id,
                answer_text=submission_answer.answer_text,
                is_correct=False,  # Will be set during grading
                points_earned=0   # Will be set during grading
            )
            answer_records.append(answer_data)

        # Save answers to database
        answers = await quiz_repository.create_answers_batch(db, answer_records)

        # ✨ FIXED: Refresh the attempt to load the newly created answers
        await db.refresh(attempt, ['answers'])
        logger.info(f"Refreshed attempt {attempt.id}, found {len(attempt.answers)} answers to grade.")

        # Grade the quiz using AI grading service
        quiz_grading_service = QuizGradingService(db_session=db)
        grading_result = await quiz_grading_service.grade_quiz_attempt(
            attempt_id=submission.attempt_id
        )

        # Extract results from grading service response
        score_percentage = grading_result.get("score", 0.0) * 100  # Convert to percentage
        earned_points = grading_result.get("earned_points", 0)
        total_points = grading_result.get("total_points", 0)
        passed = grading_result.get("passed", False)
        overall_feedback = grading_result.get("feedback", "")
        skill_points_awarded = grading_result.get("skill_points_awarded", 0)

        # Calculate time taken
        completed_at = get_current_utc_plus_2_time()
        started_at = attempt.started_at

        if started_at.tzinfo is None:
            logger.warning(f"Database driver returned a naive datetime for attempt {attempt.id}. Forcing UTC.")
            started_at_aware = started_at.replace(tzinfo=timezone.utc)
        else:
            started_at_aware = started_at

        time_taken = int((completed_at - started_at_aware).total_seconds())

        # Update quiz attempt
        await quiz_repository.update_quiz_attempt(
            db=db,
            attempt_id=submission.attempt_id,
            status=QuizStatus.COMPLETED,
            score=score_percentage,
            total_points=total_points,
            earned_points=earned_points,
            passed=passed,
            feedback=overall_feedback,
            skill_points_awarded=skill_points_awarded,
            completed_at=completed_at,
            time_taken=time_taken
        )

        # Get the updated attempt with graded answers
        updated_attempt = await quiz_repository.get_quiz_attempt_by_id(db, submission.attempt_id)

        # Format answer results using the graded answers
        answer_results = []
        for answer in updated_attempt.answers:
            question = await quiz_repository.get_question_by_id(db, answer.question_id)
            answer_result = AnswerResult(
                question_id=answer.question_id,
                question_text=question.question_text if question else "",
                user_answer=answer.answer_text,
                correct_answer=question.correct_answer if question else "",
                is_correct=answer.is_correct,
                points_earned=answer.points_earned,
                ai_feedback=answer.ai_feedback or "",  # Use empty string if None
            )
            answer_results.append(answer_result)

        # Create result response
        quiz_result = QuizResult(
            attempt_id=submission.attempt_id,
            quiz_id=quiz_id,
            user_id=user_id,
            score=score_percentage,
            total_points=total_points,
            earned_points=earned_points,
            passed=passed,
            skill_points_awarded=skill_points_awarded,
            feedback=overall_feedback,
            started_at=attempt.started_at,  # Add missing started_at field
            completed_at=completed_at,
            time_taken=time_taken,
            answers=answer_results
        )

        logger.info(f"Completed quiz grading for attempt {submission.attempt_id}: score={score_percentage:.1f}%, passed={passed}")
        return quiz_result

    except Exception as e:
        logger.error(f"Error submitting and grading quiz {quiz_id} for user {user_id}: {str(e)}")
        raise


async def get_quiz_attempt_details(
    db: AsyncSession,
    attempt_id: int,
    user_id: str
) -> Optional[QuizResult]:
    """
    Get detailed quiz attempt results including answers, explanations, and AI feedback
    """
    try:
        # Get the quiz attempt with answers (using existing method)
        attempt = await quiz_repository.get_quiz_attempt_by_id(db, attempt_id)

        if not attempt or attempt.user_id != user_id:
            logger.warning(f"Quiz attempt {attempt_id} not found or access denied for user {user_id}")
            return None

        # Get quiz questions for additional details
        quiz = await quiz_repository.get_quiz_by_id(db, attempt.quiz_id)
        if not quiz:
            logger.error(f"Quiz {attempt.quiz_id} not found for attempt {attempt_id}")
            return None

        # Build detailed answer results
        answer_results = []
        for answer in attempt.answers:
            # Find the corresponding question
            question = next((q for q in quiz.questions if q.id == answer.question_id), None)
            if not question:
                continue

            answer_result = AnswerResult(
                question_id=answer.question_id,
                question_text=question.question_text,
                user_answer=answer.answer_text,
                correct_answer=question.correct_answer,  # Get from question, not answer
                is_correct=answer.is_correct,
                points_earned=answer.points_earned,
                ai_feedback=answer.ai_feedback or ""
            )
            answer_results.append(answer_result)

        # Sort answers by question order
        answer_results.sort(key=lambda x: next(
            (q.order_index for q in quiz.questions if q.id == x.question_id),
            0
        ))

        # Build and return the detailed quiz result
        return QuizResult(
            attempt_id=attempt.id,
            quiz_id=attempt.quiz_id,
            user_id=attempt.user_id,
            score=attempt.score,  # Don't multiply by 100 - it's already a percentage
            total_points=attempt.total_points,
            earned_points=attempt.earned_points,
            passed=attempt.passed,
            skill_points_awarded=30 if attempt.skill_points_awarded else 0,
            feedback=attempt.feedback or "",
            started_at=attempt.started_at,  # Add started_at field
            completed_at=attempt.completed_at if attempt.completed_at else attempt.started_at,
            time_taken=attempt.time_taken or 0,
            answers=answer_results
        )

    except Exception as e:
        logger.error(f"Error getting quiz attempt details for attempt {attempt_id}: {str(e)}")
        raise


async def get_user_quiz_attempts_by_module(
    db: AsyncSession,
    module_id: int,
    user_id: str
) -> List[QuizAttemptResponse]:
    """Get all quiz attempts for a user and module"""
    try:
        attempts = await quiz_repository.get_user_quiz_attempts_by_module(db, module_id, user_id)

        response_attempts = []
        for attempt in attempts:
            response = QuizAttemptResponse(
                id=attempt.id,
                quiz_id=attempt.quiz_id,
                user_id=attempt.user_id,
                status=attempt.status,
                score=attempt.score,
                total_points=attempt.total_points,
                earned_points=attempt.earned_points,
                passed=attempt.passed,
                feedback=attempt.feedback,
                skill_points_awarded=attempt.skill_points_awarded,
                started_at=attempt.started_at,
                completed_at=attempt.completed_at,
                time_taken=attempt.time_taken
            )
            response_attempts.append(response)

        return response_attempts

    except Exception as e:
        logger.error(f"Error getting quiz attempts for module {module_id}, user {user_id}: {str(e)}")
        raise


async def get_user_quiz_attempts_by_quiz(
    db: AsyncSession,
    quiz_id: int,
    user_id: str
) -> List[QuizAttemptResponse]:
    """Get all quiz attempts for a user and specific quiz"""
    try:
        attempts = await quiz_repository.get_user_quiz_attempts_by_quiz(db, quiz_id, user_id)

        response_attempts = []
        for attempt in attempts:
            response = QuizAttemptResponse(
                id=attempt.id,
                quiz_id=attempt.quiz_id,
                user_id=attempt.user_id,
                status=attempt.status,
                score=attempt.score,
                total_points=attempt.total_points,
                earned_points=attempt.earned_points,
                passed=attempt.passed,
                feedback=attempt.feedback,
                skill_points_awarded=attempt.skill_points_awarded,
                started_at=attempt.started_at,
                completed_at=attempt.completed_at,
                time_taken=attempt.time_taken
            )
            response_attempts.append(response)

        return response_attempts

    except Exception as e:
        logger.error(f"Error getting quiz attempts for quiz {quiz_id}, user {user_id}: {str(e)}")
        raise


async def _format_question_options(question) -> List[QuestionOption]:
    """Format question options for multiple choice questions"""
    if not question.options:
        return []

    options = []
    if isinstance(question.options, dict):
        for label, text in question.options.items():
            options.append(QuestionOption(label=label, text=text))
    elif isinstance(question.options, list):
        for i, text in enumerate(question.options):
            label = chr(65 + i)  # A, B, C, D...
            options.append(QuestionOption(label=label, text=text))

    return options