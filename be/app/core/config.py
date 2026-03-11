from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application configuration using Pydantic BaseSettings.
    Automatically loads environment variables from .env file.
    """
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    
    app_name: str = Field(
        default="Dynamic Learning Path API",
        description="Application name"
    )

    app_description: str = Field(
        default="AI-powered personalized learning path generation system",
        description="Application description"
    )

    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    environment: str = Field(
        default="development",
        description="Environment: development, production"
    )
    
    # =============================================================================
    # SERVER SETTINGS
    # =============================================================================
    
    server_url: str = Field(
        default="http://localhost:3000",
        description="Host to bind the application"
    )
    
    # =============================================================================
    # PLATFORM API KEYS
    # =============================================================================

    youtube_api_key: str = Field(
        default='none',
        description="YouTube API key for video content retrieval"
    )
    
    google_books_api_key: str = Field(
        default="none",
        description="Google Books API key"
    )

    spotify_client_id: str = Field(
        default='none',
        description="Spotify Client ID for audiobook content retrieval"
    )

    spotify_client_secret: str = Field(
        default='none',
        description="Spotify Client Secret for audiobook content retrieval"
    )
    
    coursera_client_id: str = Field(
        default='none',
        description="Coursera Client ID for course content retrieval"
    )
    
    coursera_client_secret: str = Field(
        default='none',
        description="Coursera Client Secret for course content retrieval"
    )
    
    coursera_app_id: str = Field(
        default='none',
        description="Coursera Organization ID for business/organization content retrieval"
    )
    
    coursera_api_key: str = Field(
        default='none',
        description="Coursera API key for course content retrieval"
    )

    # =============================================================================
    # AUTHENTICATION SETTINGS
    # =============================================================================
    
    secret_key: str = Field(
        default="none",
        description="Secret key for JWT token signing"
    )
    
    algorithm: str = Field(
        default="HS256",
        description="JWT token algorithm"
    )
    
    access_token_expire_minutes: int = Field(
        default=1000,
        description="JWT access token expiration time in minutes"
    )

    # Resend Email Settings
    resend_api_key: str = Field(
        default="none",
        description="Resend API key for email sending"
    )
    
    from_email: str = Field(
        default="noreply@yourdomain.com",
        description="From email address for authentication emails"
    )
    
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for magic link redirects"
    )


    # =============================================================================
    # CORS SETTINGS
    # =============================================================================
    
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    cors_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )
    
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed CORS methods"
    )
    
    cors_headers: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )
    
    # =============================================================================
    # CELERY SETTINGS
    # =============================================================================
    
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )

    # Task timeouts
    celery_task_time_limit: int = Field(
        default=30 * 60,
        description="Celery task time limit"
    )
    celery_task_soft_time_limit: int = Field(
        default=25 * 60,
        description="Celery task soft time limit"
    )
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================

    redis_host: str = Field(
        default="localhost",
        description="Redis host"
    )
    redis_port: int = Field(
        default=6379,
        description="Redis port"
    )
    redis_db: int = Field(
        default=0,
        description="Redis database number"
    )
    
    redis_url: str = Field(
        default=f"redis://{redis_host}:{redis_port}/{redis_db}",
        description="Redis connection URL"
    )

    redis_key_prefix: str = Field(
        default="quiz_tasks:learning_path:",
        description="Prefix for Redis keys"
    )

    redis_expiry: int = Field(
        default=3600 * 6,  # 6 hours in seconds
        description="Redis key expiry time in seconds"
    )
    
    # Content pool caching settings
    content_pool_cache_ttl: int = 604800  # 7 days in seconds
    content_pool_cache_prefix: str = "content_pool:"
    enable_content_pool_caching: bool = True
    
    # Bridge module generation settings
    bridge_module_max_retries: int = 3
    bridge_module_timeout: int = 60
    bridge_content_selection_temperature: float = 0.3
    
    # Module insertion settings
    max_modules_per_learning_path: int = 20
    allow_duplicate_content_in_bridges: bool = False
    bridge_module_difficulty_tolerance: int = 1  # Max difficulty level difference

    # =============================================================================
    # AI & LANGCHAIN SETTINGS
    # =============================================================================

    llm_api_key: str = Field(
        default="abcdefghijklmnopqrstuvwxyz1234567890",
        description="LLM API key"
    )
    
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model"
    )
    
    llm_url: str = Field(
        default="https://api.openai.com/v1/chat/completions",
        description="LLM API URL"
    )
    
    # Timeout
    llm_request_timeout: int = Field(default=900, description="LLM request timeout in seconds")

    # Add retry settings
    llm_max_retries: int = Field(default=3, description="Maximum number of LLM request retries")
    llm_retry_delay: float = Field(default=2.0, description="Delay between LLM retries in seconds")
    
    # =============================================================================
    # QUIZ SETTINGS
    # =============================================================================
    
    default_quiz_questions: int = Field(default=6, description="Default number of questions per quiz")
    default_quiz_passing_score: float = Field(default=0.666, description="Default passing score for quizzes (6.66/10 = 66.6%)")
    default_quiz_time_limit: int = Field(default=10, description="Default time limit in minutes")
    max_quiz_questions: int = Field(default=20, description="Maximum questions per quiz")
    min_quiz_questions: int = Field(default=5, description="Minimum questions per quiz")
    quiz_generation_timeout: int = Field(default=300, description="Quiz generation timeout in seconds")

    # =============================================================================
    # SKILL-POINTS SETTINGS
    # =============================================================================
    default_module_skill_points: int = Field(default=25,description="Default skill points awarded for completing a module")
    default_quiz_skill_points: int = Field(default=30,description="Default skill points awarded for passing a quiz")
    default_path_skill_points: int = Field(default=50,description="Default skill points awarded for completing a learning path")

    # =============================================================================
    # TIMEZONE SETTINGS
    # =============================================================================
    
    timezone: str = Field(
        default="Etc/GMT-2",
        description="Application timezone (UTC+2)"
    )
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    
    database_url: str = Field(
        default="sqlite:///./learning_path.db",
        description="Database connection URL"
    )
    
    # =============================================================================
    # LOGGING SETTINGS
    # =============================================================================
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    log_dir: str = Field(
        default="logs",
        description="Directory for log files"
    )

    log_max_bytes: int = Field(
        default=5 * 1024 * 1024,  # 5 MB
        description="Maximum size of log files before rotation"
    )

    log_backup_count: int = Field(
        default=3,
        description="Number of backup log files to keep"
    )
    
    # =============================================================================
    # CONTENT GENERATION SETTINGS
    # =============================================================================
    
    min_number_of_modules: int = Field(
        default=2,
        description="Minimum number of modules per learning path"
    )
    
    max_number_of_modules: int = Field(
        default=8,
        description="Maximum number of modules per learning path"
    )
    
    # =============================================================================
    # HELPER PROPERTIES
    # =============================================================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    @property
    def debug(self) -> bool:
        """Debug mode enabled in development"""
        return self.is_development
    
    # =============================================================================
    # PYDANTIC CONFIG
    # =============================================================================
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = ""
        validate_assignment = True
        use_enum_values = True
        extra = "allow"  # Allow extra fields to prevent validation errors
        
# =============================================================================
# CONFIGURATION INSTANCE AND HELPER FUNCTIONS
# =============================================================================

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """
    Dependency function to get settings instance.
    Can be used in FastAPI dependency injection.
    """
    return settings

def validate_configuration() -> bool:
    """
    Validate that all required configuration is present and valid.
    Returns True if configuration is valid, raises exception otherwise.
    """
    try:
        # Test database URL format
        if not settings.database_url.startswith('sqlite'):
            logger.warning("Non-SQLite database detected - ensure proper configuration")
        
        # Validate environment-specific settings
        if settings.is_production:
            if settings.secret_key == "your-secret-key-change-this-in-production":
                raise ValueError("Secret key must be changed in production")
            if settings.resend_api_key == "your-resend-api-key-here" or settings.resend_api_key == "none":
                raise ValueError("Resend API key must be configured in production")
            if settings.debug:
                logger.warning("Debug mode should be disabled in production")
        
        # Validate authentication settings
        if len(settings.secret_key) < 32:
            logger.warning("Secret key should be at least 32 characters long")
            
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        raise

if __name__ == "__main__":
    validate_configuration()
