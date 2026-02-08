"""Database engine and session management for SQLAlchemy 2.0."""

import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Database URL from environment or default to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/wegent"
)

# For sync operations (Alembic migrations)
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")

# Create async engine with connection pooling
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# Create sync engine for migrations
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session makers
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

SessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session as a context manager."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a sync database session as a context manager."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_db() -> None:
    """Initialize the database by creating all tables."""
    from backend.database.base import Base
    from backend.models.kinds import Kind  # noqa: F401
    from backend.models.tasks import Task  # noqa: F401
    from backend.models.user import User  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync() -> None:
    """Initialize the database synchronously (for migrations)."""
    from backend.database.base import Base
    from backend.models.kinds import Kind  # noqa: F401
    from backend.models.tasks import Task  # noqa: F401
    from backend.models.user import User  # noqa: F401

    Base.metadata.create_all(bind=sync_engine)


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()
    sync_engine.dispose()


# FastAPI dependency for database sessions
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session for FastAPI dependency injection.

    Yields:
        AsyncSession: Database session that will be committed on success
            or rolled back on exception.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
