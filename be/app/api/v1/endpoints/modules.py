"""
Modules API Endpoints

This module provides FastAPI endpoints for managing modules.
"""

from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.core.logger import get_logger
from app.schemas.core_schemas.module_schema import (
    ModuleResponse,
    ModulesListResponse,
    ModuleDeletionResponse, ModuleCompletionResponse, ModuleCompletionRequest
)
from app.services.core_services import module_service
from app.services.core_services import learning_path_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/modules",
    tags=["Modules"]
)


# =============================
# GET MODULE ENDPOINTS
# =============================

@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module_endpoint(
        module_id: int = Path(..., description="Module ID", ge=1),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get specific module details
    """
    try:
        # Get module
        module = await module_service.get_module_by_id(
            db=db,
            module_id=module_id
        )

        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        # Verify user has access to the learning path containing this module
        if not await learning_path_service.user_has_access_to_learning_path(
                db=db,
                learning_path_id=module.learning_path_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied to module")

        return module

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting module {module_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/learning-path/{learning_path_id}", response_model=ModulesListResponse)
async def get_modules_endpoint(
        learning_path_id: int = Path(..., description="Learning path ID", ge=1),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get all modules for a specific learning path
    """
    try:
        # Verify user has access to the learning path
        if not await learning_path_service.user_has_access_to_learning_path(
                db=db,
                learning_path_id=learning_path_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied to learning path")

        # Get modules
        modules = await module_service.get_modules_by_learning_path_id(
            db=db,
            learning_path_id=learning_path_id
        )

        return ModulesListResponse(root=modules)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting modules for learning path {learning_path_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# DELETE MODULE ENDPOINT
# =============================

@router.delete("/{module_id}", response_model=ModuleDeletionResponse)
async def delete_module_endpoint(
        module_id: int = Path(..., description="Module ID", ge=1),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a specific module by ID
    """
    try:
        # Get module to verify it exists and get learning path info
        module = await module_service.get_module_by_id(
            db=db,
            module_id=module_id
        )

        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        # Verify user can delete this module (owner or team lead)
        if not await learning_path_service.user_can_modify_learning_path(
                db=db,
                learning_path_id=module.learning_path_id,
                user_id=current_user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete module and get deletion stats
        deletion_result = await module_service.delete_module(
            db=db,
            module_id=module_id
        )

        return ModuleDeletionResponse(
            success=True,
            message="Module deleted successfully",
            deleted_module_id=module_id,
            affected_learning_path_id=module.learning_path_id,
            deleted_quizzes_count=deletion_result["deleted_quizzes_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting module {module_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================
# MODULE PROGRESS ENDPOINTS
# =============================

@router.put("/{module_id}/complete", response_model=ModuleCompletionResponse)
async def mark_module_complete(
        request: ModuleCompletionRequest,
        module_id: int = Path(..., description="Module ID", gt=0),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Mark a module as completed by a user
    """
    try:
        # Authorization: users can only complete modules for themselves or team leads for others
        if current_user.id != request.user_id and current_user.role != "team_lead":
            raise HTTPException(status_code=403, detail="Access denied")

        # Verify module exists
        module = await module_service.get_module_by_id(
            db=db,
            module_id=module_id
        )

        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        # Verify user has access to the learning path
        if not await learning_path_service.user_has_access_to_learning_path(
                db=db,
                learning_path_id=module.learning_path_id,
                user_id=request.user_id
        ):
            raise HTTPException(status_code=403, detail="Access denied to learning path")

        # Mark module as complete
        completion_result = await module_service.mark_module_complete(
            db=db,
            module_id=module_id,
            user_id=request.user_id,
            completion_notes=request.completion_notes,
            time_spent_minutes=request.time_spent_minutes
        )

        return ModuleCompletionResponse(
            success=True,
            message="Module marked as completed successfully",
            module_id=module_id,
            user_id=request.user_id,
            completed_at=completion_result["completed_at"],
            skill_points_awarded=completion_result["skill_points_awarded"],
            learning_path_progress_updated=completion_result["learning_path_progress_updated"],
            new_completion_percentage=completion_result["new_completion_percentage"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking module {module_id} as complete: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
