"""
Quiz Generation and Grading Tasks
=================================

This module provides Celery tasks for comprehensive quiz management including:
- Quiz generation for entire learning paths
- Quiz generation for individual modules
- Quiz submission and automatic grading
- Real-time streaming updates for quiz operations

Key Features:
- Async quiz generation using AI services
- Automatic LLM-based grading with detailed feedback
- Real-time progress streaming via Redis
- Error handling and retry mechanisms
- Task tracking and monitoring
- Skill point awards for quiz completions
"""

import json
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.db.celery_database import get_celery_db_session_sync as get_celery_db_session
from app.core.config import settings
from app.core.logger import get_logger
from app.core.redis_publisher import RedisPublisher
from app.services.ai_services.quiz_services.quiz_generation_service import QuizGenerationService
from app.services.ai_services.quiz_services.quiz_grading_service import QuizGradingService
from app.services.core_services.task_tracking_service import register_quiz_task, unregister_quiz_task
from app.tasks.chat_assistant_tasks import run_async_in_sync

logger = get_logger(__name__)

def publish_quiz_event(stream_channel: str, event_type: str, data: Dict[str, Any]) -> None:
    """
    Publish quiz-related events to Redis channel for real-time updates.

    Args:
        stream_channel: Redis channel name
        event_type: Type of event (quiz_generation_started, quiz_completed, etc.)
        data: Event data dictionary
    """
    try:
        redis_publisher = RedisPublisher()

        event_data = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }

        success = redis_publisher.publish(stream_channel, json.dumps(event_data))
        if success:
            logger.info(f"Published {event_type} event to channel {stream_channel}")
        else:
            logger.warning(f"Failed to publish {event_type} event to channel {stream_channel}")

    except Exception as e:
        logger.error(f"Error publishing quiz event: {str(e)}")


def get_learning_path_by_id_sync(db_session, learning_path_id: int, user_id: str):
    """
    Sync version of get_learning_path_by_id for use in Celery tasks.
    """
    try:
        from app.models.learning_path import LearningPath
        from sqlalchemy import select

        result = db_session.execute(
            select(LearningPath).filter(
                LearningPath.id == learning_path_id,
                LearningPath.user_id == user_id
            )
        )

        learning_path = result.scalar_one_or_none()
        return learning_path

    except Exception as e:
        logger.error(f"Error getting learning path {learning_path_id}: {str(e)}")
        return None


def get_modules_by_learning_path_id_sync(db_session, learning_path_id: int):
    """
    Sync version of get_modules_by_learning_path_id for use in Celery tasks.
    """
    try:
        from app.models.module import Module
        from sqlalchemy import select

        result = db_session.execute(
            select(Module).filter(
                Module.learning_path_id == learning_path_id
            ).order_by(Module.order_index)
        )

        modules = result.scalars().all()
        return list(modules)

    except Exception as e:
        logger.error(f"Error getting modules for learning path {learning_path_id}: {str(e)}")
        return []


def get_quiz_by_module_id_sync(db_session, module_id: int):
    """
    Sync version of get_quiz_by_module_id for use in Celery tasks.
    """
    try:
        from app.models.quiz import Quiz
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = db_session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .filter(Quiz.module_id == module_id)
        )

        quiz = result.scalar_one_or_none()
        return quiz

    except Exception as e:
        logger.error(f"Error getting quiz for module {module_id}: {str(e)}")
        return None


async def generate_quiz_for_module_async(module_id: int, num_questions: int):
    """
    Async function to generate quiz using async session.
    """
    # FIXED: Import AsyncSessionLocal instead of async_engine
    from app.db.database import AsyncSessionLocal

    # FIXED: Use AsyncSessionLocal() to create the async session
    async with AsyncSessionLocal() as async_db:
        quiz_gen_service = QuizGenerationService(db_session=async_db)
        quiz_create = await quiz_gen_service.generate_quiz_for_module(
            module_id=module_id,
            num_questions=num_questions
        )
        await async_db.commit()
        return quiz_create


# =============================================================================
# LEARNING PATH QUIZ GENERATION TASKS
# =============================================================================

