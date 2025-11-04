"""
Progress Service

This module provides business logic for progress operations.
All methods use repository pattern for data access abstraction.
Handles module completion, quiz completion skill point awards, and progress tracking.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.repositories import progress_repository

logger = get_logger(__name__)


async def award_skill_points_for_module(db: AsyncSession, module_id: int, user_id: str) -> int:
    """
    Award skill points for module completion.

    This method is called from module_service.mark_module_complete()
    to award skill points when a user completes a module.

    Args:
        db: Database session
        module_id: ID of the completed module
        user_id: ID of the user who completed the module

    Returns:
        Number of skill points awarded
    """
    logger.info(f"Processing skill point award for module {module_id} completion by user {user_id}")

    try:
        # Check if module is actually completed to prevent duplicate awards
        is_completed = await progress_repository.is_module_completed(db, module_id, user_id)

        if not is_completed:
            logger.warning(f"Module {module_id} not marked as completed for user {user_id}, no skill points awarded")
            return 0

        # Award skill points through repository
        skill_points = await progress_repository.award_skill_points_for_module(db, module_id, user_id)

        logger.info(f"Successfully awarded {skill_points} skill points for module {module_id} to user {user_id}")
        return skill_points

    except Exception as e:
        logger.error(f"Error awarding skill points for module {module_id}, user {user_id}: {str(e)}")
        raise


async def award_quiz_skill_points(db: AsyncSession, user_id: str, quiz_id: int, score: float) -> int:
    """
    Award skill points for quiz completion (only for passing scores and first-time passes).

    This method is called from quiz_service.submit_quiz_attempt()
    when a user passes a quiz for the first time.

    Args:
        db: Database session
        user_id: ID of the user who completed the quiz
        quiz_id: ID of the completed quiz
        score: Quiz score percentage

    Returns:
        Number of skill points awarded (0 if not eligible)
    """
    logger.info(f"Processing skill point award for quiz {quiz_id} completion by user {user_id} (score: {score:.1f}%)")

    try:
        # Only award points for passing scores
        if score < 66.6:  # Based on default_quiz_passing_score setting
            logger.info(f"Quiz {quiz_id} score {score:.1f}% below passing threshold, no skill points awarded")
            return 0

        # Award skill points through repository (handles duplicate prevention)
        skill_points = await progress_repository.award_quiz_skill_points(db, user_id, quiz_id, score)

        if skill_points > 0:
            logger.info(f"Successfully awarded {skill_points} skill points for quiz {quiz_id} to user {user_id}")
        else:
            logger.info(
                f"No skill points awarded for quiz {quiz_id} to user {user_id} (already awarded or not eligible)")

        return skill_points

    except Exception as e:
        logger.error(f"Error awarding quiz skill points for quiz {quiz_id}, user {user_id}: {str(e)}")
        raise
