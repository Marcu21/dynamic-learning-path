from fastapi import status, APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.schemas.core_schemas.user_schema import UserResponse
from app.services.auth_services.auth_service import AuthService
from app.core.dependencies import get_current_active_user
from app.models import User
from app.schemas.core_schemas.statistics_schema import UserStatisticsResponse
from app.services.core_services import statistics_service
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get user by ID"""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.get("/{user_id}/statistics", response_model=UserStatisticsResponse)
async def get_user_statistics(
        user_id: str = Path(..., description="User ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get comprehensive user statistics for the profile page.

    This endpoint provides all statistical data needed for the user profile page,
    including streak information, completion statistics, community comparisons,
    and detailed learning analytics.

    Args:
        user_id: ID of the user to get statistics for
        current_user: User making the request, must be authenticated
        db: Database session dependency

    Returns:
        UserStatisticsResponse: Comprehensive user statistics data

    Raises:
        HTTPException: 403 if access denied, 404 if user not found, 500 for server errors
    """
    import time
    start_time = time.time()
    
    logger.info(f"Getting user statistics for user {user_id} (requested by {current_user.id})")

    try:
        # Authorization: users can only access their own statistics or team leads can access any
        if current_user.id != user_id and current_user.role != "team_lead":
            logger.warning(f"Access denied: user {current_user.id} tried to access statistics for user {user_id}")
            raise HTTPException(status_code=403, detail="Access denied")

        # Get comprehensive user statistics
        statistics = await statistics_service.get_user_statistics(
            db=db,
            user_id=user_id
        )

        if not statistics:
            logger.warning(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        execution_time = time.time() - start_time
        logger.info(f"✅ Statistics retrieved for user {user_id} in {execution_time:.2f}s")
        
        return statistics

    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ Error getting user statistics for user {user_id} after {execution_time:.2f}s: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
