import asyncio
import time
import json
import traceback
from typing import Dict, Any
from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal  # Correctly import the async session
from app.core.redis_publisher import RedisPublisher, get_redis_client
from app.core.logger import get_logger

logger = get_logger(__name__)


def run_async_in_sync(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def wait_for_frontend_ready(redis, stream_channel, timeout=30):
    """
    Wait for frontend to be ready for streaming with handshake system.

    Args:
        redis: Redis client
        stream_channel: Stream channel name
        timeout: Timeout in seconds

    Returns:
        bool: True if frontend is ready, False if timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        value = redis.get(f"ready:{stream_channel}")
        logger.debug(f"[READY HANDSHAKE] Checking ready key: ready:{stream_channel} value={value}")
        if value == "1":
            logger.info(f"Frontend ready for streaming on channel: {stream_channel}")
            return True
        time.sleep(0.1)

    logger.warning(f"Frontend not ready for streaming on channel: {stream_channel} (timeout: {timeout}s)")
    return False


async def _stream_chat_response_async(
    task, user_id, question, location_context, stream_channel, session_id
):
    """
    Asynchronous helper to run the chat workflow with a proper async database session.
    """
    task_id = task.request.id
    publisher = RedisPublisher()

    def publish_stream_event(event_type: str, data: Any, progress: int = None):
        """Helper to publish streaming events"""
        event = {
            "type": event_type, "data": data, "task_id": task_id, "timestamp": time.time(),
            "user_id": user_id, "session_id": session_id,
            "location_context": {
                "location": location_context.get("location"),
                "team_id": location_context.get("team_id"),
                "is_team_context": location_context.get("team_id") is not None
            }
        }
        if progress is not None:
            event["progress"] = progress
        publisher.publish(stream_channel, json.dumps(event))

    async with AsyncSessionLocal() as db_session:
        from app.services.ai_services.workflows.chat_assistant_workflow import ChatAssistantWorkflow
        from app.services.ai_services.chat_services.chat_service import create_user_location

        user_location = create_user_location(
            location=location_context.get('location', 'dashboard'),
            learning_path_id=location_context.get('learning_path_id'),
            module_id=location_context.get('module_id'),
            quiz_id=location_context.get('quiz_id'),
            quiz_attempt_id=location_context.get('quiz_attempt_id'),
            team_id=location_context.get('team_id')
        )
        
        analysis_message = f"Analyzing question for {user_location.location.value.replace('_', ' ')}..."
        publish_stream_event("status", {"message": analysis_message, "step": "analyzing_context"}, 20)
        
        chat_workflow = ChatAssistantWorkflow(db_session)
        final_result = await stream_chat_generation_workflow(
            chat_workflow, user_id, question, user_location,
            publish_stream_event, task_id, location_context
        )
        return final_result


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def stream_chat_response_background(
        self,
        user_id: str,
        question: str,
        location_context: Dict[str, Any],
        stream_channel: str,
        session_id: str = None
) -> Dict[str, Any]:
    """
    Generate and stream chat response in background using Redis pub/sub.
    This is the synchronous wrapper for the main async logic.
    """
    task_id = self.request.id
    logger.info(f"🌊 Starting streaming chat task {task_id} for user {user_id}")

    publisher = RedisPublisher()
    
    def publish_stream_event(event_type: str, data: Any, progress: int = None):
        """Helper to publish events from the sync wrapper"""
        event = {"type": event_type, "data": data, "task_id": task_id, "timestamp": time.time()}
        if progress is not None:
            event["progress"] = progress
        publisher.publish(stream_channel, json.dumps(event))

    try:
        redis = get_redis_client()
        if not wait_for_frontend_ready(redis, stream_channel, timeout=30):
            error_msg = "Frontend did not connect in time. Please try again."
            logger.warning(f"Aborting task {task_id}: {error_msg}")
            publish_stream_event("error", {"message": error_msg})
            return {'success': False, 'error': 'Frontend not ready'}

        publish_stream_event("status", {"message": "Initializing chat analysis..."}, 5)
        self.update_state(state='PROGRESS', meta={'step': 'initializing', 'progress': 10})

        # Run the async helper
        final_result = run_async_in_sync(
            _stream_chat_response_async(
                self, user_id, question, location_context, stream_channel, session_id
            )
        )

        publish_stream_event("complete", {"message": "Chat response generated successfully", "final_result": final_result}, 100)
        self.update_state(state='SUCCESS', meta={'step': 'completed', 'progress': 100, 'result': final_result})
        
        logger.info(f"✅ Streaming chat task {task_id} completed successfully.")
        return {'success': True, 'task_id': task_id, 'final_result': final_result}

    except Exception as e:
        error_msg = f"Streaming chat task {task_id} failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        publish_stream_event("error", {"message": f"Chat generation failed: {str(e)}", "error": str(e)})
        self.update_state(state='FAILURE', meta={'step': 'error', 'error': str(e)})

        return {'success': False, 'task_id': task_id, 'error': str(e)}


async def stream_chat_generation_workflow(
        chat_workflow,
        user_id: str,
        question: str,
        user_location,
        publish_event_func,
        task_id: str,
        location_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle the streaming chat generation process using the new workflow.
    Enhanced with team support and word-by-word streaming.
    """
    context_start_time = time.time()
    
    try:
        async for chunk_data in chat_workflow.execute_chat_stream(
                user_id=user_id, question=question, user_location=user_location):
            try:
                chunk = json.loads(chunk_data)
                if chunk.get("type") == "content":
                    publish_event_func("content", {"content": chunk.get("content", "")})
                elif chunk.get("type") == "status":
                    publish_event_func("workflow_status", chunk)
                elif chunk.get("type") == "metadata":
                    # This is the final chunk with all metadata
                    streamed_content = "" # This would need to be accumulated if not sent in final metadata
                    
                    final_result = {
                        "response": chunk.get("response", ""), # Assuming response is now part of metadata
                        "context_type": chunk.get("context_type", "general"),
                        "confidence": chunk.get("confidence", 0.0),
                        "sources": chunk.get("sources", []),
                        "cache_hit": chunk.get("cache_hit", False),
                        "processing_time_ms": chunk.get("processing_time_ms", 0),
                        "restricted": chunk.get("restricted", False),
                        "restriction_reason": chunk.get("restriction_reason")
                    }
                    return final_result
            except json.JSONDecodeError:
                logger.warning(f"Could not parse chunk: {chunk_data}")
                continue
        # Fallback if the stream ends without a metadata event
        return {"response": "Stream finished without providing final metadata.", "context_type": "error"}
    except Exception as e:
        logger.error(f"Error in stream_chat_generation_workflow: {str(e)}")
        return {"response": "An error occurred during generation.", "error": str(e), "context_type": "error"}