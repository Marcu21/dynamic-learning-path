"""
Learning Path Service

This module provides business logic for learning path operations.
All methods use repository pattern for data access abstraction.
"""

from typing import List, Dict, Any, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models import LearningPath, Progress, Module
from app.schemas.core_schemas.learning_path_schema import (
    LearningPathResponse,
    TeamLearningPathResponse,
    LearningPathProgressResponse,
)
from app.repositories import learning_path_repository, progress_repository

logger = get_logger(__name__)


async def get_learning_path_by_id(db: AsyncSession, learning_path_id: int, user_id: str) -> Optional[LearningPathResponse]:
    """
    Get learning path by ID with user access validation.

    Args:
        db: Database session
        learning_path_id: ID of the learning path to retrieve
        user_id: ID of the user requesting access

    Returns:
        LearningPathResponse object or None if not found/no access
    """
    logger.info(f"Getting learning path {learning_path_id} for user {user_id}")

    try:
        # Get learning path from repository
        learning_path = await learning_path_repository.get_by_id(db, learning_path_id)

        if not learning_path:
            logger.warning(f"Learning path {learning_path_id} not found")
            return None

        # Check user access permissions
        if not await user_has_access_to_learning_path(db, learning_path_id, user_id):
            logger.warning(f"User {user_id} denied access to learning path {learning_path_id}")
            return None

        logger.info(f"Successfully retrieved learning path {learning_path_id}")
        return learning_path

    except Exception as e:
        logger.error(f"Error getting learning path {learning_path_id}: {str(e)}")
        raise


async def get_user_learning_paths(db: AsyncSession, user_id: str) -> List[LearningPathResponse]:
    """
    Get all learning paths for a specific user.

    Args:
        db: Database session
        user_id: ID of the user to get learning paths for

    Returns:
        List of LearningPathResponse objects
    """
    logger.info(f"Getting learning paths for user {user_id}")

    try:
        learning_paths = await learning_path_repository.get_by_user_id(db, user_id)
        logger.info(f"Retrieved {len(learning_paths)} learning paths for user {user_id}")
        return learning_paths

    except Exception as e:
        logger.error(f"Error getting learning paths for user {user_id}: {str(e)}")
        raise


async def get_team_learning_paths(db: AsyncSession, team_id: str) -> List[TeamLearningPathResponse]:
    """
    Get all learning paths for a specific team.

    Args:
        db: Database session
        team_id: ID of the team to get learning paths for

    Returns:
        List of TeamLearningPathResponse objects
    """
    logger.info(f"Getting team learning paths for team {team_id}")

    try:
        team_learning_paths = await learning_path_repository.get_by_team_id(db, team_id)
        logger.info(f"Retrieved {len(team_learning_paths)} learning paths for team {team_id}")
        return team_learning_paths

    except Exception as e:
        logger.error(f"Error getting team learning paths for team {team_id}: {str(e)}")
        raise


async def user_has_access_to_learning_path(db: AsyncSession, learning_path_id: int, user_id: str) -> bool:
    """
    Check if user has access to a specific learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user to check access for

    Returns:
        True if user has access, False otherwise
    """
    logger.debug(f"Checking access for user {user_id} to learning path {learning_path_id}")

    try:
        has_access = await learning_path_repository.user_has_access(db, learning_path_id, user_id)
        logger.debug(f"User {user_id} access to learning path {learning_path_id}: {has_access}")
        return has_access

    except Exception as e:
        logger.error(f"Error checking access for user {user_id} to learning path {learning_path_id}: {str(e)}")
        return False


async def user_can_modify_learning_path(db: AsyncSession, learning_path_id: int, user_id: str) -> bool:
    """
    Check if user can modify a specific learning path (owner or team lead).

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user to check permissions for

    Returns:
        True if user can modify, False otherwise
    """
    logger.debug(f"Checking modify permissions for user {user_id} on learning path {learning_path_id}")

    try:
        can_modify = await learning_path_repository.user_can_modify(db, learning_path_id, user_id)
        logger.debug(f"User {user_id} can modify learning path {learning_path_id}: {can_modify}")
        return can_modify

    except Exception as e:
        logger.error(f"Error checking modify permissions for user {user_id} on learning path {learning_path_id}: {str(e)}")
        return False


