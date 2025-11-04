"""
Module Service

This module provides business logic for module operations.
All methods use repository pattern for data access abstraction.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.logger import get_logger
from app.schemas.core_schemas.module_schema import ModuleResponse
from app.repositories import module_repository, progress_repository

logger = get_logger(__name__)


async def get_module_by_id(db: AsyncSession, module_id: int) -> Optional[ModuleResponse]:
    """
    Get module by ID.

    Args:
        db: Database session
        module_id: ID of the module to retrieve

    Returns:
        ModuleResponse object or None if not found
    """
    logger.info(f"Getting module {module_id}")

    try:
        module = await module_repository.get_by_id(db, module_id)

        if not module:
            logger.warning(f"Module {module_id} not found")
            return None

        logger.info(f"Successfully retrieved module {module_id}: {module.title}")
        return module

    except Exception as e:
        logger.error(f"Error getting module {module_id}: {str(e)}")
        raise


async def get_modules_by_learning_path_id(db: AsyncSession, learning_path_id: int) -> List[ModuleResponse]:
    """
    Get all modules for a specific learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path

    Returns:
        List of ModuleResponse objects ordered by order_index
    """
    logger.info(f"Getting modules for learning path {learning_path_id}")

    try:
        modules = await module_repository.get_by_learning_path_id(db, learning_path_id)
        logger.info(f"Retrieved {len(modules)} modules for learning path {learning_path_id}")
        return modules

    except Exception as e:
        logger.error(f"Error getting modules for learning path {learning_path_id}: {str(e)}")
        raise


async def delete_module(db: AsyncSession, module_id: int) -> Dict[str, Any]:
    """
    Delete a module and all its associated data.

    Args:
        db: Database session
        module_id: ID of the module to delete

    Returns:
        Dictionary with deletion statistics
    """
    logger.info(f"Deleting module {module_id}")

    try:
        deletion_result = await module_repository.delete_with_cascade(db, module_id)

        logger.info(f"Successfully deleted module {module_id}. "
                   f"Deleted {deletion_result['deleted_quizzes_count']} associated quizzes")

        return deletion_result

    except Exception as e:
        logger.error(f"Error deleting module {module_id}: {str(e)}")
        raise


async def mark_module_complete(
    db: AsyncSession,
    module_id: int,
    user_id: str,
    completion_notes: Optional[str] = None,
    time_spent_minutes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Mark a module as completed for a user and update progress tracking.

    Args:
        db: Database session
        module_id: ID of the module to mark as complete
        user_id: ID of the user completing the module
        completion_notes: Optional notes about the completion
        time_spent_minutes: Optional time spent on the module

    Returns:
        Dictionary with completion details including skill points and updated progress
    """
    logger.info(f"Marking module {module_id} as complete for user {user_id}")

    try:
        # Check if module is already completed to avoid duplicate processing
        is_already_completed = await progress_repository.is_module_completed(db, module_id, user_id)

        if is_already_completed:
            logger.warning(f"Module {module_id} already completed by user {user_id}")
            # Return existing completion data
            existing_completion = await progress_repository.get_module_completion(db, module_id, user_id)
            return existing_completion

        # Mark module as completed
        completion_data = {
            "module_id": module_id,
            "user_id": user_id,
            "completed_at": datetime.now(),
            "completion_notes": completion_notes,
            "time_spent_minutes": time_spent_minutes or 0
        }

        # Process completion and calculate rewards
        completion_result = await progress_repository.mark_module_complete(db, completion_data)

        # Update learning path completion percentage
        learning_path_id = await module_repository.get_learning_path_id_by_module(db, module_id)
        updated_progress = await progress_repository.recalculate_learning_path_progress(
            db, learning_path_id, user_id
        )

        # Calculate skill points awarded based on module difficulty and user performance
        skill_points = await progress_repository.award_skill_points_for_module(db, module_id, user_id)

        result = {
            "completed_at": completion_result["completed_at"],
            "skill_points_awarded": skill_points,
            "learning_path_progress_updated": True,
            "new_completion_percentage": updated_progress["completion_percentage"]
        }

        logger.info(f"Module {module_id} marked complete for user {user_id}. "
                   f"Awarded {skill_points} skill points. "
                   f"Learning path progress: {result['new_completion_percentage']}%")

        return result

    except Exception as e:
        logger.error(f"Error marking module {module_id} as complete for user {user_id}: {str(e)}")
        raise


async def get_platform_id_by_name(db: AsyncSession, platform_name: str) -> Optional[int]:
    """
    Get a platform by its ID.

    Args:
        db: Database session
        platform_name: name of the platform to retrieve

    Returns:
        The platform object if found, None otherwise
    """
    result = await module_repository.get_platform_id_by_name(db, platform_name)
    if not result:
        logger.warning(f"Platform {platform_name} not found")
        return None
    logger.info(f"Retrieved platform id {platform_name}: {result}")
    return result