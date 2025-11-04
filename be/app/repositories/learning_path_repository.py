"""
Learning Path Repository

This module provides data access methods for learning path operations.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import joinedload

from app.core.logger import get_logger
from app.models import Preferences
from app.models.learning_path import LearningPath
from app.models.module import Module
from app.models.team_member import TeamMember
from app.models.enums import TeamMemberRole
from app.schemas.core_schemas.learning_path_schema import LearningPathResponse, TeamLearningPathResponse, \
    LearningPathCreate

logger = get_logger(__name__)


def create_learning_path(db, learning_path_data: LearningPathCreate) -> LearningPathResponse:
   """
   Create a new learning path (works with both sync and async sessions).

   Args:
       db: Database session (sync or async)
       learning_path_data: Learning path creation data

   Returns:
       LearningPathResponse object with created learning path details
   """
   logger.info(f"Creating learning path: {getattr(learning_path_data, 'title')} for user {getattr(learning_path_data, 'user_id')}")

   # Detect if this is an async session
   is_async = hasattr(db, '__aenter__') or str(type(db)).find('AsyncSession') != -1

   try:
       # Create learning path instance
       learning_path = LearningPath(
           user_id=getattr(learning_path_data, 'user_id'),
           title=getattr(learning_path_data, 'title'),
           description=getattr(learning_path_data, 'description'),
           estimated_days=getattr(learning_path_data, 'estimated_days'),
           team_id=getattr(learning_path_data, 'team_id'),
           preferences_id=getattr(learning_path_data, 'preferences_id')
       )

       db.add(learning_path)
       
       if is_async:
           raise ValueError("Async sessions not supported - use sync session from Celery")
       else:
           db.flush()  # Get the learning path ID (sync version)
           db.commit()

       # Build response object
       learning_path_response = LearningPathResponse(
           id=learning_path.id,
           user_id=learning_path.user_id,
           title=learning_path.title,
           description=learning_path.description,
           estimated_days=learning_path.estimated_days,
           completion_percentage=0.0,  # New learning path starts at 0%
           created_at=learning_path.created_at,
           updated_at=learning_path.updated_at
       )

       logger.info(f"Created learning path {learning_path.id}: {learning_path.title}")
       return learning_path_response

   except Exception as e:
       logger.error(f"Error creating learning path {getattr(learning_path_data, 'title')}: {str(e)}")
       if is_async:
           raise ValueError("Async sessions not supported - use sync session from Celery")
       else:
           db.rollback()
       raise

async def get_by_id(db: AsyncSession, learning_path_id: int) -> Optional[LearningPathResponse]:
    """
    Get learning path by ID.

    Args:
        db: Database session
        learning_path_id: ID of the learning path

    Returns:
        LearningPathResponse object or None if not found
    """
    logger.debug(f"Getting learning path by ID: {learning_path_id}")

    try:
        result = await db.execute(select(LearningPath).options(
            joinedload(LearningPath.progress_records)
        ).filter(LearningPath.id == learning_path_id))
        learning_path = result.unique().scalar_one_or_none()

        if not learning_path:
            return None

        # Compute completion percentage manually to avoid lazy loading
        if learning_path.progress_records:
            total_completion = sum(p.completion_percentage for p in learning_path.progress_records)
            completion_percentage = total_completion / len(learning_path.progress_records)
        else:
            completion_percentage = 0.0

        return LearningPathResponse(
            id=learning_path.id,
            user_id=learning_path.user_id,
            title=learning_path.title,
            description=learning_path.description,
            estimated_days=learning_path.estimated_days,
            completion_percentage=completion_percentage,
            preferences_id=learning_path.preferences_id,
            created_at=learning_path.created_at,
            updated_at=learning_path.updated_at
        )

    except Exception as e:
        logger.error(f"Error getting learning path {learning_path_id}: {str(e)}")
        raise


async def get_by_user_id(db: AsyncSession, user_id: str) -> List[LearningPathResponse]:
    """
    Get all personal learning paths for a user (excludes team paths).

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of LearningPathResponse objects for personal paths only
    """
    logger.debug(f"Getting personal learning paths for user: {user_id}")

    try:
        # Filter by user_id AND team_id is NULL to get only personal paths
        # Eagerly load progress_records to avoid lazy loading issues
        result = await db.execute(select(LearningPath).options(
            joinedload(LearningPath.progress_records)
        ).filter(
            and_(LearningPath.user_id == user_id, LearningPath.team_id.is_(None))
        ))
        learning_paths = result.unique().scalars().all()

        result = []
        for lp in learning_paths:
            # Compute completion percentage manually to avoid lazy loading
            if lp.progress_records:
                total_completion = sum(p.completion_percentage for p in lp.progress_records)
                completion_percentage = total_completion / len(lp.progress_records)
            else:
                completion_percentage = 0.0

            result.append(LearningPathResponse(
                id=lp.id,
                user_id=lp.user_id,
                title=lp.title,
                description=lp.description,
                estimated_days=lp.estimated_days,
                completion_percentage=completion_percentage,
                created_at=lp.created_at,
                updated_at=lp.updated_at
            ))

        logger.debug(f"Retrieved {len(result)} personal learning paths for user {user_id}")
        return result

    except Exception as e:
        logger.error(f"Error getting learning paths for user {user_id}: {str(e)}")
        raise


async def get_by_team_id(db: AsyncSession, team_id: str) -> List[TeamLearningPathResponse]:
    """
    Get all learning paths for a team.

    Args:
        db: Database session
        team_id: ID of the team

    Returns:
        List of TeamLearningPathResponse objects
    """
    logger.debug(f"Getting team learning paths for team: {team_id}")

    try:
        result = await db.execute(select(LearningPath).options(
            selectinload(LearningPath.progress_records)
        ).options(
            selectinload(LearningPath.modules)
        ).filter(LearningPath.team_id == team_id))
        learning_paths = result.unique().scalars().all()

        result = []
        for lp in learning_paths:
            completion_percentage = lp.average_completion_percentage
            total_modules = lp.total_modules  # Using model property

            result.append(TeamLearningPathResponse(
                id=lp.id,
                title=lp.title,
                description=lp.description,
                user_id=lp.user_id,
                team_id=lp.team_id,
                estimated_days=lp.estimated_days,
                is_public=lp.is_public,
                total_modules=total_modules,
                completion_percentage=completion_percentage,
                created_at=lp.created_at,
                updated_at=lp.updated_at
            ))

        return result

    except Exception as e:
        logger.error(f"Error getting team learning paths for team {team_id}: {str(e)}")
        raise


async def user_has_access(db: AsyncSession, learning_path_id: int, user_id: str) -> bool:
    """
    Check if user has access to a learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user

    Returns:
        True if user has access, False otherwise
    """
    logger.debug(f"Checking access for user {user_id} to learning path {learning_path_id}")

    try:
        result = await db.execute(select(LearningPath).filter(LearningPath.id == learning_path_id))
        learning_path = result.scalar_one_or_none()

        if not learning_path:
            return False

        # User has access if they own the learning path
        if learning_path.user_id == user_id:
            return True

        # User has access if it's a team learning path and they're a team member
        if learning_path.team_id:
            member_result = await db.execute(select(TeamMember).filter(
                and_(
                    TeamMember.team_id == learning_path.team_id,
                    TeamMember.user_id == user_id
                )
            ))
            team_member = member_result.scalar_one_or_none()
            return team_member is not None

        return False

    except Exception as e:
        logger.error(f"Error checking access for user {user_id} to learning path {learning_path_id}: {str(e)}")
        return False


async def user_can_modify(db: AsyncSession, learning_path_id: int, user_id: str) -> bool:
    """
    Check if user can modify a learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user

    Returns:
        True if user can modify, False otherwise
    """
    logger.debug(f"Checking modify permissions for user {user_id} on learning path {learning_path_id}")

    try:
        result = await db.execute(select(LearningPath).filter(LearningPath.id == learning_path_id))
        learning_path = result.scalar_one_or_none()

        if not learning_path:
            return False

        # Owner can always modify
        if learning_path.user_id == user_id:
            return True

        # Team lead can modify team learning paths
        if learning_path.team_id:
            member_result = await db.execute(select(TeamMember).filter(
                and_(
                    TeamMember.team_id == learning_path.team_id,
                    TeamMember.user_id == user_id,
                    TeamMember.role == TeamMemberRole.TEAM_LEAD
                )
            ))
            team_member = member_result.scalar_one_or_none()
            return team_member is not None

        return False

    except Exception as e:
        logger.error(f"Error checking modify permissions for user {user_id} on learning path {learning_path_id}: {str(e)}")
        return False


async def user_can_delete(db: AsyncSession, learning_path_id: int, user_id: str) -> bool:
    """
    Check if user can delete a learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path
        user_id: ID of the user

    Returns:
        True if user can delete, False otherwise
    """
    logger.debug(f"Checking delete permissions for user {user_id} on learning path {learning_path_id}")

    try:
        # For now, same logic as modify - owner or team lead
        return await user_can_modify(db, learning_path_id, user_id)

    except Exception as e:
        logger.error(f"Error checking delete permissions for user {user_id} on learning path {learning_path_id}: {str(e)}")
        return False


async def delete_with_cascade(db: AsyncSession, learning_path_id: int) -> Dict[str, Any]:
    """
    Delete learning path and all associated data.

    Args:
        db: Database session
        learning_path_id: ID of the learning path to delete

    Returns:
        Dictionary with deletion statistics
    """
    logger.info(f"Deleting learning path {learning_path_id} with cascade")

    try:
        # Get learning path first
        result = await db.execute(select(LearningPath).options(joinedload(LearningPath.progress_records)).filter(LearningPath.id == learning_path_id))
        learning_path = result.unique().scalar_one_or_none()

        if not learning_path:
            raise ValueError("Learning path not found")

        # Count modules and quizzes to be deleted
        modules_result = await db.execute(select(Module).options(joinedload(Module.quiz)).filter(Module.learning_path_id == learning_path_id))
        modules = modules_result.scalars().all()
        deleted_modules_count = len(modules)

        # Count quizzes across all modules
        deleted_quizzes_count = 0
        for module in modules:
            if module.quiz:
                deleted_quizzes_count += 1

        # Get affected users (users with progress on this learning path)
        affected_users = list(set([p.user_id for p in learning_path.progress_records]))

        # Delete the learning path (cascade will handle modules, quizzes, progress)
        await db.delete(learning_path)
        await db.commit()

        return {
            "deleted_modules_count": deleted_modules_count,
            "deleted_quizzes_count": deleted_quizzes_count,
            "affected_users": affected_users
        }

    except Exception as e:
        logger.error(f"Error deleting learning path {learning_path_id}: {str(e)}")
        await db.rollback()
        raise

async def get_preferences(db: AsyncSession, learning_path_id: int) -> Optional[Preferences]:
    """
    Get preferences for a learning path.

    Args:
        db: Database session
        learning_path_id: ID of the learning path

    Returns:
        Dictionary with preferences or None if not found
    """
    logger.debug(f"Getting preferences for learning path {learning_path_id}")

    try:
        result = await db.execute(select(LearningPath).filter(LearningPath.id == learning_path_id))
        learning_path = result.scalar_one_or_none()

        if not learning_path or not learning_path.preferences_id:
            return None

        # Assuming preferences are stored in a separate table
        prefs_result = await db.execute(select(Preferences).filter(
            Preferences.id == learning_path.preferences_id
        ))
        preferences = prefs_result.scalar_one_or_none()

        if not preferences:
            return None

        return preferences

    except Exception as e:
        logger.error(f"Error getting preferences for learning path {learning_path_id}: {str(e)}")
        raise