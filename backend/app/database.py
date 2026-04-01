import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models import Base

# Database URL from environment or default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

is_postgresql = "postgresql" in DATABASE_URL

# For async support, we use asyncpg for PostgreSQL
if is_postgresql:
    # Convert postgresql:// to postgresql+asyncpg://
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    # PostgreSQL supports connection pooling
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
else:
    # SQLite does NOT support pool_size/max_overflow — use NullPool to avoid issues
    from sqlalchemy.pool import NullPool
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )


# Create session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
