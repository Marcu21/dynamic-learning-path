"""
User Service

This module provides business logic for user operations.
All methods use repository pattern for data access abstraction.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.schemas.core_schemas.user_schema import UserResponse
from app.repositories import user_repository

logger = get_logger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[UserResponse]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: ID of the user to retrieve

    Returns:
        UserResponse object or None if not found
    """
    logger.info(f"Getting user {user_id}")

    try:
        user = await user_repository.get_by_id(db, user_id)

        if not user:
            logger.warning(f"User {user_id} not found")
            return None

        logger.info(f"Successfully retrieved user {user_id}: {user.username}")
        return user

    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise
