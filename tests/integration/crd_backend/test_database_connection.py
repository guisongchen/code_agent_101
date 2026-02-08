"""Tests for database connection and session management.

Tests: 3 tests covering database connection functionality
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Create test engines using SQLite
TEST_ASYNC_DB_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def test_async_engine():
    """Create a test async engine."""
    engine = create_async_engine(TEST_ASYNC_DB_URL)
    yield engine
    engine.sync_engine.dispose()


@pytest.fixture
def test_sync_engine():
    """Create a test sync engine."""
    engine = create_engine(TEST_SYNC_DB_URL)
    yield engine
    engine.dispose()


@pytest.mark.epic_7
@pytest.mark.integration
@pytest.mark.backend
class TestDatabaseConnection:
    """Test suite for database connections - 3 tests."""

    @pytest.mark.asyncio
    async def test_async_session_context_manager(self, test_async_engine):
        """Test async session context manager handles transactions."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        AsyncSessionLocal = async_sessionmaker(
            test_async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with AsyncSessionLocal() as session:
            assert isinstance(session, AsyncSession)
            # Test that we can execute a query
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1

    def test_sync_session_context_manager(self, test_sync_engine):
        """Test sync session context manager handles transactions."""
        SessionLocal = sessionmaker(test_sync_engine)

        with SessionLocal() as session:
            assert isinstance(session, Session)
            # Test that we can execute a query
            result = session.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1

    def test_database_url_configuration(self):
        """Test database URL can be configured via environment."""
        custom_url = "postgresql+asyncpg://custom:custom@localhost:5432/customdb"

        with patch.dict(os.environ, {"DATABASE_URL": custom_url}):
            # Re-import to pick up new environment variable
            import importlib

            from backend.database import engine

            importlib.reload(engine)

            # The engine should use the custom URL
            # Note: We can't actually connect, but we can verify the configuration
            assert engine.DATABASE_URL == custom_url
            assert engine.SYNC_DATABASE_URL == custom_url.replace("+asyncpg", "+psycopg2")