async def user_can_delete_learning_path(db: AsyncSession, learning_path_id: int, user_id: str) -> bool:
    """
    Check if user can delete a specific learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user to check permissions for

    Returns:
        True if user can delete, False otherwise
    """
    logger.debug(f"Checking delete permissions for user {user_id} on learning path {learning_path_id}")

    try:
        can_delete = await learning_path_repository.user_can_delete(db, learning_path_id, user_id)
        logger.debug(f"User {user_id} can delete learning path {learning_path_id}: {can_delete}")
        return can_delete

    except Exception as e:
        logger.error(f"Error checking delete permissions for user {user_id} on learning path {learning_path_id}: {str(e)}")
        return False


async def delete_learning_path(db: AsyncSession, learning_path_id: int) -> Dict[str, Any]:
    """
    Delete a learning path and all its associated data.

    Args:
        db: Database session
        learning_path_id: ID of the learning path to delete

    Returns:
        Dictionary with deletion statistics
    """
    logger.info(f"Deleting learning path {learning_path_id}")

    try:
        deletion_result = await learning_path_repository.delete_with_cascade(db, learning_path_id)

        logger.info(f"Successfully deleted learning path {learning_path_id}. "
                   f"Deleted {deletion_result['deleted_modules_count']} modules, "
                   f"{deletion_result['deleted_quizzes_count']} quizzes, "
                   f"affected {len(deletion_result['affected_users'])} users")

        return deletion_result

    except Exception as e:
        logger.error(f"Error deleting learning path {learning_path_id}: {str(e)}")
        raise


async def get_learning_path_progress(db: AsyncSession, learning_path_id: int, user_id: str) -> LearningPathProgressResponse:
    """
    Get detailed learning path progress for a specific user.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user to get progress for

    Returns:
        LearningPathProgressResponse with detailed progress information
    """
    logger.info(f"Getting learning path progress for path {learning_path_id}, user {user_id}")

    try:
        # Get overall progress data
        progress_data = await progress_repository.get_learning_path_progress(db, learning_path_id, user_id)

        # Get detailed module progress
        module_progress = await progress_repository.get_module_progress_for_learning_path(
            db, learning_path_id, user_id
        )

        # Build response with all progress details
        response = LearningPathProgressResponse(
            learning_path_id=learning_path_id,
            user_id=user_id,
            completion_percentage=progress_data["completion_percentage"],
            completed_modules=progress_data["completed_modules"],
            total_modules=progress_data["total_modules"],
            modules=module_progress,
            total_time_spent_minutes=progress_data["total_time_spent_minutes"],
            skill_points_earned=progress_data["skill_points_earned"],
            questions_answered=progress_data["questions_answered_correctly"],
            started_at=progress_data["started_at"],
            last_activity_at=progress_data["last_activity_at"]
        )

        logger.info(f"Retrieved progress for learning path {learning_path_id}: "
                   f"{response.completion_percentage}% complete, "
                   f"{len(response.completed_modules)}/{response.total_modules} modules")

        return response

    except Exception as e:
        logger.error(f"Error getting learning path progress for path {learning_path_id}, user {user_id}: {str(e)}")
        raise


async def validate_learning_path_access(db: AsyncSession, learning_path_id: int, user_id: str) -> bool:
    """
    Validate if a user has access to a specific learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user to validate access for

    Returns:
        True if user has access, False otherwise
    """
    logger.debug(f"Validating access for user {user_id} to learning path {learning_path_id}")

    try:
        # Use the existing repository method for access validation
        has_access = await learning_path_repository.user_has_access(db, learning_path_id, user_id)

        if has_access:
            logger.debug(f"User {user_id} has access to learning path {learning_path_id}")
        else:
            logger.warning(f"User {user_id} denied access to learning path {learning_path_id}")

        return has_access

    except Exception as e:
        logger.error(f"Error validating access for user {user_id} to learning path {learning_path_id}: {str(e)}")
        return False


