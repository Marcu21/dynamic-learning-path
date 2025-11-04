"""
Module Insertion Celery Tasks
=============================

This module contains essential Celery tasks for module insertion operations.
Tasks are designed to handle asynchronous module insertion with proper error handling,
logging, and notification delivery.

Key Features:
- Asynchronous module insertion workflow execution
- Comprehensive error handling and recovery
- Progress tracking and status updates
- Automatic retry mechanisms
- Task result persistence
- User notification integration
- WebSocket task completion events
"""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tasks.quiz_tasks import generate_module_quiz_task
from app.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.schemas.core_schemas.notification_schema import NotificationType
from app.services.ai_services.workflows.module_insertion_workflow import ModuleInsertionWorkflow
from app.repositories import learning_path_repository, notification_repository
from app.api.v1.websockets.notifications import NotificationWebSocketManager
from app.tasks.chat_assistant_tasks import run_async_in_sync

logger = get_logger(__name__)

async def _send_completion_notification(
        db: AsyncSession,
        user_id: str,
        result: Dict[str, Any],
        success: bool
) -> None:
    """
    Send notification about task completion.
    """
    try:
        if success:
            title = "Module Inserted Successfully"
            message = (
                f"Your module '{result.get('module_title', 'New Module')}' has been "
                f"successfully inserted into your learning path '{result.get('learning_path_title', '')}' at position {result.get('insert_position')}."
            )
            notification_type = NotificationType.MODULE_COMPLETED
        else:
            title = "Module Insertion Failed"
            message = (
                f"Failed to insert module into your learning path. "
                f"Error: {result.get('error', 'Unknown error')}"
            )
            notification_type = NotificationType.MODULE_COMPLETED

        await notification_repository.create_notification(
            db=db,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            learning_path_id=result.get('learning_path_id'),
            module_id=result.get('created_module_id')
        )

    except Exception as e:
        logger.error(f"Failed to send completion notification: {str(e)}")
        # No rollback here, let the caller handle it

# NEW & FIXED: Add and fix the error notification helper
async def _send_error_notification(
        db: AsyncSession,
        user_id: str,
        learning_path_id: int,
        error_message: str
) -> None:
    """
    Send notification about a task error.
    """
    try:
        await notification_repository.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.MODULE_COMPLETED, # Or a dedicated error type
            title="Module Insertion Failed",
            message=f"Failed to insert a module into your learning path. Error: {error_message}",
            learning_path_id=learning_path_id
        )
    except Exception as e:
        logger.error(f"Failed to send error notification: {str(e)}")

# =============================================================================
# MAIN MODULE INSERTION TASK
# =============================================================================
async def _insert_module_async(
    user_query: str,
    learning_path_id: int,
    insert_position: int,
    platform_name: str,
    user_id: str,
    task: Any
) -> Dict[str, Any]:
    """Asynchronous helper to run the module insertion workflow."""
    result = {}
    async with AsyncSessionLocal() as db:
        try:
            learning_path = await learning_path_repository.get_by_id(db, learning_path_id)
            if not learning_path:
                raise ValueError(f"Learning path {learning_path_id} not found")

            task.update_state(
                state='PROGRESS',
                meta={ 'stage': 'validation_complete', 'progress': 10, 'message': 'Input validation completed', 'learning_path_title': learning_path.title }
            )

            workflow = ModuleInsertionWorkflow(db)
            result = await _execute_workflow_with_progress(
                workflow, user_query, learning_path_id, insert_position, platform_name, user_id, task
            )

            result['learning_path_title'] = learning_path.title
            # await _send_completion_notification(db, user_id, result, success=result.get('success', False))

            return result
        except Exception as e:
            logger.error(f"Async workflow caught an exception: {e}")
            result['success'] = False
            result['error'] = str(e)
            result['learning_path_id'] = learning_path_id
            await _send_completion_notification(db, user_id, result, success=False)
            return result

# =============================================================================
# MAIN MODULE INSERTION TASK
# =============================================================================

