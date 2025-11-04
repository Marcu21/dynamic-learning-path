from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import Optional
from app.core.auth import verify_token
from app.db.database import get_db_session
from app.models.user import User
from app.models.enums import UserRole
from app.models.team_member import TeamMember

security = HTTPBearer()



async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get the current authenticated user with eagerly loaded relationships"""
    token = credentials.credentials
    token_data = verify_token(token)

    # This is the efficient, eagerly-loaded query
    query = (
        select(User)
        .options(
            selectinload(User.team_memberships).selectinload(TeamMember.team),
            selectinload(User.notifications)
        )
        .filter(User.id == token_data.user_id)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current user (is_active check removed since it tracks login status)"""
    return current_user


def require_role(required_role: UserRole):
    """Dependency factory to require specific user role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {str(required_role)} role"
            )
        return current_user
    return role_checker


async def get_current_user_from_sse(
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Get the current authenticated user from SSE token query parameter"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required for SSE authentication",
        )

    try:
        # Verify the token
        token_data = verify_token(token)

        # Get user from database
        result = await db.execute(select(User).filter(User.id == token_data.user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user

    except Exception as e:
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"SSE authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