@celery_app.task(bind=True, name="generate_learning_path_quizzes")
def generate_learning_path_quizzes_task(
        self,
        learning_path_id: int,
        user_id: str,
        num_questions_per_module: int = settings.default_quiz_questions,
        stream_channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate quizzes for all modules in a learning path.

    This task creates quizzes for each module in the learning path that doesn't
    already have a quiz. It provides real-time progress updates and handles
    errors gracefully.

    Args:
        learning_path_id: ID of the learning path
        user_id: ID of the user requesting quiz generation
        num_questions_per_module: Number of questions per quiz (default: 5)
        stream_channel: Optional Redis channel for real-time updates

    Returns:
        Dict containing generation results and statistics
    """
    db_session = None

    try:
        logger.info(f"Starting quiz generation for learning path {learning_path_id}")

        # Set up database session
        db_session = get_celery_db_session()

        # Register task for tracking
        run_async_in_sync(register_quiz_task(learning_path_id, self.request.id, "learning_path_quiz_generation"))

        # Set up streaming channel
        if not stream_channel:
            stream_channel = f"quiz_generation_{user_id}"

        # Publish initial event
        publish_quiz_event(stream_channel, "quiz_generation_started", {
            "learning_path_id": learning_path_id,
            "task_id": self.request.id,
            "user_id": user_id,
            "num_questions_per_module": num_questions_per_module
        })

        # Get learning path and validate access using sync version
        learning_path = get_learning_path_by_id_sync(db_session, learning_path_id, user_id)
        if not learning_path:
            raise ValueError(f"Learning path {learning_path_id} not found or access denied")

        # Get all modules in the learning path using sync version
        modules = get_modules_by_learning_path_id_sync(db_session, learning_path_id)
        if not modules:
            raise ValueError(f"No modules found in learning path {learning_path_id}")

        logger.info(f"Found {len(modules)} modules in learning path {learning_path_id}")

        # Track generation results
        results = {
            "learning_path_id": learning_path_id,
            "total_modules": len(modules),
            "quizzes_generated": 0,
            "quizzes_skipped": 0,
            "errors": [],
            "generated_quizzes": [],
            "task_id": self.request.id
        }

        # Generate quizzes for each module
        for i, module in enumerate(modules):
            try:
                # Update progress
                progress = int((i / len(modules)) * 100)
                publish_quiz_event(stream_channel, "module_quiz_progress", {
                    "module_id": module.id,
                    "module_title": module.title,
                    "progress": progress,
                    "current_module": i + 1,
                    "total_modules": len(modules)
                })

                # Check if quiz already exists using sync version
                existing_quiz = get_quiz_by_module_id_sync(db_session, module.id)
                if existing_quiz:
                    logger.info(f"Quiz already exists for module {module.id}, skipping")
                    results["quizzes_skipped"] += 1
                    continue

                # Generate quiz for module
                logger.info(f"Generating quiz for module {module.id}: {module.title}")

                quiz_create = run_async_in_sync(
                    generate_quiz_for_module_async(module.id, num_questions_per_module)
                )

                # Get the actual persisted quiz to get the questions count using sync version
                persisted_quiz = get_quiz_by_module_id_sync(db_session, module.id)
                questions_count = len(persisted_quiz.questions) if persisted_quiz and persisted_quiz.questions else num_questions_per_module

                results["quizzes_generated"] += 1
                results["generated_quizzes"].append({
                    "module_id": module.id,
                    "quiz_id": persisted_quiz.id if persisted_quiz else 'unknown',
                    "questions_count": questions_count
                })

                # Publish module completion event
                publish_quiz_event(stream_channel, "module_quiz_completed", {
                    "module_id": module.id,
                    "module_title": module.title,
                    "quiz_id": persisted_quiz.id if persisted_quiz else 'unknown',
                    "questions_count": questions_count
                })

                logger.info(f"Successfully generated quiz for module {module.id}")

            except Exception as module_error:
                error_msg = f"Failed to generate quiz for module {module.id}: {str(module_error)}"
                logger.error(error_msg)
                results["errors"].append({
                    "module_id": module.id,
                    "module_title": module.title,
                    "error": str(module_error)
                })

                # Publish error event
                publish_quiz_event(stream_channel, "module_quiz_error", {
                    "module_id": module.id,
                    "module_title": module.title,
                    "error": str(module_error)
                })

        # Calculate final statistics
        success_rate = (results["quizzes_generated"] / results["total_modules"]) * 100 if results["total_modules"] > 0 else 0

        # Publish completion event
        publish_quiz_event(stream_channel, "quiz_generation_completed", {
            "learning_path_id": learning_path_id,
            "results": results,
            "success_rate": round(success_rate, 2),
            "summary": f"Generated {results['quizzes_generated']}/{results['total_modules']} quizzes"
        })

        logger.info(f"Quiz generation completed for learning path {learning_path_id}: "
                    f"{results['quizzes_generated']}/{results['total_modules']} quizzes generated")

        return results

    except Exception as e:
        error_msg = f"Quiz generation failed for learning path {learning_path_id}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        # Publish error event
        if stream_channel:
            publish_quiz_event(stream_channel, "quiz_generation_error", {
                "learning_path_id": learning_path_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "task_id": self.request.id
            })

        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'error_type': type(e).__name__,
                'learning_path_id': learning_path_id,
                'traceback': traceback.format_exc()
            }
        )

        raise Exception(error_msg)

    finally:
        # Clean up
        if db_session:
            db_session.close()
        run_async_in_sync(unregister_quiz_task(learning_path_id, self.request.id))


# =============================================================================
# INDIVIDUAL MODULE QUIZ GENERATION TASKS
# =============================================================================

@celery_app.task(bind=True, name="generate_module_quiz")
def generate_module_quiz_task(
        self,
        module_id: int,
        user_id: str,
        num_questions: int = 5,
        regenerate: bool = False,
        stream_channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a quiz for a specific module.

    Args:
        module_id: ID of the module
        user_id: ID of the user requesting quiz generation
        num_questions: Number of questions to generate
        regenerate: Whether to regenerate if quiz already exists
        stream_channel: Optional Redis channel for real-time updates

    Returns:
        Dict containing quiz generation results
    """
    db_session = None

    try:
        logger.info(f"Starting quiz generation for module {module_id}")

        # Set up database session
        db_session = get_celery_db_session()

        # Set up streaming channel
        if not stream_channel:
            stream_channel = f"module_quiz_generation_{user_id}_{self.request.id}"

        # Publish initial event
        publish_quiz_event(stream_channel, "module_quiz_generation_started", {
            "module_id": module_id,
            "task_id": self.request.id,
            "user_id": user_id,
            "num_questions": num_questions,
            "regenerate": regenerate
        })

        # Check if quiz already exists using sync version
        if not regenerate:
            existing_quiz = get_quiz_by_module_id_sync(db_session, module_id)
            if existing_quiz:
                result = {
                    "module_id": module_id,
                    "quiz_id": existing_quiz.id,
                    "questions_count": len(existing_quiz.questions),
                    "status": "existing",
                    "message": "Quiz already exists for this module"
                }

                publish_quiz_event(stream_channel, "module_quiz_exists", result)
                return result

        # Update progress
        publish_quiz_event(stream_channel, "module_quiz_progress", {
            "module_id": module_id,
            "progress": 25,
            "stage": "Analyzing module content"
        })

        # Generate quiz using async function
        quiz_create = run_async_in_sync(
            generate_quiz_for_module_async(module_id, num_questions)
        )

        # Update progress
        publish_quiz_event(stream_channel, "module_quiz_progress", {
            "module_id": module_id,
            "progress": 75,
            "stage": "Creating quiz in database"
        })

        # Delete existing quiz if regenerating
        if regenerate:
            existing_quiz = get_quiz_by_module_id_sync(db_session, module_id)
            if existing_quiz:
                db_session.delete(existing_quiz)
                db_session.commit()
                logger.info(f"Deleted existing quiz {existing_quiz.id} for module {module_id}")

        # Get the persisted quiz using sync version
        persisted_quiz = get_quiz_by_module_id_sync(db_session, module_id)

        result = {
            "module_id": module_id,
            "quiz_id": persisted_quiz.id if persisted_quiz else 'unknown',
            "questions_count": len(persisted_quiz.questions) if persisted_quiz and persisted_quiz.questions else num_questions,
            "status": "generated",
            "message": f"Successfully generated quiz with {num_questions} questions"
        }

        # Publish completion event
        publish_quiz_event(stream_channel, "module_quiz_generation_completed", result)

        logger.info(f"Successfully generated quiz for module {module_id}")
        return result

    except Exception as e:
        error_msg = f"Quiz generation failed for module {module_id}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        # Publish error event
        if stream_channel:
            publish_quiz_event(stream_channel, "module_quiz_generation_error", {
                "module_id": module_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "task_id": self.request.id
            })

        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'error_type': type(e).__name__,
                'module_id': module_id,
                'traceback': traceback.format_exc()
            }
        )

        raise Exception(error_msg)

    finally:
        if db_session:
            db_session.close()