@celery_app.task(bind=True, name="insert_module")
def insert_module_task(
        self,
        user_query: str,
        learning_path_id: int,
        insert_position: int,
        platform_name: str,
        user_id: str
) -> Dict[str, Any]:
    """
    Asynchronous Celery task for module insertion.
    """
    task_id = self.request.id
    start_time = datetime.now()

    logger.info(
        f"Starting module insertion task {task_id} - "
        f"User: {user_id}, Learning Path: {learning_path_id}, "
        f"Position: {insert_position}, Platform: {platform_name}"
    )

    self.update_state(
        state='PROGRESS',
        meta={
            'stage': 'initialization',
            'progress': 0,
            'message': 'Starting module insertion workflow',
            'started_at': start_time.isoformat()
        }
    )

    try:
        result = run_async_in_sync(
            _insert_module_async(
                user_query, learning_path_id, insert_position, platform_name, user_id, self
            )
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        final_result = {
            'success': result.get('success', False),
            'task_id': task_id,
            'execution_time_seconds': execution_time,
            'created_module_id': result.get('created_module_id'),
            'module_title': result.get('module_title'),
            'learning_path_id': learning_path_id,
            'insert_position': insert_position,
            'completed_at': datetime.now().isoformat(),
            'error': result.get('error')
        }

        if final_result['success']:
            logger.info(f"Module insertion task {task_id} completed successfully")
            self.update_state(state='SUCCESS', meta={'stage': 'completed', 'progress': 100, **final_result})
        else:
            logger.error(f"Module insertion task {task_id} failed: {final_result['error']}")
            self.update_state(state='FAILURE', meta={'stage': 'failed', 'progress': 0, **final_result})

        # Send WebSocket notification for task completion
        run_async_in_sync(NotificationWebSocketManager.send_notification_to_user(
            user_id=user_id,
            notification_data={
                "type": "task_completed",
                "task_id": task_id,
                "result": final_result,
                "message": f"Your module titled '{final_result.get('module_title')}' was successfully inserted into the learning path.",
                "completion_time": datetime.now().isoformat()
            }
        ))

        if final_result['success'] and final_result.get('created_module_id'):
            try:
                logger.info(f"Starting quiz generation for inserted module {final_result['created_module_id']}")

                # Trigger quiz generation task asynchronously
                quiz_task = generate_module_quiz_task.apply_async(
                    args=[
                        final_result['created_module_id'],  # module_id
                        user_id,  # user_id
                        settings.default_quiz_questions,  # num_questions (default)
                        False,  # regenerate
                        None  # stream_channel
                    ],
                    queue="quiz_generation"
                )

                # Update final result with quiz task info
                final_result['quiz_generation_triggered'] = True
                final_result['quiz_task_id'] = quiz_task.id

                logger.info(
                    f"Quiz generation task {quiz_task.id} triggered for module {final_result['created_module_id']}")

                # Send additional notification about quiz generation
                run_async_in_sync(NotificationWebSocketManager.send_notification_to_user(
                    user_id=user_id,
                    notification_data={
                        "type": "quiz_generation_started",
                        "module_id": final_result['created_module_id'],
                        "quiz_task_id": quiz_task.id,
                        "message": f"Quiz generation started for module '{final_result.get('module_title')}'",
                        "timestamp": datetime.now().isoformat()
                    }
                ))

            except Exception as quiz_error:
                logger.error(
                    f"Failed to trigger quiz generation for module {final_result['created_module_id']}: {str(quiz_error)}")
                final_result['quiz_generation_triggered'] = False
                final_result['quiz_generation_error'] = str(quiz_error)

        return final_result

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_message = str(e)

        logger.error(f"Module insertion task {task_id} encountered error: {error_message}")

        if _should_retry_error(e, self.request.retries):
            logger.info(f"Retrying module insertion task {task_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            final_failure_result = {
                'success': False, 'error': error_message, 'task_id': task_id,
                'execution_time_seconds': execution_time, 'failed_permanently': True
            }
            # Send WebSocket notification for permanent failure
            run_async_in_sync(NotificationWebSocketManager.send_notification_to_user(
                user_id=user_id,
                notification_data={
                    "type": "task_completed", "task_id": task_id,
                    "result": final_failure_result, "message": f"Module insertion failed permanently."
                }
            ))
            self.update_state(state='FAILURE', meta=final_failure_result)
            return final_failure_result

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _execute_workflow_with_progress(
        workflow: ModuleInsertionWorkflow,
        user_query: str,
        learning_path_id: int,
        insert_position: int,
        platform_name: str,
        user_id: str,
        task: Any
) -> Dict[str, Any]:
    """
    Execute workflow with progress updates to Celery task.
    """
    try:
        task.update_state(
            state='PROGRESS',
            meta={
                'stage': 'workflow_started',
                'progress': 20,
                'message': 'Starting module generation workflow'
            }
        )

        result = await workflow.insert_module(
            user_query, learning_path_id, insert_position, platform_name, user_id
        )

        if result.get('success'):
            task.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'workflow_completed',
                    'progress': 90,
                    'message': 'Module generation completed, finalizing...',
                    'created_module_id': result.get('created_module_id'),
                    'module_title': result.get('module_title')
                }
            )

        return result

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        task.update_state(
            state='PROGRESS',
            meta={
                'stage': 'workflow_failed',
                'progress': 0,
                'message': f'Workflow execution failed: {str(e)}'
            }
        )
        return {
            'success': False,
            'error': str(e)
        }


def _should_retry_error(error: Exception, retry_count: int) -> bool:
    """
    Determine if an error should trigger a task retry.
    """
    retryable_errors = [
        'Connection error',
        'Timeout',
        'Service temporarily unavailable',
        'Rate limit',
        'Database connection',
        'Temporary failure'
    ]
    error_message = str(error).lower()
    for retryable in retryable_errors:
        if retryable in error_message:
            return True

    permanent_errors = [
        'not found',
        'invalid',
        'unauthorized',
        'forbidden',
        'bad request'
    ]
    for permanent in permanent_errors:
        if permanent in error_message:
            return False

    return retry_count < 2