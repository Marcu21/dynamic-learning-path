"""
Celery Application Configuration
===============================

Essential Celery configuration for path generation, quiz generation, and chat assistant tasks.
"""

from celery import Celery
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Create Celery application instance
celery_app = Celery(
    "learning_path_app",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        'app.tasks.path_generation_tasks',
        'app.tasks.quiz_tasks',
        'app.tasks.chat_assistant_tasks',
        'app.tasks.module_insertion_tasks',
    ]
)

# Essential Celery Configuration
celery_app.conf.update(
    # Task Settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Keep results for WebSocket notifications
    task_ignore_result=False,
    result_backend=settings.celery_result_backend,

    # Task Result Settings
    result_expires=7200,  # 2 hours

    # Task Routing
    task_routes={
        # Path generation
        'generate_learning_path_stream': {'queue': 'path_generation'},

        # Quiz generation and grading
        'generate_learning_path_quizzes': {'queue': 'quiz_generation'},
        'generate_module_quiz': {'queue': 'quiz_generation'},
        'grade_quiz_submission': {'queue': 'quiz_grading'},

        # Chat assistant tasks
        'app.tasks.chat_assistant_tasks.stream_chat_response_background': {'queue': 'chat_assistant'},

        # Module insertion tasks
        'insert_module': {'queue': 'module_insertion'},
    },

    # Worker Settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_disable_rate_limits=False,
    worker_concurrency=None,  # Let Docker compose control concurrency per worker

    # Connection Pool Settings
    broker_pool_limit=20,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,

    # Connection Settings - Optimized for high concurrency
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 hour
        'fanout_prefix': True,
        'fanout_patterns': True,
        'priority_steps': list(range(10)),
        'sep': ':',
        'queue_order_strategy': 'priority',
        'master_name': None,
    },

    # Redis-specific optimizations
    redis_max_connections=50,
    redis_socket_keepalive=True,
    redis_socket_keepalive_options={},

    # Task Error Handling
    task_soft_time_limit=1500,
    task_time_limit=1800,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Task Retry Settings
    task_default_retry_delay=30,
    task_max_retries=2,
)

# Import tasks to register them with Celery
try:
    from app.tasks import path_generation_tasks
    from app.tasks import quiz_tasks
    from app.tasks import chat_assistant_tasks
    logger.info("Celery tasks imported successfully")
except ImportError as e:
    logger.warning(f"Failed to import some Celery tasks: {e}")

# Make celery_app available for imports
__all__ = ['celery_app']