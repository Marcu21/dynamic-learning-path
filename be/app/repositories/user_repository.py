"""
User Repository

This module provides data access methods for user operations.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.core_schemas.user_schema import UserResponse, UserRoleEnum

logger = get_logger(__name__)


async def get_by_id(db: AsyncSession, user_id: str) -> Optional[UserResponse]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        UserResponse object or None if not found
    """
    logger.debug(f"Getting user by ID: {user_id}")

    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.debug(f"User {user_id} not found")
            return None

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=UserRoleEnum.TEAM_LEAD if user.role == UserRole.TEAM_LEAD else UserRoleEnum.USER,
            is_active=user.is_active,
            skill_points=user.skill_points,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )

    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise
