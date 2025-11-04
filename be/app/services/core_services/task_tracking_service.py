import json
from datetime import datetime
from typing import List, Dict, Any
from app.core.logger import get_logger
from app.core.redis_publisher import get_redis_client
from app.core.config import settings

logger = get_logger(__name__)

async def register_quiz_task(learning_path_id: int, task_id: str, task_type: str = "quiz_generation") -> None:
    """
    Register a quiz generation task for a learning path.

    Args:
        learning_path_id: ID of the learning path
        task_id: Celery task ID
        task_type: Type of task (quiz_generation, module_quiz, etc.)
    """
    try:
        redis_client = get_redis_client()
        key = f"{settings.redis_key_prefix}{learning_path_id}"

        # Get existing tasks
        existing_tasks = await get_learning_path_tasks(learning_path_id)

        # Add new task
        task_info = {
            "task_id": task_id,
            "task_type": task_type,
            "registered_at": str(int(__import__('time').time()))
        }
        existing_tasks.append(task_info)

        # Store back to Redis
        redis_client.setex(key, settings.redis_expiry, json.dumps(existing_tasks))
        logger.info(f"Registered {task_type} task {task_id} for learning path {learning_path_id}")

    except Exception as e:
        logger.error(f"Error registering task {task_id} for learning path {learning_path_id}: {str(e)}")

async def unregister_quiz_task(learning_path_id: int, task_id: str) -> None:
    """
    Unregister a completed quiz generation task.

    Args:
        learning_path_id: ID of the learning path
        task_id: Celery task ID to remove
    """
    try:
        redis_client = get_redis_client()
        key = f"{settings.redis_key_prefix}{learning_path_id}"

        # Get existing tasks
        existing_tasks = await get_learning_path_tasks(learning_path_id)

        # Remove the task
        updated_tasks = [task for task in existing_tasks if task.get("task_id") != task_id]

        if len(updated_tasks) != len(existing_tasks):
            # Store back to Redis
            if updated_tasks:
                redis_client.setex(key, settings.redis_expiry, json.dumps(updated_tasks))
            else:
                redis_client.delete(key)
            logger.info(f"Unregistered task {task_id} for learning path {learning_path_id}")

    except Exception as e:
        logger.error(f"Error unregistering task {task_id} for learning path {learning_path_id}: {str(e)}")

async def get_learning_path_tasks(learning_path_id: int) -> List[Dict[str, Any]]:
    """
    Get all registered tasks for a learning path.

    Args:
        learning_path_id: ID of the learning path

    Returns:
        List of task information dictionaries
    """
    try:
        redis_client = get_redis_client()
        key = f"{settings.redis_key_prefix}{learning_path_id}"

        tasks_data = redis_client.get(key)
        if tasks_data:
            return json.loads(await _safe_decode_redis_data(tasks_data))
        return []

    except Exception as e:
        logger.error(f"Error getting tasks for learning path {learning_path_id}: {str(e)}")
        return []

async def cancel_learning_path_tasks(learning_path_id: int) -> List[str]:
    """
    Cancel all registered quiz generation tasks for a learning path.

    Args:
        learning_path_id: ID of the learning path

    Returns:
        List of cancelled task IDs
    """
    cancelled_tasks = []

    try:
        from app.celery_app import celery_app

        # Get registered tasks
        tasks = await get_learning_path_tasks(learning_path_id)

        for task_info in tasks:
            task_id = task_info.get("task_id")
            task_type = task_info.get("task_type", "unknown")

            if task_id:
                try:
                    # Cancel the task
                    celery_app.control.revoke(task_id, terminate=True)
                    cancelled_tasks.append(task_id)
                    logger.info(f"Cancelled {task_type} task {task_id} for learning path {learning_path_id}")
                except Exception as cancel_error:
                    logger.error(f"Error cancelling task {task_id}: {str(cancel_error)}")

        # Clear the task registry for this learning path
        if cancelled_tasks:
            redis_client = get_redis_client()
            key = f"{settings.redis_key_prefix}{learning_path_id}"
            redis_client.delete(key)
            logger.info(f"Cleared task registry for learning path {learning_path_id}")

    except Exception as e:
        logger.error(f"Error cancelling tasks for learning path {learning_path_id}: {str(e)}")

    return cancelled_tasks

async def register_path_task(user_id: str, task_id: str, task_type: str = "path_generation", **kwargs) -> None:
    """
    Register a path generation task for a user.

    Args:
        user_id: User ID
        task_id: Celery task ID
        task_type: Type of task (path_generation, streaming_path_generation, etc.)
        **kwargs: Additional task metadata
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            logger.warning("Redis not available for task registration")
            return

        key = f"path_tasks:{user_id}"

        task_info = {
            "task_id": task_id,
            "task_type": task_type,
            "registered_at": datetime.now().isoformat(),
            "status": "running",
            **kwargs
        }

        # Store task info using hash
        redis_client.hset(key, task_id, json.dumps(task_info))
        redis_client.expire(key, 86400)  # 24 hour expiry

        logger.info(f"Registered {task_type} task {task_id} for user {user_id}")

    except Exception as e:
        logger.error(f"Error registering path task {task_id}: {str(e)}")


async def unregister_path_task(user_id: str, task_id: str) -> None:
    """
    Unregister a completed path generation task.

    Args:
        user_id: User ID
        task_id: Task ID to remove
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return

        key = f"path_tasks:{user_id}"
        redis_client.hdel(key, task_id)

        logger.info(f"Unregistered path task {task_id} for user {user_id}")

    except Exception as e:
        logger.error(f"Error unregistering path task {task_id}: {str(e)}")


async def get_user_path_tasks(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all path generation tasks for a user.

    Args:
        user_id: User ID

    Returns:
        List of task information dictionaries
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return []

        key = f"path_tasks:{user_id}"
        task_data = redis_client.hgetall(key)

        tasks = []
        for task_id, task_info_str in task_data.items():
            try:
                task_info = json.loads(task_info_str)
                task_info["task_id"] = task_id
                tasks.append(task_info)
            except json.JSONDecodeError:
                logger.warning(f"Invalid task data for task {task_id}")

        return tasks

    except Exception as e:
        logger.error(f"Error getting path tasks for user {user_id}: {str(e)}")
        return []

async def _safe_decode_redis_data(data: Any) -> str:
    """
    Safely decode Redis data whether it's bytes or string.

    Args:
        data: Data from Redis (could be bytes or string)

    Returns:
        Decoded string data
    """
    if data is None:
        return ""

    # If data is already a string (decode_responses=True), return as-is
    if isinstance(data, str):
        return data

    # If data is bytes, decode it
    if isinstance(data, bytes):
        return data.decode('utf-8')

    # For other types, convert to string
    return str(data)
