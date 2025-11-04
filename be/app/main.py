from fastapi import FastAPI
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
import redis

# Import routers
from app.api.v1.endpoints.learning_paths import router as learning_paths_router
from app.api.v1.endpoints.modules import router as modules_router
from app.api.v1.endpoints.path_generation import router as learning_path_generation_router
from app.api.v1.endpoints.quizzes import router as quizzes_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.teams import router as teams_router
from app.api.v1.endpoints.users import router as api_users_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.chat_assistant import router as chat_learning_path_router
from app.api.v1.endpoints.module_insertion import router as module_insertion_router
from app.api.v1.websockets.notifications import router as websockets_router

# Database and models
from app.db.database import async_engine, Base
from app.models import *  # Import all models to register them

# Core utilities
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting application...")
    
    try:
        # Create database tables using the async engine
        logger.info("Creating database tables...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully!")
        
        # Initialize database
        logger.info("Initializing database...")
        logger.info("Database initialization completed!")
        
        # Validate Redis connection
        validate_redis_connection()
        
        # Check Celery connection
        celery_available = await check_celery_connection()
        if celery_available:
            logger.info("Celery workers are available")
        else:
            logger.warning("Celery workers not available - background tasks disabled")
            
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    # Clean up Redis connections
    try:
        from app.core.redis_publisher import _redis_pool
        if _redis_pool:
            _redis_pool.disconnect()
            logger.info("Redis pool disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting Redis pool: {e}")

# Create FastAPI application with optimized settings for concurrency
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    # Optimize for multiple concurrent users
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Health check endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running successfully"}

@app.get("/api/v1/health")
def health_check_v1():
    return {"status": "healthy", "message": "API v1 is running successfully"}

# Register API routers
app.include_router(auth_router)
app.include_router(api_users_router)
app.include_router(learning_paths_router)
app.include_router(modules_router)
app.include_router(learning_path_generation_router)
app.include_router(quizzes_router)
app.include_router(teams_router)
app.include_router(notifications_router)
app.include_router(chat_learning_path_router)
app.include_router(module_insertion_router)
app.include_router(websockets_router)

async def check_celery_connection() -> bool:
    """Check if Celery is available and workers are running"""
    try:
        from app.celery_app import celery_app
        inspector = celery_app.control.inspect()
        active_workers = inspector.active()
        return bool(active_workers)
    except ImportError:
        logger.warning("Celery not imported - background tasks disabled")
        return False
    except Exception as e:
        logger.warning(f"Celery connection check failed: {str(e)}")
        return False

def validate_redis_connection() -> bool:
    """Validate Redis connection on startup"""
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        # Test connection
        redis_client.ping()
        logger.info("Redis connection validated successfully")
        return True
        
    except redis.ConnectionError:
        logger.error("Redis connection failed - caching will be disabled")
        return False
    except Exception as e:
        logger.error(f"Unexpected Redis error: {str(e)}")
        return False
