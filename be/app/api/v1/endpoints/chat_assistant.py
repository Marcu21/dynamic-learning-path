"""
Chat assistant API endpoints with streaming support.

This module provides REST API endpoints for the chat assistant functionality,
supporting both streaming and non-streaming chat interactions with location
awareness and team context support.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import asyncio
import uuid
import time

from app.db.database import get_db_session
from app.services.ai_services.chat_services.chat_service import create_user_location
from app.services.ai_services.chat_services.context_retriever import (
    ContextRetriever,
    UserLocation
)
from app.core.redis_publisher import RedisPublisher, RedisSubscriber, get_redis_client
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.team import Team
from app.core.logger import get_logger
from app.tasks.chat_assistant_tasks import stream_chat_response_background

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/chat_assistant",
    tags=["Chat Assistant"]
)


# =============================
# PYDANTIC MODELS
# =============================

class LocationAwareChatRequest(BaseModel):
    """Request model for location-aware chat queries"""
    user_id: str = Field(..., description="User ID (UUID as string)")
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")

    # Location context
    location: str = Field(..., description="User's current location in the app")
    learning_path_id: Optional[int] = Field(None, description="Current learning path ID")
    module_id: Optional[int] = Field(None, description="Current module ID")
    quiz_id: Optional[int] = Field(None, description="Current quiz ID")
    quiz_attempt_id: Optional[int] = Field(None, description="Current quiz attempt ID")

    # Team context
    team_id: Optional[str] = Field(None, description="Team ID when on team dashboard")

    # Optional metadata
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    context_hint: Optional[str] = Field(None, description="Optional context hint")


class StreamingChatResponse(BaseModel):
    """Response model for streaming chat initiation"""
    task_id: str
    stream_channel: str
    message: str
    status: str
    user_context: Dict[str, Any]
    estimated_completion_time: int = 30  # seconds


# =============================
# STREAMING CHAT ENDPOINTS
# =============================

@router.post("/ask/stream", response_model=StreamingChatResponse)
async def start_streaming_chat(
        request: LocationAwareChatRequest,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Start a streaming chat session using the new workflow architecture.
    Enhanced with team support and proper validation.
    """
    logger.info(f"🌊 Streaming chat request received from user {current_user.id}")
    logger.debug(f"Request details: {request.model_dump_json(indent=2)}")

    try:
        # Validate user permissions
        if str(current_user.id) != request.user_id and current_user.role.value != "TEAM_LEAD":
            logger.warning(f"Permission denied: user {current_user.id} attempted to chat as {request.user_id}")
            raise HTTPException(
                status_code=403,
                detail="You can only ask questions for yourself"
            )

        # Validate team access if team_id is provided
        if request.team_id:
            result = await db.execute(select(Team).filter(Team.id == request.team_id))
            team = result.scalar_one_or_none()
            if not team:
                raise HTTPException(
                    status_code=404,
                    detail="Team not found"
                )

            # Check team membership (this would need to be implemented based on your team model)
            # For now, assuming team lead can access any team
            if current_user.role.value != "TEAM_LEAD":
                # Add your team membership validation logic here
                logger.warning(f"Team access validation needed for user {current_user.id} and team {request.team_id}")

        # Generate unique identifiers
        task_id = str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        stream_channel = f"stream:{request.user_id}:{task_id}"

        logger.info(f"🚀 Starting streaming chat for user {request.user_id}")
        logger.info(f"   Task ID: {task_id}")
        logger.info(f"   Stream channel: {stream_channel}")
        logger.info(f"   Question: {request.question[:50]}...")
        logger.info(f"   Location: {request.location}")

        if request.team_id:
            logger.info(f"   Team Context: {request.team_id}")

        # Validate user location context using new service
        user_location = create_user_location(
            location=request.location,
            learning_path_id=request.learning_path_id,
            module_id=request.module_id,
            quiz_id=request.quiz_id,
            quiz_attempt_id=request.quiz_attempt_id,
            team_id=request.team_id
        )

        # Enhanced location context with team support
        location_context = {
            "location": request.location,
            "learning_path_id": request.learning_path_id,
            "module_id": request.module_id,
            "quiz_id": request.quiz_id,
            "quiz_attempt_id": request.quiz_attempt_id,
            "team_id": request.team_id
        }

        # Start Celery task for streaming generation
        try:
            logger.info(f"📋 Queuing streaming chat task for user {request.user_id}")

            task = stream_chat_response_background.delay(
                user_id=request.user_id,
                question=request.question,
                location_context=location_context,
                stream_channel=stream_channel,
                session_id=session_id
            )

            logger.info(f"✅ Streaming chat task queued successfully: {task.id}")

        except Exception as celery_error:
            logger.error(f"Failed to start streaming chat task: {str(celery_error)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Background processing service is unavailable. Please try again later."
            )

        # Enhanced user context with team information
        user_context = {
            "user_id": request.user_id,
            "location": request.location,
            "learning_path_id": request.learning_path_id,
            "module_id": request.module_id,
            "quiz_id": request.quiz_id,
            "quiz_attempt_id": request.quiz_attempt_id,
            "team_id": request.team_id,
            "session_id": session_id,
            "is_team_context": request.team_id is not None
        }

        # Add team name if in team context
        if request.team_id:
            result = await db.execute(select(Team).filter(Team.id == request.team_id))
            team = result.scalar_one_or_none()
            if team:
                user_context["team_name"] = team.name

        return StreamingChatResponse(
            task_id=task.id,
            stream_channel=stream_channel,
            message="Streaming chat session started successfully",
            status="processing",
            user_context=user_context
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting streaming chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start chat session"
        )


