"""
Progress Repository

This module provides data access methods for progress operations.
Handles all database interactions for user progress tracking, module completion,
quiz completion, and skill point awards.
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, select
from sqlalchemy.orm import contains_eager
from datetime import datetime

from app.core.logger import get_logger
from app.core.config import settings
from app.models.progress import Progress, ModuleProgress
from app.models.user import User
from app.models.quiz import QuizAttempt, Quiz, Answer
from app.models.module import Module
from app.schemas.core_schemas.learning_path_schema import ModuleProgressInfo

logger = get_logger(__name__)


async def is_module_completed(db: AsyncSession, module_id: int, user_id: str) -> bool:
    """
    Check if a module is already completed by a user.

    Args:
        db: Database session
        module_id: ID of the module to check
        user_id: ID of the user

    Returns:
        True if module is completed, False otherwise
    """
    logger.debug(f"Checking if module {module_id} is completed by user {user_id}")

    try:
        result = await db.execute(select(ModuleProgress).filter(
            and_(
                ModuleProgress.module_id == module_id,
                ModuleProgress.user_id == user_id,
                ModuleProgress.is_completed == True
            )
        ))
        progress = result.scalar_one_or_none()

        is_completed = progress is not None
        logger.debug(f"Module {module_id} completion status for user {user_id}: {is_completed}")
        return is_completed

    except Exception as e:
        logger.error(f"Error checking module completion for module {module_id}, user {user_id}: {str(e)}")
        raise


async def get_module_completion(db: AsyncSession, module_id: int, user_id: str) -> Dict[str, Any]:
    """
    Get existing module completion data.

    Args:
        db: Database session
        module_id: ID of the module
        user_id: ID of the user

    Returns:
        Dictionary with completion details
    """
    logger.debug(f"Getting module completion data for module {module_id}, user {user_id}")

    try:
        result = await db.execute(select(ModuleProgress).filter(
            and_(
                ModuleProgress.module_id == module_id,
                ModuleProgress.user_id == user_id
            )
        ))
        progress = result.scalar_one_or_none()

        if not progress:
            logger.warning(f"No progress record found for module {module_id}, user {user_id}")
            return {
                "completed_at": None,
                "skill_points_awarded": 0,
                "learning_path_progress_updated": False,
                "new_completion_percentage": 0.0
            }

        return {
            "completed_at": progress.completed_at,
            "skill_points_awarded": settings.default_module_skill_points if progress.is_completed else 0,
            "learning_path_progress_updated": True,
            "new_completion_percentage": 0.0  # Will be calculated separately
        }

    except Exception as e:
        logger.error(f"Error getting module completion for module {module_id}, user {user_id}: {str(e)}")
        raise


async def mark_module_complete(db: AsyncSession, completion_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark a module as completed and update database records.

    Args:
        db: Database session
        completion_data: Dictionary containing completion information

    Returns:
        Dictionary with completion result details
    """
    module_id = completion_data["module_id"]
    user_id = completion_data["user_id"]
    completed_at = completion_data["completed_at"]
    time_spent_minutes = completion_data.get("time_spent_minutes", 0)

    logger.info(f"Marking module {module_id} as complete for user {user_id}")

    try:
        # Get or create module progress record
        result = await db.execute(select(ModuleProgress).filter(
            and_(
                ModuleProgress.module_id == module_id,
                ModuleProgress.user_id == user_id
            )
        ))
        progress = result.scalar_one_or_none()

        if not progress:
            # Create new progress record
            progress = ModuleProgress(user_id=user_id, module_id=module_id)
            db.add(progress)

        # Mark as completed
        progress.mark_completed(time_spent_minutes)

        # Update user skill points
        user_result = await db.execute(select(User).filter(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.skill_points += settings.default_module_skill_points
            logger.info(f"Added {settings.default_module_skill_points} skill points to user {user_id}")

        await db.commit()

        logger.info(f"Successfully marked module {module_id} as complete for user {user_id}")

        return {
            "completed_at": completed_at,
            "skill_points_awarded": settings.default_module_skill_points,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error marking module {module_id} as complete for user {user_id}: {str(e)}")
        await db.rollback()
        raise


async def award_skill_points_for_module(db: AsyncSession, module_id: int, user_id: str) -> int:
    """
    Award skill points for module completion.

    Args:
        db: Database session
        module_id: ID of the completed module
        user_id: ID of the user

    Returns:
        Number of skill points awarded
    """
    logger.info(f"Awarding skill points for module {module_id} completion by user {user_id}")

    try:
        # Check if already completed (should not award duplicate points)
        result = await db.execute(select(ModuleProgress).filter(
            and_(
                ModuleProgress.module_id == module_id,
                ModuleProgress.user_id == user_id,
                ModuleProgress.is_completed == True
            )
        ))
        progress = result.scalar_one_or_none()

        if not progress:
            logger.warning(f"Module {module_id} not marked as completed for user {user_id}")
            return 0

        # Award skill points (already handled in mark_module_complete)
        logger.info(
            f"Awarded {settings.default_module_skill_points} skill points for module {module_id} to user {user_id}")
        return settings.default_module_skill_points

    except Exception as e:
        logger.error(f"Error awarding skill points for module {module_id}, user {user_id}: {str(e)}")
        raise


async def award_quiz_skill_points(
        db: AsyncSession,
        user_id: str,
        quiz_id: int,
        score: float
) -> int:
    """
    Award skill points for quiz completion (only for passing scores and first-time passes).

    Args:
        db: Database session
        user_id: ID of the user
        quiz_id: ID of the quiz
        score: Quiz score percentage

    Returns:
        Number of skill points awarded (0 if not eligible)
    """
    logger.info(f"Processing skill points for quiz {quiz_id} completion by user {user_id} (score: {score:.1f}%)")

    try:
        # Check if user has already been awarded skill points for this quiz
        existing_result = await db.execute(select(QuizAttempt).filter(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.skill_points_awarded == True
            )
        ))
        existing_passed_attempt = existing_result.scalar_one_or_none()

        if existing_passed_attempt:
            logger.info(f"User {user_id} already awarded skill points for quiz {quiz_id}")
            return 0

        # Award skill points to user
        user_result = await db.execute(select(User).filter(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.skill_points += settings.default_quiz_skill_points
            logger.info(f"Added {settings.default_quiz_skill_points} skill points to user {user_id} for quiz {quiz_id}")

        await db.commit()

        return settings.default_quiz_skill_points

    except Exception as e:
        logger.error(f"Error awarding quiz skill points for quiz {quiz_id}, user {user_id}: {str(e)}")
        await db.rollback()
        raise


async def get_learning_path_progress(db: AsyncSession, learning_path_id: int, user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive learning path progress for a user.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user

    Returns:
        Dictionary with detailed progress information
    """
    logger.debug(f"Getting learning path progress for path {learning_path_id}, user {user_id}")

    try:
        # Get or create overall progress record
        progress_result = await db.execute(select(Progress).filter(
            and_(
                Progress.learning_path_id == learning_path_id,
                Progress.user_id == user_id
            )
        ))
        progress = progress_result.scalar_one_or_none()

        if not progress:
            # Create new progress record
            progress = Progress(user_id=user_id, learning_path_id=learning_path_id)
            db.add(progress)
            await db.commit()

        # Get module progress statistics
        total_modules_result = await db.execute(select(func.count(Module.id)).filter(Module.learning_path_id == learning_path_id))
        total_modules = total_modules_result.scalar()

        completed_modules_result = await db.execute(select(ModuleProgress.module_id).join(Module).filter(
            and_(
                Module.learning_path_id == learning_path_id,
                ModuleProgress.user_id == user_id,
                ModuleProgress.is_completed == True
            )
        ))
        completed_module_ids = [row[0] for row in completed_modules_result.all()]
        completed_modules_count = len(completed_module_ids)

        # Calculate questions answered correctly across all quizzes in this learning path
        questions_result = await db.execute(select(func.count(Answer.id)).join(
            QuizAttempt, Answer.attempt_id == QuizAttempt.id
        ).join(
            Quiz, QuizAttempt.quiz_id == Quiz.id
        ).join(
            Module, Quiz.module_id == Module.id
        ).filter(
            and_(
                Module.learning_path_id == learning_path_id,
                QuizAttempt.user_id == user_id,
                Answer.is_correct == True
            )
        ))
        questions_answered_correctly = questions_result.scalar() or 0

        # Calculate total time spent
        time_result = await db.execute(select(func.sum(ModuleProgress.time_spent_minutes)).join(Module).filter(
            and_(
                Module.learning_path_id == learning_path_id,
                ModuleProgress.user_id == user_id
            )
        ))
        total_time_spent = time_result.scalar() or 0

        # Calculate skill points earned for this learning path
        # Module skill points
        module_skill_points = completed_modules_count * settings.default_module_skill_points
        
        # Quiz skill points for this learning path
        quiz_result = await db.execute(select(func.count(QuizAttempt.id)).join(
            Quiz, QuizAttempt.quiz_id == Quiz.id
        ).join(
            Module, Quiz.module_id == Module.id
        ).filter(
            and_(
                Module.learning_path_id == learning_path_id,
                QuizAttempt.user_id == user_id,
                QuizAttempt.skill_points_awarded == True
            )
        ))
        quiz_skill_points = (quiz_result.scalar() or 0) * settings.default_quiz_skill_points
        
        # Total skill points for this learning path
        skill_points_earned = module_skill_points + quiz_skill_points

        # Calculate completion percentage
        completion_percentage = (completed_modules_count / total_modules * 100) if total_modules > 0 else 0

        return {
            "completion_percentage": completion_percentage,
            "completed_modules": completed_module_ids,  # ← Now returns list of IDs
            "total_modules": total_modules,
            "total_time_spent_minutes": total_time_spent,
            "skill_points_earned": skill_points_earned,
            "questions_answered_correctly": questions_answered_correctly,
            "started_at": progress.started_at,
            "last_activity_at": progress.last_updated_at
        }

    except Exception as e:
        logger.error(f"Error getting learning path progress for path {learning_path_id}, user {user_id}: {str(e)}")
        raise


async def recalculate_learning_path_progress(db: AsyncSession, learning_path_id: int, user_id: str) -> Dict[str, Any]:
    """
    Recalculate and update learning path completion percentage.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user

    Returns:
        Dictionary with updated progress information
    """
    logger.info(f"Recalculating learning path progress for path {learning_path_id}, user {user_id}")

    try:
        # Get current progress data
        progress_data = await get_learning_path_progress(db, learning_path_id, user_id)

        # Update the progress record
        progress_result = await db.execute(select(Progress).filter(
            and_(
                Progress.learning_path_id == learning_path_id,
                Progress.user_id == user_id
            )
        ))
        progress = progress_result.scalar_one_or_none()

        if progress:
            progress.completion_percentage = progress_data["completion_percentage"]
            progress.last_updated_at = datetime.now()

            # Check if learning path is now completed
            if progress_data["completion_percentage"] >= 100.0 and not progress.completed_at:
                progress.mark_completed()

                # Award learning path completion skill points
                user_result = await db.execute(select(User).filter(User.id == user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    user.skill_points += settings.default_path_skill_points
                    logger.info(
                        f"Awarded {settings.default_path_skill_points} skill points for completing learning path {learning_path_id}")

            await db.commit()

        logger.info(f"Updated learning path {learning_path_id} progress: {progress_data['completion_percentage']:.1f}%")

        return {
            "completion_percentage": progress_data["completion_percentage"],
            "is_completed": progress_data["completion_percentage"] >= 100.0
        }

    except Exception as e:
        logger.error(
            f"Error recalculating learning path progress for path {learning_path_id}, user {user_id}: {str(e)}")
        await db.rollback()
        raise


async def get_module_progress_for_learning_path(db: AsyncSession, learning_path_id: int, user_id: str) -> List[ModuleProgressInfo]:
    """
    Get detailed module progress for all modules in a learning path.
    """
    logger.debug(f"Getting module progress for learning path {learning_path_id}, user {user_id}")

    try:
        # Eagerly load the progress_records relationship using the joined data
        modules_result = await db.execute(
            select(Module)
            .outerjoin(
                ModuleProgress,
                and_(
                    ModuleProgress.module_id == Module.id,
                    ModuleProgress.user_id == user_id
                )
            )
            .options(contains_eager(Module.progress_records))  # <-- FIX APPLIED HERE
            .filter(Module.learning_path_id == learning_path_id)
            .order_by(Module.order_index)
        )
        modules_with_progress = modules_result.scalars().unique().all()

        module_progress_list = []
        for module in modules_with_progress:
            # The progress_records collection will now be populated correctly
            progress_record = module.progress_records[0] if module.progress_records else None

            # Create ModuleProgressInfo object directly
            module_info = ModuleProgressInfo(
                id=module.id,
                title=module.title,
                order_index=module.order_index,
                is_completed=progress_record.is_completed if progress_record else False,
                completed_at=progress_record.completed_at if progress_record else None,
                time_spent_minutes=progress_record.time_spent_minutes if progress_record else None,
                difficulty=module.difficulty.value if module.difficulty else "intermediate",
                learning_style=module.learning_style[0] if module.learning_style else "visual"
            )

            # Validate required fields
            if module_info.difficulty is None:
                raise ValueError(f"Module {module.id} is missing required difficulty field")

            if module_info.learning_style is None:
                raise ValueError(f"Module {module.id} is missing required learning_style field")

            module_progress_list.append(module_info)

        logger.debug(f"Retrieved progress for {len(module_progress_list)} modules in learning path {learning_path_id}")
        return module_progress_list

    except Exception as e:
        logger.error(f"Error getting module progress for learning path {learning_path_id}, user {user_id}: {str(e)}")
        raise
