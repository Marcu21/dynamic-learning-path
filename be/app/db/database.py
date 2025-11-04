from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

ASYNC_DATABASE_URL = settings.database_url

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=50,
    max_overflow=100,
    pool_timeout=30,
    echo=False,

    pool_reset_on_return='commit',
    connect_args={
        "server_settings": {
            "jit": "off",
        }
    }
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db_session():
    """
    FastAPI dependency for asynchronous database sessions.

    This function uses an 'async with' block to ensure that the session
    is always properly closed and that transactions are correctly handled
    (committed on success, rolled back on error).
    """
    async with AsyncSessionLocal() as session:
        yield session