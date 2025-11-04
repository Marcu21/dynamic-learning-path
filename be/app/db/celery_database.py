from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

celery_database_url = settings.database_url
if "postgresql+asyncpg://" in celery_database_url:
    celery_database_url = celery_database_url.replace("postgresql+asyncpg://", "postgresql://")
elif "postgresql+psycopg2://" in celery_database_url:
    celery_database_url = celery_database_url.replace("postgresql+psycopg2://", "postgresql://")

celery_engine = create_engine(
    celery_database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

CelerySessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=celery_engine
)

@contextmanager
def get_celery_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in Celery tasks.
    Ensures proper cleanup and error handling.
    """
    session = CelerySessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error in Celery task: {str(e)}")
        raise
    finally:
        session.close()

def get_celery_db_session_sync() -> Session:
    """
    Get a database session for synchronous Celery tasks.
    Remember to close the session manually.
    """
    return CelerySessionLocal()