# =============================================================================
# QUIZ SUBMISSION AND GRADING TASKS
# =============================================================================

@celery_app.task(bind=True, name="grade_quiz_submission")
def grade_quiz_submission_task(
        self,
        attempt_id: int,
        user_id: str,
        stream_channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Grade a submitted quiz attempt using AI-powered grading.

    This task handles both objective and subjective question grading,
    provides detailed feedback, calculates scores, and awards skill points.

    Args:
        attempt_id: ID of the quiz attempt to grade
        user_id: ID of the user who submitted the quiz
        stream_channel: Optional Redis channel for real-time updates

    Returns:
        Dict containing grading results and feedback
    """
    try:
        logger.info(f"Starting quiz grading for attempt {attempt_id}")

        # Set up streaming channel
        if not stream_channel:
            stream_channel = f"quiz_grading_{user_id}_{self.request.id}"

        # Publish initial event
        publish_quiz_event(stream_channel, "quiz_grading_started", {
            "attempt_id": attempt_id,
            "task_id": self.request.id,
            "user_id": user_id
        })

        async def run_grading():
            from app.db.database import async_engine

            async with async_engine as async_db:
                grading_service = QuizGradingService(db_session=async_db)

                publish_quiz_event(stream_channel, "quiz_grading_progress", {
                    "attempt_id": attempt_id,
                    "progress": 10,
                    "stage": "Initializing grading process"
                })

                grading_result = await grading_service.grade_quiz_attempt(attempt_id)

                publish_quiz_event(stream_channel, "quiz_grading_progress", {
                    "attempt_id": attempt_id,
                    "progress": 90,
                    "stage": "Finalizing results"
                })

                await async_db.commit()
                return grading_result

        # Run the async grading
        grading_result = run_async_in_sync(run_grading())

        # Prepare result summary
        result = {
            "attempt_id": attempt_id,
            "quiz_id": grading_result.get("quiz_id"),
            "user_id": user_id,
            "score": grading_result.get("score", 0),
            "max_score": grading_result.get("max_score", 0),
            "percentage": grading_result.get("percentage", 0),
            "passed": grading_result.get("passed", False),
            "skill_points_awarded": grading_result.get("skill_points_awarded", 0),
            "questions_graded": grading_result.get("questions_graded", 0),
            "correct_answers": grading_result.get("correct_answers", 0),
            "grading_time_seconds": grading_result.get("grading_time_seconds", 0),
            "overall_feedback": grading_result.get("overall_feedback", ""),
            "status": "completed"
        }

        # Publish completion event
        publish_quiz_event(stream_channel, "quiz_grading_completed", {
            **result,
            "message": f"Quiz graded successfully - {result['percentage']:.1f}% ({result['score']}/{result['max_score']})"
        })

        logger.info(f"Successfully graded quiz attempt {attempt_id}: "
                    f"{result['score']}/{result['max_score']} ({result['percentage']:.1f}%)")

        return result

    except Exception as e:
        error_msg = f"Quiz grading failed for attempt {attempt_id}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        # Publish error event
        if stream_channel:
            publish_quiz_event(stream_channel, "quiz_grading_error", {
                "attempt_id": attempt_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "task_id": self.request.id
            })

        # Update task state
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'error_type': type(e).__name__,
                'attempt_id': attempt_id,
                'traceback': traceback.format_exc()
            }
        )

        raise Exception(error_msg)
