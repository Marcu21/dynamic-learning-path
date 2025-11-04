"""
Enhanced Path Generation Tasks
=============================

This module provides enhanced Celery tasks for learning path generation with
integrated quiz generation support. After a learning path is successfully
generated, it can automatically trigger quiz generation for all modules.

Key Features:
- Asynchronous path generation using streaming workflow
- Automatic quiz generation after path completion
- Real-time progress updates via Redis channels
- Task chaining and coordination between path and quiz generation
- Comprehensive error handling and recovery
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.celery_app import celery_app
from app.core.config import settings
from app.core.logger import get_logger
from app.core.redis_publisher import RedisPublisher
from app.models.enums import ExperienceLevel, LearningStyle
from app.services.ai_services.workflows.path_generation_workflow import (
    StreamingPathGenerationWorkflow,
    StreamEventType
)
from app.repositories import learning_path_repository, notification_repository
from app.services.core_services import task_tracking_service
from app.api.v1.websockets.notifications import NotificationWebSocketManager
from app.tasks.chat_assistant_tasks import run_async_in_sync
from app.db.database import AsyncSessionLocal
from app.schemas.core_schemas.notification_schema import NotificationType
from app.db.celery_database import get_celery_db_session


logger = get_logger(__name__)


async def get_learning_path(learning_path_id: int) -> Optional[str]:
    """
    Get learning path title by ID.
    
    Args:
        learning_path_id: ID of the learning path
        
    Returns:
        Learning path title or None if not found
    """
    try:
        async with AsyncSessionLocal() as async_db_session:
            learning_path = await learning_path_repository.get_by_id(async_db_session, learning_path_id)
            if learning_path:
                return learning_path.title
            return None
    except Exception as e:
        logger.error(f"Error getting learning path {learning_path_id}: {str(e)}")
        return None


def publish_path_event(stream_channel: str, event_type: str, data: Dict[str, Any]) -> None:
    """
    Publish path generation events to Redis channel for real-time updates.

    Args:
        stream_channel: Redis channel name
        event_type: Type of event
        data: Event data dictionary
    """
    try:
        redis_publisher = RedisPublisher()

        event_data = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data
        }

        success = redis_publisher.publish(stream_channel, json.dumps(event_data))
        if success:
            logger.info(f"Published {event_type} event to channel {stream_channel}")
        else:
            logger.warning(f"Failed to publish {event_type} event to channel {stream_channel}")

    except Exception as e:
        logger.error(f"Error publishing path event: {str(e)}")


@celery_app.task(bind=True, name="generate_learning_path_stream")
def generate_learning_path_stream_task(
        self,
        user_id: str,
        subject: str,
        experience_level: str,
        learning_styles: List[str],
        preferred_platforms: List[str],
        study_time_minutes: int,
        goals: str,
        team_id: Optional[str] = None,
        stream_channel: Optional[str] = None,
        enable_quiz_generation: bool = True,
        quiz_questions_per_module: int = settings.default_quiz_questions
) -> Dict[str, Any]:
    """
    Enhanced Celery task for streaming learning path generation with quiz support.

    This task runs the streaming path generation workflow and optionally
    triggers quiz generation for all modules after path completion.
    """
    task_id = self.request.id

    if not stream_channel:
        stream_channel = f"path_generation_{user_id}_{task_id}"

    logger.info(f"Starting enhanced path generation task {task_id} for user {user_id}")
    logger.info(f"Quiz generation enabled: {enable_quiz_generation}")

    with get_celery_db_session() as db_session:
        try:
            run_async_in_sync(task_tracking_service.register_path_task(
                user_id, task_id, "enhanced_path_generation", team_id=team_id
            ))

            self.update_state(
                state="STARTED",
                meta={ "stage": "initialization", "progress": 0, "stream_channel": stream_channel }
            )

            publish_path_event(stream_channel, "generation_started", {
                "task_id": task_id, "message": "Starting learning path generation..."
            })

            workflow = StreamingPathGenerationWorkflow(db_session=db_session)

            experience_level_enum = ExperienceLevel(experience_level)
            learning_styles_enums = [LearningStyle(style) for style in learning_styles]

            learning_path_id = None
            total_modules = 0
            generation_successful = False

            async def run_generation():
                nonlocal learning_path_id, total_modules, generation_successful
                try:
                    async for stream_event in workflow.generate_learning_path_stream(
                        user_id=user_id, subject=subject, experience_level=experience_level_enum,
                        learning_styles=learning_styles_enums, preferred_platforms=preferred_platforms,
                        study_time_minutes=study_time_minutes, goals=goals, team_id=team_id,
                    ):
                        self.update_state(state="PROGRESS", meta={
                            "stage": stream_event.stage.value, "progress": stream_event.progress_percentage
                        })
                        publish_path_event(stream_channel, stream_event.event_type.value, stream_event.data)
                        if stream_event.event_type == StreamEventType.LEARNING_PATH_INFO:
                            learning_path_id = stream_event.data.get("learning_path_id")
                            total_modules = stream_event.data.get("total_modules", 0)
                    generation_successful = True
                except Exception as gen_error:
                    logger.error(f"Streaming generation failed: {str(gen_error)}")
                    raise gen_error

            run_async_in_sync(run_generation())

            results = {
                "learning_path_id": learning_path_id,
                "generation_successful": generation_successful,
                "team_id": team_id
            }

            if generation_successful and learning_path_id:
                logger.info(f"Path generation successful. Learning path ID: {learning_path_id}")

                async def notify_users():
                    async with AsyncSessionLocal() as async_db:
                        from app.repositories.team_repository import get_team_members

                        learning_path_title = await get_learning_path(learning_path_id) or subject

                        users_to_notify = []
                        if team_id:
                            team_members = await get_team_members(async_db, team_id)
                            users_to_notify = [member.user_id for member in team_members]
                            message = f"A new learning path '{learning_path_title}' has been added to your team."
                            notif_type = NotificationType.TEAM_LEARNING_PATH_GENERATED
                        else:
                            users_to_notify.append(user_id)
                            message = f"Your new learning path '{learning_path_title}' is ready!"
                            notif_type = NotificationType.LEARNING_PATH_GENERATED

                        for uid in users_to_notify:
                            # 1. Persist notification to DB
                            await notification_repository.create_notification(
                                db=async_db, user_id=uid, notification_type=notif_type,
                                title="Learning Path Ready", message=message,
                                learning_path_id=learning_path_id, team_id=team_id
                            )
                            # 2. Send WebSocket notification to stop animation
                            await NotificationWebSocketManager.send_notification_to_user(
                                user_id=uid,
                                notification_data={
                                    "type": "task_completed", "task_id": task_id,
                                    "result": results, "message": message, "team_id": team_id
                                }
                            )
                        logger.info(f"Sent completion notifications to {len(users_to_notify)} user(s).")

                run_async_in_sync(notify_users())

                # Automatic quiz generation after path completion
                if enable_quiz_generation and total_modules > 0:
                    logger.info(f"Starting automatic quiz generation for learning path {learning_path_id}")

                    try:
                        # Update progress to show quiz generation starting
                        self.update_state(
                            state="PROGRESS",
                            meta={
                                "stage": "quiz_generation_starting",
                                "progress": 90,
                                "learning_path_id": learning_path_id
                            }
                        )

                        publish_path_event(stream_channel, "quiz_generation_starting", {
                            "learning_path_id": learning_path_id,
                            "total_modules": total_modules,
                            "questions_per_module": quiz_questions_per_module,
                            "message": f"Starting quiz generation for {total_modules} modules..."
                        })

                        # Import and execute quiz generation task
                        from app.tasks.quiz_tasks import generate_learning_path_quizzes_task

                        # Execute quiz generation as part of this task
                        quiz_result = generate_learning_path_quizzes_task.__wrapped__(
                            generate_learning_path_quizzes_task,
                            learning_path_id=learning_path_id,
                            user_id=user_id,
                            num_questions_per_module=quiz_questions_per_module,
                            stream_channel=stream_channel
                        )

                        logger.info(f"Quiz generation completed: {quiz_result}")

                        # Update results with quiz info
                        results.update({
                            "quiz_generation_successful": quiz_result.get("success", False),
                            "quizzes_generated": quiz_result.get("quizzes_generated", 0)
                        })

                    except Exception as quiz_error:
                        logger.error(f"Quiz generation failed: {str(quiz_error)}")
                        results.update({
                            "quiz_generation_successful": False,
                            "quiz_generation_error": str(quiz_error)
                        })

            self.update_state(state="SUCCESS", meta={ "stage": "completed", "progress": 100, "results": results })
            publish_path_event(stream_channel, "generation_complete", { **results, "message": "Path generation complete." })

            return results

        except Exception as e:
            error_msg = f"Path generation failed for task {task_id}: {str(e)}"
            logger.error(error_msg)
            publish_path_event(stream_channel, "error_event", { "error": str(e), "message": "Path generation failed." })
            self.update_state(state='FAILURE', meta={ 'error': str(e) })
            raise Exception(error_msg)
        finally:
            run_async_in_sync(task_tracking_service.unregister_path_task(user_id, task_id))
