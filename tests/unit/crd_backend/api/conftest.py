"""Fixtures for API tests."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.base import Base
from backend.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def async_client():
    """Create an async HTTP client for testing with isolated database per test."""
    # Create engine and tables for this test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create app with test database
    app = create_app()

    # Override the database dependency
    from backend.api.v1.kinds import get_db_session

    async def override_get_db_session():
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with async_session() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