async def get_learning_path_preferences(db: AsyncSession, learning_path_id: int) -> Optional[object]:
    """
    Get preferences associated with a specific learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path

    Returns:
        Raw preferences object or None if not found
    """
    logger.info(f"Getting preferences for learning path {learning_path_id}")

    try:
        learning_path = await learning_path_repository.get_by_id(db, learning_path_id)

        if not learning_path:
            logger.warning(f"Learning path {learning_path_id} not found when getting preferences")
            return None

        from app.repositories import preferences_repository
        preferences = await preferences_repository.get_by_id(db, learning_path.preferences_id)

        if not preferences:
            logger.warning(f"No preferences found for learning path {learning_path_id}")
            return None

        logger.info(f"Retrieved preferences for learning path {learning_path_id}")
        # Return raw preferences object, let the API endpoint handle validation
        return preferences

    except Exception as e:
        logger.error(f"Error getting preferences for learning path {learning_path_id}: {str(e)}")
        raise


async def get_personal_learning_paths(db: AsyncSession, user_id: str) -> List[LearningPathResponse]:
    """
    Get all personal learning paths for a specific user.

    Args:
        db: Database session
        user_id: ID of the user to get personal learning paths for

    Returns:
        List of LearningPathResponse objects
    """
    logger.info(f"Getting personal learning paths for user {user_id}")

    try:
        all_paths = await get_user_learning_paths(db, user_id)
        team_paths = await get_team_learning_paths(db, user_id)

        # Extract IDs from team paths for comparison
        team_path_ids = {team_path.id for team_path in
                         team_paths}

        # Filter out paths that are in team paths
        personal_learning_paths = [
            path for path in all_paths
            if path.id not in team_path_ids
        ]

        logger.info(f"Retrieved {len(personal_learning_paths)} personal learning paths for user {user_id}")
        return personal_learning_paths

    except Exception as e:
        logger.error(f"Error getting personal learning paths for user {user_id}: {str(e)}")
        raise


async def get_team_learning_paths_with_user_progress(
        db: AsyncSession,
        team_id: str,
        user_id: str
) -> List[TeamLearningPathResponse]:
    """
    Get all learning paths for a team with the current user's progress.

    Args:
        db: Database session
        team_id: ID of the team to get learning paths for
        user_id: ID of the current user to get progress for

    Returns:
        List of TeamLearningPathResponse objects with user's completion_percentage
    """
    logger.info(f"Getting team learning paths with user progress for team {team_id}, user {user_id}")

    try:
        # Get team learning paths with user progress in a single query
        result = await db.execute(
            select(LearningPath, Progress, func.count(Module.id).label('total_modules'))
            .outerjoin(Progress, and_(
                Progress.learning_path_id == LearningPath.id,
                Progress.user_id == user_id
            ))
            .outerjoin(Module, Module.learning_path_id == LearningPath.id)
            .filter(LearningPath.team_id == team_id)
            .group_by(LearningPath.id, Progress.id)
            .order_by(LearningPath.created_at.desc())
        )

        paths_with_progress = []
        for learning_path, progress, total_modules in result.all():
            # Create response object with user's progress
            path_response = TeamLearningPathResponse(
                id=learning_path.id,
                title=learning_path.title,
                description=learning_path.description,
                user_id=learning_path.user_id,
                team_id=learning_path.team_id,
                estimated_days=learning_path.estimated_days,
                is_public=learning_path.is_public,
                total_modules=total_modules or 0,
                # Set completion_percentage to user's progress, default to 0.0 if no progress
                completion_percentage=progress.completion_percentage if progress else 0.0,
                created_at=learning_path.created_at,
                updated_at=learning_path.updated_at
            )

            paths_with_progress.append(path_response)

        logger.info(f"Retrieved {len(paths_with_progress)} learning paths with user progress for team {team_id}")
        return paths_with_progress

    except Exception as e:
        logger.error(f"Error getting team learning paths with user progress for team {team_id}: {str(e)}")
        raise
