"""
Module Insertion API Endpoint
============================

This module contains the FastAPI endpoint for module insertion operations.
Provides both synchronous and asynchronous module insertion capabilities
with comprehensive validation, error handling, and monitoring.

Key Features:
- Synchronous and asynchronous module insertion
- Input validation and authorization
- Task status monitoring and cancellation
- Comprehensive error handling
- OpenAPI documentation
- Rate limiting and security
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.core.logger import get_logger
from app.services.core_services import learning_path_service
from app.repositories import learning_path_repository
from app.schemas.path_generation_schemas.module_insertion_schema import ModuleInsertionAsyncRequest, AsyncInsertionResponse

from app.tasks.module_insertion_tasks import insert_module_task


logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/module-insertion",
    tags=["Module Insertion"]
)

@router.post(
    "/insert",
    response_model=AsyncInsertionResponse,
    summary="Insert module asynchronously",
    description="Insert a new module into a learning path asynchronously. Use for complex insertions."
)
async def insert_module_async_endpoint(
        request: ModuleInsertionAsyncRequest = Body(...),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
) -> AsyncInsertionResponse:
    """
    Insert a module into a learning path asynchronously.

    This endpoint starts a background task for module insertion and returns immediately
    with a task ID. Use this for complex insertions that may take longer to complete.
    """
    try:
        logger.info(
            f"Asynchronous module insertion request - "
            f"User: {current_user.id}, Learning Path: {request.learning_path_id}, "
            f"Position: {request.insert_position}, Platform: {request.platform_name}"
        )

        # Validate learning path access
        learning_path = await learning_path_repository.get_by_id(db, request.learning_path_id)
        if not learning_path:
            raise HTTPException(
                status_code=404,
                detail=f"Learning path {request.learning_path_id} not found"
            )

        # Check user permissions
        if not await learning_path_service.validate_learning_path_access(db, learning_path.id, current_user.id):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to modify this learning path"
            )

        # Start asynchronous task
        task_result = insert_module_task.delay(
            user_query=request.user_query,
            learning_path_id=request.learning_path_id,
            insert_position=request.insert_position,
            platform_name=request.platform_name,
            user_id=str(current_user.id)
        )

        # Prepare response
        response = AsyncInsertionResponse(
            task_id=task_result.id,
            status="PENDING",
            message="Module insertion task started successfully",
            estimated_completion_time="5-10 minutes"
        )

        logger.info(f"Asynchronous module insertion task {task_result.id} started for user {current_user.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asynchronous module insertion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start module insertion task: {str(e)}"
        )
