from fastapi import WebSocket, WebSocketDisconnect, Query
from fastapi.routing import APIRouter
from typing import Dict, Set, Optional
import json
import redis
import asyncio
from sqlalchemy import select
from app.core.auth import verify_token
from app.models.user import User
from app.core.logger import get_logger
from app.core.config import settings
from starlette.websockets import WebSocketState

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/notifications"
)

# Store active WebSocket connections by user ID (FastAPI process only)
active_connections: Dict[str, Set[WebSocket]] = {}

# Redis client for sharing connection info between processes
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=30,
    retry_on_timeout=True,
    health_check_interval=30
)

class NotificationWebSocketManager:
    """WebSocket manager for notifications with Redis-based cross-process communication"""
    
    @staticmethod
    async def connect(websocket: WebSocket, user_id: str):
        """Connect a new WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in active_connections:
            active_connections[user_id] = set()
        
        active_connections[user_id].add(websocket)
        
        # Store connection info in Redis for Celery workers to see
        redis_client.sadd(f"websocket_users", user_id)
        redis_client.expire(f"websocket_users", 3600)  # Expire after 1 hour
        
        logger.info(f"WebSocket connected for user {user_id}. Active connections: {len(active_connections[user_id])}")
    
    @staticmethod
    async def disconnect(websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket for a user"""
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]
                # Remove from Redis when no connections left
                redis_client.srem(f"websocket_users", user_id)
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    @staticmethod
    async def send_notification_to_user(user_id: str, notification_data: dict):
        """Send notification to all WebSocket connections for a user"""
        # Check if user has active connections in THIS process
        if user_id not in active_connections:
            # Check Redis to see if user has connections in ANY process
            has_connections = redis_client.sismember(f"websocket_users", user_id)
            if not has_connections:
                all_connected_users = redis_client.smembers(f"websocket_users")
                logger.info(f"No active WebSocket connections for user {user_id}. Available connections: {list(all_connected_users)}")
                return
            else:
                # User has connections in another process, publish to Redis channel
                # Extract the inner notification data if it's already wrapped
                redis_data = notification_data
                if notification_data.get("type") == "notification" and "notification" in notification_data:
                    # Send the already-formatted structure to Redis
                    redis_data = notification_data
                else:
                    # Wrap the data for Redis if it's not already wrapped
                    redis_data = {
                        "type": "notification",
                        "notification": notification_data
                    }

                redis_client.publish(f"websocket_notify_{user_id}", json.dumps(redis_data))
                logger.info(f"Published WebSocket notification to Redis channel for user {user_id}")
                return

        # Check if this is a task completion message
        if notification_data.get("type") == "task_completed":
            message = {
                "type": "task_completed",
                "task_id": notification_data.get("task_id"),
                "result": notification_data.get("result")
            }
        elif notification_data.get("type") == "module_inserted":
            # Handle module_inserted messages properly - send as-is
            message = notification_data
        elif notification_data.get("type") == "notification":
            # Notification data is already in the correct format
            message = notification_data
        else:
            # Legacy format - wrap the notification data
            message = {
                "type": "notification",
                "notification": notification_data
            }
        
        # Send to all connections for this user
        disconnected_sockets = set()
        for websocket in active_connections[user_id].copy():
            try:
                # Check WebSocket state before attempting to send
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.info(f"WebSocket not connected for user {user_id}, marking for cleanup")
                    disconnected_sockets.add(websocket)
                    continue

                await websocket.send_text(json.dumps(message))
                logger.info(f"✅ Successfully sent message to user {user_id} via WebSocket: {message.get('type', 'unknown type')}")
            except Exception as e:
                # Check if the error is due to WebSocket being closed
                if "close message has been sent" in str(e) or websocket.client_state == WebSocketState.DISCONNECTED:
                    logger.info(f"WebSocket closed for user {user_id}, marking for cleanup: {e}")
                else:
                    logger.warning(f"Failed to send WebSocket message to user {user_id}: {e}")
                disconnected_sockets.add(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected_sockets:
            active_connections[user_id].discard(ws)

        # If no connections left for this user, clean up Redis entry
        if user_id in active_connections and not active_connections[user_id]:
            del active_connections[user_id]
            redis_client.srem(f"websocket_users", user_id)

    @staticmethod
    async def send_notification_to_team(team_id: str, user_ids: list, notification_data: dict):
        """Send notification to all users in a team"""
        for user_id in user_ids:
            await NotificationWebSocketManager.send_notification_to_user(user_id, notification_data)


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time notifications"""
    
    user_id = None
    user = None
    
    try:
        if token:
            # Validate the JWT token
            try:
                token_data = verify_token(token)
                user_id = token_data.user_id
                logger.info(f"Token validation successful for user_id: {user_id}")
            except Exception as e:
                logger.error(f"Token validation failed: {e}")
                await websocket.accept()
                await websocket.close(code=1008, reason="Invalid or expired token")
                return
            
            # Get user from database to verify they exist
            from app.db.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).filter(User.id == user_id))
                user = result.scalar_one_or_none()
                if not user:
                    logger.error(f"User with ID {user_id} not found in database")
                    # Accept connection first, then close with error
                    await websocket.accept()
                    await websocket.close(code=1008, reason="User not found")
                    return
                    
                logger.info(f"WebSocket authentication successful for user: {user.email} (ID: {user_id})")
        else:
            # No token provided - reject connection
            logger.error("WebSocket connection without authentication token - rejecting")
            await websocket.accept()
            await websocket.close(code=1008, reason="Authentication required")
            return
        
    except Exception as e:
        logger.error(f"WebSocket authentication failed with exception: {e}")
        logger.error(f"Exception type: {type(e)}")
        # Accept connection first, then close with error
        try:
            await websocket.accept()
            await websocket.close(code=1008, reason="Authentication failed")
        except Exception as close_error:
            logger.error(f"Error closing WebSocket: {close_error}")
        return
    
    await NotificationWebSocketManager.connect(websocket, user_id)
    
    # Create Redis pubsub for this user
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"websocket_notify_{user_id}")
    
    async def redis_listener():
        """Listen for Redis messages and forward to WebSocket"""
        try:
            while True:
                # Check if WebSocket is still connected before processing messages
                if websocket.client_state == WebSocketState.DISCONNECTED:
                    logger.info(f"WebSocket disconnected for user {user_id}, stopping Redis listener")
                    break

                message = pubsub.get_message(timeout=5.0)  # Increased timeout to 5 seconds
                if message is None:
                    await asyncio.sleep(0.5)  # Increased sleep to reduce CPU usage
                    continue
                    
                if message['type'] == 'message':
                    try:
                        # Double-check WebSocket state before sending
                        if websocket.client_state != WebSocketState.CONNECTED:
                            logger.info(f"WebSocket not connected for user {user_id}, skipping message")
                            break

                        notification_data = json.loads(message['data'])

                        # Check if this is a task completion message
                        if notification_data.get("type") == "task_completed":
                            ws_message = {
                                "type": "task_completed",
                                "task_id": notification_data.get("task_id"),
                                "result": notification_data.get("result")
                            }
                        elif notification_data.get("type") == "module_inserted":
                            # Handle module_inserted messages properly - send as-is
                            ws_message = notification_data
                        elif notification_data.get("type") == "notification":
                            # Notification data is already in the correct format
                            ws_message = notification_data
                        else:
                            # Legacy format - wrap the notification data
                            ws_message = {
                                "type": "notification",
                                "notification": notification_data
                            }
                        
                        await websocket.send_text(json.dumps(ws_message))
                        logger.info(f"✅ Forwarded Redis message to WebSocket for user {user_id}: {ws_message.get('type', 'unknown type')}")
                    except Exception as e:
                        # Check if the error is due to WebSocket being closed
                        if "close message has been sent" in str(e) or websocket.client_state == WebSocketState.DISCONNECTED:
                            logger.info(f"WebSocket closed for user {user_id}, stopping Redis listener: {e}")
                            break
                        logger.error(f"Error processing Redis message for user {user_id}: {e}")
        except asyncio.CancelledError:
            logger.info(f"Redis listener cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Redis listener error for user {user_id}: {e}")
        finally:
            # Ensure pubsub is properly closed
            try:
                pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub for user {user_id}: {e}")

    # Start Redis listener in background
    redis_task = asyncio.create_task(redis_listener())
    
    try:
        while True:
            # Keep connection alive with timeout to allow for periodic cleanup
            try:
                # Wait for incoming messages with timeout for periodic health checks
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                # Handle ping/pong for connection health
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                        logger.debug(f"Sent pong to user {user_id}")
                except json.JSONDecodeError:
                    logger.debug(f"Received non-JSON message from user {user_id}: {data}")
                    pass
                    
            except asyncio.TimeoutError:
                # No message received in 60 seconds - check connection health
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.info(f"WebSocket connection lost for user {user_id} during timeout check")
                    break
                # Connection is still alive, continue listening
                continue
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for user {user_id}")
        redis_task.cancel()
        pubsub.close()
        await NotificationWebSocketManager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        redis_task.cancel()
        pubsub.close()
        await NotificationWebSocketManager.disconnect(websocket, user_id)
    finally:
        # Ensure cleanup
        if not redis_task.done():
            redis_task.cancel()
        try:
            pubsub.close()
        except:
            pass


# Utility function to send notifications via WebSocket
async def send_websocket_notification(user_id: str, notification_dict: dict):
    """Helper function to send notifications via WebSocket"""
    await NotificationWebSocketManager.send_notification_to_user(user_id, notification_dict)


async def send_websocket_team_notification(team_id: str, user_ids: list, notification_dict: dict):
    """Helper function to send team notifications via WebSocket"""
    await NotificationWebSocketManager.send_notification_to_team(team_id, user_ids, notification_dict)


# Debug function to check active connections
def get_active_connections_info():
    """Get information about active WebSocket connections for debugging"""
    info = {}
    for user_id, connections in active_connections.items():
        info[user_id] = len(connections)
    return info