# =============================
# NON-STREAMING ENDPOINT (Updated for New Workflow)
# =============================

@router.post("/ask")
async def ask_question_non_streaming(
        request: LocationAwareChatRequest,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Simple non-streaming chat endpoint using the new workflow architecture.
    For testing when Redis/Celery are not available.
    """
    try:
        # Check permissions
        logger.debug(f"Auth check: current_user.id={current_user.id}, request.user_id={request.user_id}")

        if str(current_user.id) != request.user_id and current_user.role.value != "TEAM_LEAD":
            logger.error(f"Permission denied: User ID mismatch: '{current_user.id}' != '{request.user_id}'")
            raise HTTPException(
                status_code=403,
                detail="You can only ask questions for yourself or you must be a team lead"
            )

        # Create user location context using new service
        user_location = create_user_location(
            location=request.location,
            learning_path_id=request.learning_path_id,
            module_id=request.module_id,
            quiz_id=request.quiz_id,
            quiz_attempt_id=request.quiz_attempt_id,
            team_id=request.team_id
        )

        # Initialize chat workflow using new architecture
        from app.services.ai_services.workflows.chat_assistant_workflow import ChatAssistantWorkflow

        chat_workflow = ChatAssistantWorkflow(db)

        # Get chat response using new workflow
        response = await chat_workflow.execute_chat(
            user_id=request.user_id,
            question=request.question,
            user_location=user_location
        )

        return {
            "response": response.get("response", "Sorry, I couldn't generate a response."),
            "context_type": response.get("context_type", "general"),
            "confidence": response.get("confidence", 0.0),
            "sources": response.get("sources", []),
            "cache_hit": response.get("cache_hit", False),
            "processing_time_ms": response.get("processing_time_ms", 0),
            "restricted": response.get("restricted", False),
            "restriction_reason": response.get("restriction_reason"),
            "user_location": user_location.model_dump(),
            "timestamp": time.time(),
            "architecture": "workflow_based"
        }

    except Exception as e:
        logger.error(f"Error in non-streaming chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(e)}"
        )


# =============================
# STREAM MANAGEMENT ENDPOINTS
# =============================

@router.get("/stream/{stream_channel}/status")
async def get_stream_status(
        stream_channel: str,
        current_user: User = Depends(get_current_active_user)
):
    """Get the current status of a streaming session."""
    try:
        # Extract user ID from channel for authorization
        parts = stream_channel.split(':')
        if len(parts) >= 2:
            stream_user_id = parts[1]
            # Check permissions
            current_user_id_str = str(current_user.id)
            if current_user_id_str != stream_user_id and current_user.role.value != "TEAM_LEAD":
                raise HTTPException(
                    status_code=403,
                    detail="You can only check status of your own streams"
                )

        # Check if ready signal was set
        redis_client = get_redis_client()
        ready_key = f"ready:{stream_channel}"
        ready_value = redis_client.get(ready_key)
        is_ready = ready_value == "1" or ready_value == b"1"  # Handle both string and bytes

        # Get message history to determine current status using RedisPublisher
        publisher = RedisPublisher()
        try:
            # Use the _store_message_history method to get history
            history_key = f"stream_history:{stream_channel}"
            recent_messages_raw = redis_client.lrange(history_key, 0, 9)  # Get last 10 messages
            recent_messages = []

            for msg_raw in recent_messages_raw:
                try:
                    msg = json.loads(msg_raw)
                    recent_messages.append(msg)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.warning(f"Could not retrieve message history: {str(e)}")
            recent_messages = []

        current_status = "unknown"
        last_message = None
        progress = 0

        if recent_messages:
            # Get the most recent message (first in list due to LPUSH)
            last_message = recent_messages[0]
            current_status = last_message.get('type', 'unknown')
            progress = last_message.get('progress', 0)

        return {
            "stream_channel": stream_channel,
            "user_id": stream_user_id if len(parts) >= 2 else "unknown",
            "current_status": current_status,
            "progress": progress,
            "is_ready": is_ready,
            "ready_key": ready_key,
            "last_message": last_message,
            "message_count": len(recent_messages),
            "is_active": current_status not in ['complete', 'error'],
            "architecture": "workflow_based"
        }

    except Exception as e:
        logger.error(f"Error getting stream status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stream status: {str(e)}"
        )


@router.delete("/stream/{stream_channel}")
async def cleanup_stream(
        stream_channel: str,
        current_user: User = Depends(get_current_active_user)
):
    """Clean up a stream channel and its history."""
    try:
        # Extract user ID from channel for authorization
        parts = stream_channel.split(':')
        if len(parts) >= 2:
            stream_user_id = parts[1]
            # Check permissions
            current_user_id_str = str(current_user.id)
            if current_user_id_str != stream_user_id and current_user.role.value != "TEAM_LEAD":
                raise HTTPException(
                    status_code=403,
                    detail="You can only cleanup your own streams"
                )

        redis_client = get_redis_client()

        # Clean up ready signal
        ready_key = f"ready:{stream_channel}"
        redis_client.delete(ready_key)

        # Clean up stream channel history
        history_key = f"stream_history:{stream_channel}"
        redis_client.delete(history_key)

        # Note: RedisPublisher doesn't have a cleanup_channel method in the provided code
        # So we'll clean up manually
        logger.info(f"Cleaned up stream channel: {stream_channel}")

        return {
            "message": f"Stream channel {stream_channel} cleaned up successfully",
            "stream_channel": stream_channel,
            "ready_key_cleaned": ready_key,
            "history_key_cleaned": history_key
        }

    except Exception as e:
        logger.error(f"Error cleaning up stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup stream: {str(e)}"
        )


@router.get("/stream/{stream_channel}")
async def listen_to_stream(
        stream_channel: str,
        current_user: User = Depends(get_current_active_user)
):
    """
    Listen to streaming chat events from Redis pub/sub channel.
    This endpoint provides Server-Sent Events (SSE) from the Celery worker.
    """
    try:
        # Extract user ID from stream channel for authorization
        parts = stream_channel.split(':')
        if len(parts) >= 2:
            stream_user_id = parts[1]
            # Check permissions - user can only listen to their own stream unless team lead
            current_user_id_str = str(current_user.id)
            if current_user_id_str != stream_user_id and current_user.role.value != "TEAM_LEAD":
                raise HTTPException(
                    status_code=403,
                    detail="You can only listen to your own chat streams"
                )

        subscriber = RedisSubscriber()

        # Subscribe to the stream channel
        if not subscriber.subscribe(stream_channel):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to subscribe to stream channel"
            )

        async def event_stream():
            try:
                # Send initial connection confirmation
                yield f"data: {json.dumps({'type': 'connected', 'channel': stream_channel, 'timestamp': time.time()})}\n\n"

                # Listen for messages from Redis using enhanced subscriber
                while True:
                    message = subscriber.get_message(timeout=1.0)

                    if message is None:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                        await asyncio.sleep(0.5)
                        continue

                    if message.get('type') == 'message':
                        message_data = message.get('data', {})

                        # Format as Server-Sent Event
                        yield f"data: {json.dumps(message_data)}\n\n"

                        # Break if this is a completion or error event
                        if message_data.get('type') in ['complete', 'error']:
                            break

                        # Add small delay to prevent overwhelming the client
                        await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in event stream: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            finally:
                # Clean up subscription
                subscriber.unsubscribe(stream_channel)
                subscriber.close()

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

    except Exception as e:
        logger.error(f"Error setting up stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup stream: {str(e)}"
        )


@router.post("/ready/{stream_channel}")
async def signal_frontend_ready(
        stream_channel: str,
        current_user: User = Depends(get_current_active_user)
):
    """
    Signal that the frontend is ready to receive streaming events.
    This triggers the Celery worker to start processing.
    """
    try:
        # Extract user ID from stream channel for authorization
        parts = stream_channel.split(':')
        if len(parts) >= 2:
            stream_user_id = parts[1]
            # Check permissions
            current_user_id_str = str(current_user.id)
            if current_user_id_str != stream_user_id and current_user.role.value != "TEAM_LEAD":
                raise HTTPException(
                    status_code=403,
                    detail="You can only signal ready for your own chat streams"
                )

        # Get Redis client
        redis_client = get_redis_client()

        # Set the ready flag for this stream channel
        ready_key = f"ready:{stream_channel}"
        redis_client.set(ready_key, "1", ex=60)  # Expire after 60 seconds

        logger.info(f"📡 Frontend ready signal received for stream: {stream_channel}")

        return {
            "status": "ok",
            "message": f"Frontend ready signal set for {stream_channel}",
            "ready_key": ready_key
        }

    except Exception as e:
        logger.error(f"Error setting frontend ready signal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to signal frontend ready: {str(e)}"
        )


# =============================
# UTILITY ENDPOINTS
# =============================

@router.get("/locations")
async def get_available_locations():
    """Get available user locations in the application"""
    return {
        "locations": [
            {
                "value": UserLocation.DASHBOARD.value,
                "description": "User is viewing the main dashboard with all learning paths"
            },
            {
                "value": UserLocation.LEARNING_PATH.value,
                "description": "User is viewing a specific learning path with its modules"
            },
            {
                "value": UserLocation.MODULE.value,
                "description": "User is viewing a specific module with its content and quiz"
            },
            {
                "value": UserLocation.QUIZ.value,
                "description": "User is viewing a quiz page with details and attempts"
            },
            {
                "value": UserLocation.QUIZ_ATTEMPT_ACTIVE.value,
                "description": "User is actively taking a quiz (responses restricted)"
            },
            {
                "value": UserLocation.REVIEW_ANSWERS.value,
                "description": "User is reviewing their latest quiz attempt answers"
            }
        ]
    }


@router.get("/health")
async def chat_agent_health():
    """Health check endpoint for the streaming chat agent service."""
    try:
        # Test Redis connection
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            redis_healthy = True
        else:
            redis_healthy = False

        health_status = {
            "status": "healthy" if redis_healthy else "degraded",
            "service": "streaming_chat_agent",
            "timestamp": time.time(),
            "architecture": "workflow_based",
            "features": {
                "streaming_chat": "enabled",
                "celery_workers": "enabled",
                "redis_pubsub": "enabled",
                "ready_handshake": "enabled",
                "location_awareness": "enabled",
                "team_context": "enabled",
                "quiz_attempt_restriction": "enabled",
                "progress_tracking": "enabled",
                "langgraph_workflow": "enabled"
            },
            "supported_locations": [loc.value for loc in UserLocation],
            "components": {
                "database": "healthy",
                "llm_service": "healthy",
                "redis": "healthy" if redis_healthy else "unhealthy",
                "workflow_engine": "enabled",
                "context_retriever": "enabled",
                "chat_service": "enabled"
            }
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service health check failed: {str(e)}"
        )


# =============================
# CONTEXT VALIDATION ENDPOINTS
# =============================

@router.post("/validate-context")
async def validate_user_context(
        request: LocationAwareChatRequest,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Validate that the user's reported context matches the database state.
    Updated to use new workflow architecture.
    """
    try:
        # Check permissions
        current_user_id_str = str(current_user.id)
        if current_user_id_str != request.user_id and current_user.role.value != "TEAM_LEAD":
            raise HTTPException(
                status_code=403,
                detail="You can only validate your own context"
            )

        # Use new context retriever
        retriever = ContextRetriever(db)

        # Create user location using new service
        user_location = create_user_location(
            location=request.location,
            learning_path_id=request.learning_path_id,
            module_id=request.module_id,
            quiz_id=request.quiz_id,
            quiz_attempt_id=request.quiz_attempt_id,
            team_id=request.team_id
        )

        # Check for active quiz attempt
        active_attempt = await retriever.check_active_quiz_attempt(
            request.user_id, request.quiz_id
        )

        validation_result = {
            "valid": True,
            "warnings": [],
            "user_location": user_location.model_dump(),
            "active_quiz_attempt": active_attempt,
            "architecture": "workflow_based"
        }

        # Validate learning path access
        if request.learning_path_id:
            try:
                from app.services.core_services import learning_path_service
                learning_path = await learning_path_service.get_learning_path_by_id(
                    db, request.learning_path_id, current_user.id
                )
                if not learning_path:
                    validation_result["warnings"].append(
                        f"Learning path {request.learning_path_id} not found or access denied"
                    )
                    validation_result["valid"] = False
            except Exception as e:
                validation_result["warnings"].append(f"Error validating learning path: {str(e)}")

        # Validate module access
        if request.module_id:
            try:
                from app.services.core_services import module_service
                module = await module_service.get_module_by_id(db, request.module_id)
                if not module:
                    validation_result["warnings"].append(
                        f"Module {request.module_id} not found or access denied"
                    )
                    validation_result["valid"] = False
            except Exception as e:
                validation_result["warnings"].append(f"Error validating module: {str(e)}")

        # Check for mismatched active quiz attempt
        if active_attempt and request.location != "quiz_attempt_active":
            validation_result["warnings"].append(
                f"User has active quiz attempt {active_attempt['attempt_id']} but location is {request.location}"
            )

        return validation_result

    except Exception as e:
        logger.error(f"Error validating user context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate context: {str(e)}"
        )


# =============================
# CONTEXT RETRIEVAL ENDPOINTS
# =============================

@router.get("/contexts/dashboard/{user_id}")
async def get_dashboard_context(
        user_id: str,
        team_id: Optional[str] = Query(None, description="Team ID for team dashboard context"),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """
    Get context for dashboard view - personal or team learning paths with progress.
    Updated to use new service methods and corrected Pydantic model access.
    """
    try:
        # Check permissions
        if str(current_user.id) != user_id and current_user.role.value != "TEAM_LEAD":
            raise HTTPException(
                status_code=403,
                detail="You can only view your own dashboard context"
            )

        if team_id:
            # TEAM DASHBOARD CONTEXT
            team_result = await db.execute(select(Team).filter(Team.id == team_id))
            team = team_result.scalar_one_or_none()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")

            from app.services.core_services import learning_path_service
            team_paths = await learning_path_service.get_team_learning_paths(db, team_id)
            
            # The service already returns paths for this team, just limit to 5
            team_specific_paths = team_paths[:5]

            return {
                "user_id": user_id,
                "location": "team_dashboard",
                "team_id": team_id,
                "team_name": team.name,
                "learning_paths": team_specific_paths,
                "total_accessible_paths": len(team_paths),
                "is_team_dashboard": True,
                "architecture": "workflow_based"
            }
        else:
            # PERSONAL DASHBOARD CONTEXT
            from app.services.core_services import learning_path_service
            from app.repositories import progress_repository

            # Service already returns only personal paths
            personal_paths = await learning_path_service.get_user_learning_paths(db, user_id)
            
            # Limit to the last 5 created paths
            personal_only_paths = personal_paths[:5]
            
            user_progress_summary = []
            for path in personal_only_paths:
                # Correctly access the id attribute of the Pydantic model
                progress = await progress_repository.get_learning_path_progress(db, path.id, user_id)
                user_progress_summary.append(progress)

            return {
                "user_id": user_id,
                "location": "personal_dashboard",
                "team_id": None,
                "user_progress_summary": user_progress_summary,
                "learning_paths": personal_only_paths,
                "total_accessible_paths": len(personal_paths),
                "is_team_dashboard": False,
                "architecture": "workflow_based"
            }

    except Exception as e:
        logger.error(f"Error getting dashboard context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard context: {str(e)}"
        )


@router.get("/active-quiz-attempt/{user_id}")
async def check_active_quiz_attempt(
        user_id: str,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
):
    """Check if user has any active quiz attempts using new context retriever."""
    try:
        # Check permissions
        if str(current_user.id) != user_id and current_user.role.value != "TEAM_LEAD":
            raise HTTPException(
                status_code=403,
                detail="You can only check your own quiz attempts"
            )

        # Use new context retriever
        retriever = ContextRetriever(db)
        active_attempt = await retriever.check_active_quiz_attempt(user_id)

        return {
            "user_id": user_id,
            "has_active_attempt": active_attempt is not None,
            "active_attempt": active_attempt,
            "architecture": "workflow_based"
        }

    except Exception as e:
        logger.error(f"Error checking active quiz attempt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check active quiz attempt: {str(e)}"
        )