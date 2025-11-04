"""
Path Generation API Endpoints
===================================

This module provides secure API endpoints for learning path generation
using Celery workers with JWT authentication and real-time streaming.

Key Features:
- JWT token authentication
- Async Celery task dispatch
- Real-time streaming via Redis channels
- Request validation and rate limiting
- Comprehensive error handling
- User permission validation
- Task status monitoring
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.schemas.path_generation_schemas.generation_endpoint_schema import PathGenerationRequest, PathGenerationResponse, UserTasksResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.core.dependencies import get_current_active_user, get_current_user_from_sse
from app.models.user import User
from app.services.core_services.task_tracking_service import get_user_path_tasks
from app.tasks.path_generation_tasks import (
    generate_learning_path_stream_task
)
from app.services.core_services import team_service
from app.core.logger import get_logger
from app.core.redis_publisher import RedisSubscriber, get_redis_client
import json

logger = get_logger(__name__)

# Create router for path generation endpoints
router = APIRouter(prefix="/api/v1/path-generation", tags=["Path Generation"])


# =============================================================================
# AUTHENTICATION AND PERMISSION HELPERS
# =============================================================================

async def validate_user_permissions(
        user: User,
        request_data: PathGenerationRequest,
        db: AsyncSession
) -> None:
    """
    Validate user permissions for path generation.

    Args:
        user: Authenticated user
        request_data: Generation request data
        db: Database session

    Raises:
        HTTPException: If user lacks required permissions
    """
    # Validate team permissions if team_id provided
    if request_data.team_id:
        if not await team_service.is_user_team_member(db, user.id, request_data.team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of the specified team"
            )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post(
    "/generate",
    response_model=PathGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate Learning Path",
    description="Start asynchronous learning path generation with real-time streaming updates"
)
async def generate_learning_path(
        request_data: PathGenerationRequest,
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
) -> PathGenerationResponse:
    """
    Generate a learning path asynchronously using Celery workers.

    This endpoint:
    1. Validates user permissions and request data
    2. Dispatches a Celery task for path generation
    3. Returns task ID and streaming channel for real-time updates
    4. Provides estimated completion time

    The actual generation happens asynchronously, and clients can:
    - Monitor progress via the returned stream_channel using WebSocket/SSE
    - Check task status using the task_id
    - Cancel the task if needed

    Returns:
        PathGenerationResponse: Task information and streaming details
    """
    try:
        logger.info(f"Path generation requested by user {current_user.id} for subject: {request_data.subject}")

        # Validate permissions and request data
        await validate_user_permissions(current_user, request_data, db)

        # Prepare task parameters
        task_kwargs = {
            "user_id": current_user.id,
            "subject": request_data.subject,
            "experience_level": request_data.experience_level.value,
            "learning_styles": [style.value for style in request_data.learning_styles],
            "preferred_platforms": request_data.preferred_platforms,
            "study_time_minutes": request_data.study_time_minutes,
            "goals": request_data.goals,
            "team_id": request_data.team_id,
        }

        # Dispatch Celery task
        task_result = generate_learning_path_stream_task.apply_async(
            kwargs=task_kwargs,
            queue="path_generation",
            routing_key="path_generation"
        )

        task_id = task_result.id

        # Generate stream channel with task ID
        stream_channel = f"path_generation_{current_user.id}_{task_id}"

        # Estimate completion time (business logic)
        estimated_modules = min(max(request_data.study_time_minutes // 30, 3), 12)
        estimated_duration_minutes = estimated_modules * 2  # ~2 minutes per module

        logger.info(f"Dispatched path generation task {task_id} for user {current_user.id}")
        logger.info(f"Stream channel: {stream_channel}")

        return PathGenerationResponse(
            task_id=task_id,
            stream_channel=stream_channel,
            status="STARTED",
            user_id=current_user.id,
            subject=request_data.subject,
            estimated_duration_minutes=estimated_duration_minutes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start path generation for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start path generation. Please try again."
        )


@router.get(
    "/stream/{stream_channel}",
    summary="Stream Generation Updates",
    description="Server-Sent Events endpoint for real-time path generation updates"
)
async def listen_stream_generation(
        stream_channel: str,
        token: Optional[str] = None,
        current_user: User = Depends(get_current_user_from_sse),
        db: AsyncSession = Depends(get_db_session)
) -> StreamingResponse:
    """
    Server-Sent Events endpoint for real-time path generation updates.

    This endpoint provides real-time streaming of path generation progress
    using Server-Sent Events (SSE). Clients can connect to receive:
    - Progress updates
    - Learning path information when ready
    - Individual module information as generated
    - Completion notifications
    - Error notifications

    Args:
        stream_channel: Redis channel for the generation task (format: path_generation_{user_id}_{task_id})
        current_user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse: SSE stream of generation updates
    """

    async def event_generator():
        """Generate SSE events from Redis stream with optimized connection handling."""
        redis_subscriber = None

        try:
            # Verify user has access to this stream channel
            if not stream_channel.startswith(f"path_generation_{current_user.id}_"):
                yield f"event: error\ndata: {json.dumps({'error': 'Access denied to stream channel'})}\n\n"
                return

            # Extract task ID from channel for additional validation
            try:
                channel_parts = stream_channel.split('_')
                if len(channel_parts) >= 3:
                    task_id = channel_parts[2]  # path_generation_{user_id}_{task_id}
                    logger.info(f"User {current_user.id} connecting to stream for task {task_id}")
                else:
                    raise ValueError("Invalid channel format")
            except (IndexError, ValueError):
                yield f"event: error\ndata: {json.dumps({'error': 'Invalid stream channel format'})}\n\n"
                return

            # Create Redis subscriber with better error handling
            redis_subscriber = RedisSubscriber()
            if not redis_subscriber.pubsub:
                yield f"event: error\ndata: {json.dumps({'error': 'Redis connection failed'})}\n\n"
                return

            # Subscribe to the Redis channel
            if not redis_subscriber.subscribe(stream_channel):
                yield f"event: error\ndata: {json.dumps({'error': 'Failed to connect to stream'})}\n\n"
                return

            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'message': 'Connected to generation stream', 'channel': stream_channel, 'task_id': task_id})}\n\n"

            # Listen for messages with shorter timeout to prevent blocking
            timeout_seconds = 1800  # 30 minutes timeout
            start_time = datetime.now()
            consecutive_timeouts = 0
            max_consecutive_timeouts = 10  # Disconnect after 10 consecutive timeouts

            while True:
                try:
                    # Check timeout
                    if (datetime.now() - start_time).total_seconds() > timeout_seconds:
                        yield f"event: timeout\ndata: {json.dumps({'message': 'Stream timeout'})}\n\n"
                        break

                    # Get message from Redis with shorter timeout to prevent blocking
                    message = redis_subscriber.get_message(timeout=0.5)

                    if message and message.get('type') == 'message':
                        try:
                            # Reset timeout counter on successful message
                            consecutive_timeouts = 0
                            
                            # Get the data from the message dict
                            event_data = message.get('data')

                            # Check if data is already a dict (parsed by RedisSubscriber)
                            if isinstance(event_data, dict):
                                # Data is already parsed, use it directly
                                parsed_event_data = event_data
                            elif isinstance(event_data, str):
                                # Data is still a string, parse it
                                try:
                                    parsed_event_data = json.loads(event_data)
                                except json.JSONDecodeError:
                                    logger.warning(f"Could not parse JSON from event data: {event_data}")
                                    continue
                            else:
                                # Unexpected data type, log and skip
                                logger.warning(f"Unexpected event data type: {type(event_data)}")
                                continue

                            # Extract event type for SSE
                            event_type = parsed_event_data.get('event_type', 'update')

                            # Send as SSE event - Convert dict back to JSON string for SSE data field
                            yield f"event: {event_type}\ndata: {json.dumps(parsed_event_data)}\n\n"

                            # Break on completion or error
                            if event_type in ['generation_complete', 'error_event']:
                                break

                        except Exception as parse_error:
                            logger.warning(f"Error processing message: {str(parse_error)}")
                            continue

                    elif message is None:
                        # No message received within timeout
                        consecutive_timeouts += 1
                        if consecutive_timeouts >= max_consecutive_timeouts:
                            logger.info(f"No messages for {max_consecutive_timeouts * 0.5} seconds, disconnecting")
                            break
                        continue

                    # Brief pause to prevent busy waiting and reduce CPU usage
                    await asyncio.sleep(0.05)  # Reduced from 0.1 to 0.05 for better responsiveness

                except Exception as e:
                    logger.error(f"Error in stream generator loop: {str(e)}")
                    yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                    break

        except Exception as e:
            logger.error(f"Stream connection error: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': f'Stream connection failed: {str(e)}'})}\n\n"

        finally:
            # Clean up Redis subscription
            if redis_subscriber:
                try:
                    redis_subscriber.unsubscribe(stream_channel)
                    redis_subscriber.close()  # Properly close the connection
                    yield f"event: disconnected\ndata: {json.dumps({'message': 'Stream disconnected'})}\n\n"
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up Redis subscription: {str(cleanup_error)}")
            else:
                yield f"event: disconnected\ndata: {json.dumps({'message': 'Stream disconnected'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
        }
    )


@router.get(
    "/my-tasks",
    response_model=UserTasksResponse,
    summary="Get User Tasks",
    description="Get all path generation tasks for the current user"
)
async def get_my_tasks(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
) -> UserTasksResponse:
    """
    Get all path generation tasks for the current user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        UserTasksResponse: User's task information
    """
    try:
        user_tasks = await get_user_path_tasks(current_user.id)

        # Categorize tasks
        running_tasks = [t for t in user_tasks if t.get("status") == "running"]
        completed_tasks = [t for t in user_tasks if t.get("status") == "completed"]
        failed_tasks = [t for t in user_tasks if t.get("status") == "failed"]

        return UserTasksResponse(
            active_tasks=user_tasks,
            total_count=len(user_tasks),
            running_count=len(running_tasks),
            completed_count=len(completed_tasks),
            failed_count=len(failed_tasks)
        )

    except Exception as e:
        logger.error(f"Failed to get tasks for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user tasks"
        )

# =============================================================================
# HEALTH AND MONITORING ENDPOINTS
# =============================================================================

@router.get(
    "/health",
    summary="Health Check",
    description="Check the health of path generation services"
)
async def health_check(
        current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Health check endpoint for path generation services.

    Returns:
        Dict[str, Any]: Health status information
    """
    try:
        # Check Redis connection
        redis_client = get_redis_client()
        redis_healthy = False
        if redis_client:
            try:
                redis_client.ping()
                redis_healthy = True
            except:
                pass

        # Check Celery worker availability
        from app.celery_app import celery_app
        inspector = celery_app.control.inspect()
        active_workers = inspector.active()
        worker_healthy = bool(active_workers)

        overall_healthy = redis_healthy and worker_healthy

        return {
            "healthy": overall_healthy,
            "services": {
                "redis": redis_healthy,
                "celery_workers": worker_healthy,
                "active_workers": len(active_workers) if active_workers else 0
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
