"""
Learning Paths API Endpoints

This module provides FastAPI endpoints for managing learning paths.
"""

from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.core.dependencies import get_current_active_user
from app.core.logger import get_logger
from app.models.user import User
from app.schemas.core_schemas.learning_path_schema import (
    LearningPathDetailResponse,
    UserLearningPathsResponse,
    TeamLearningPathsResponse,
    LearningPathDeletionResponse, LearningPathProgressResponse,
)
from app.schemas.core_schemas.preference_schema import PreferencesResponse
from app.services.core_services import learning_path_service
from app.services.core_services import module_service
from app.services.core_services import team_service


logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/learning-paths",
    tags=["Learning Paths"]
)


# =============================
# LEARNING PATH RETRIEVAL ENDPOINTS
# =============================

@router.get("/{learning_path_id}", response_model=LearningPathDetailResponse)
async def get_learning_path_details(
    learning_path_id: int = Path(..., description="Learning path ID", ge=1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get learning path with modules
    """
    try:
        # Get learning path
        learning_path = await learning_path_service.get_learning_path_by_id(
            db=db,
            learning_path_id=learning_path_id,
            user_id=current_user.id
        )

        if not learning_path:
            raise HTTPException(status_code=404, detail="Learning path not found")

        # Get modules for the learning path
        modules = await module_service.get_modules_by_learning_path_id(
            db=db,
            learning_path_id=learning_path_id
        )

        return LearningPathDetailResponse(
            learning_path=learning_path,
            modules=modules
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning path details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}", response_model=UserLearningPathsResponse)
async def get_user_learning_paths(
    user_id: str = Path(..., description="User ID to get learning paths for"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all personal learning paths for a user (excludes team paths)
    """
    try:
        # Authorization: users can only access their own paths or team leads can access any
        if current_user.id != user_id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Access denied")

        # Use get_user_learning_paths which already filters out team paths
        learning_paths = await learning_path_service.get_user_learning_paths(
            db=db,
            user_id=user_id
        )

        return UserLearningPathsResponse(root=learning_paths)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user learning paths: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/team/{team_id}", response_model=TeamLearningPathsResponse)
async def get_team_learning_paths(
    team_id: str = Path(..., description="Team ID to get learning paths for"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all learning paths for a team with current user's progress
    """
    try:
        # Verify user has access to team
        if not await team_service.user_has_team_access(
            db=db,
            team_id=team_id,
            user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied to team")

        # Get team learning paths with current user's progress
        team_learning_paths = await learning_path_service.get_team_learning_paths_with_user_progress(
            db=db,
            team_id=team_id,
            user_id=current_user.id
        )

        return TeamLearningPathsResponse(root=team_learning_paths)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team learning paths: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# LEARNING PATH DELETION
# =============================

@router.delete("/{learning_path_id}", response_model=LearningPathDeletionResponse)
async def delete_learning_path(
    learning_path_id: int = Path(..., description="Learning path ID", ge=1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a learning path and all its associated data
    """
    try:
        # Verify ownership or team lead access
        learning_path = await learning_path_service.get_learning_path_by_id(
            db=db,
            learning_path_id=learning_path_id,
            user_id=current_user.id
        )

        if not learning_path:
            raise HTTPException(status_code=404, detail="Learning path not found")

        if not await learning_path_service.user_can_delete_learning_path(
            db=db,
            learning_path_id=learning_path_id,
            user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete learning path and get deletion stats
        deletion_result = await learning_path_service.delete_learning_path(
            db=db,
            learning_path_id=learning_path_id
        )

        return LearningPathDeletionResponse(
            success=True,
            message="Learning path and all associated data deleted successfully",
            deleted_learning_path_id=learning_path_id,
            deleted_modules_count=deletion_result["deleted_modules_count"],
            deleted_quizzes_count=deletion_result["deleted_quizzes_count"],
            affected_users=deletion_result["affected_users"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting learning path: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# PATH PROGRESS
# =============================

@router.get("/{learning_path_id}/users/{user_id}", response_model=LearningPathProgressResponse)
async def get_learning_path_progress(
        learning_path_id: int = Path(..., description="Learning path ID", gt=0),
        user_id: str = Path(..., description="User ID"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get learning path progress for a specific user
    """
    try:
        # Authorization: users can only access their own progress or team leads can access any
        if current_user.id != user_id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Access denied")

        # Verify learning path exists and user has access
        learning_path = await learning_path_service.get_learning_path_by_id(
            db=db,
            learning_path_id=learning_path_id,
            user_id=current_user.id
        )

        if not learning_path:
            raise HTTPException(status_code=404, detail="Learning path not found")

        # Get detailed progress information
        progress_data = await learning_path_service.get_learning_path_progress(
            db=db,
            learning_path_id=learning_path_id,
            user_id=user_id
        )

        return progress_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning path progress for path {learning_path_id}, user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{learning_path_id}/preferences", response_model=PreferencesResponse)
async def get_learning_path_preferences(
    learning_path_id: int = Path(..., description="Learning path ID", ge=1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get preferences for a specific learning path
    """
    try:
        # Get preferences associated with the learning path
        preferences = await learning_path_service.get_learning_path_preferences(
            db=db,
            learning_path_id=learning_path_id
        )

        # Handle case where no preferences are found
        if preferences is None:
            raise HTTPException(
                status_code=404, 
                detail=f"No preferences found for learning path {learning_path_id}"
            )

        return PreferencesResponse.model_validate(preferences)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preferences for learning path {learning_path_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
