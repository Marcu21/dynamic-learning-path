"""
Preferences Repository
======================

This module contains database operations for preferences entities.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from typing import Optional
from app.models.preferences import Preferences
from app.core.logger import get_logger
from app.schemas.core_schemas.preference_schema import PreferencesCreate

logger = get_logger(__name__)


# =============================================================================
# CORE PREFERENCES REPOSITORY OPERATIONS
# =============================================================================

def create_preferences(db, preferences_data: PreferencesCreate) -> Preferences:
    """
    Create a new preferences record in the database (works with both sync and async sessions).

    Args:
        db: Database session (sync or async)
        preferences_data: Dictionary containing preferences data

    Returns:
        Preferences: The created preferences entity

    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        logger.debug(f"Creating preferences for subject: {getattr(preferences_data, 'subject')}")

        # Detect if this is an async session
        is_async = hasattr(db, '__aenter__') or str(type(db)).find('AsyncSession') != -1

        preferences = Preferences(
            subject=getattr(preferences_data, "subject"),
            experience_level=getattr(preferences_data, "experience_level"),
            learning_style=getattr(preferences_data, "learning_styles"),
            preferred_platforms=getattr(preferences_data, "preferred_platforms"),
            study_time=getattr(preferences_data, "study_time_minutes"),
            desired_goals=getattr(preferences_data, "goals")
        )

        db.add(preferences)
        
        if is_async:
            raise ValueError("Async sessions not supported - use sync session from Celery")
        else:
            db.commit()
            db.refresh(preferences)
            
        logger.debug(f"Created preferences {preferences.id} for subject: {preferences.subject}")
        return preferences

    except SQLAlchemyError as e:
        logger.error(f"Failed to create preferences: {str(e)}")
        if is_async:
            raise ValueError("Async sessions not supported - use sync session from Celery")
        else:
            db.rollback()
        raise


async def get_by_id(db: AsyncSession, preferences_id: int) -> Optional[Preferences]:
    """
    Retrieve preferences by their ID.

    Args:
        db: Database session
        preferences_id: ID of the preferences

    Returns:
        Optional[Preferences]: The preferences entity or None if not found
    """
    try:
        stmt = select(Preferences).where(Preferences.id == preferences_id)
        result = await db.execute(stmt)
        preferences = result.scalars().first()

        if preferences:
            logger.debug(f"Retrieved preferences {preferences_id}")
        else:
            logger.debug(f"Preferences {preferences_id} not found")

        return preferences

    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve preferences {preferences_id}: {str(e)}")
        raise
