"""Fixtures for service tests."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.database.base import Base
from backend.models.kinds import Kind, KindType
from backend.schemas.ghost import GhostSpec, GhostCRD, Metadata
from backend.schemas.model import ModelConfig, ModelSpec, ModelCRD
from backend.schemas.shell import ShellSpec, ShellCRD
from backend.schemas.bot import BotSpec, BotCRD
from backend.schemas.team import TeamSpec, TeamCRD, TeamMember
from backend.schemas.base import ResourceRef


# Use SQLite for async tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    """Create a fresh async database session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def ghost_schema():
    """Create a sample Ghost schema."""
    return GhostCRD(
        metadata=Metadata(name="test-ghost", namespace="default"),
        spec=GhostSpec(system_prompt="You are a helpful assistant."),
    )


@pytest.fixture
def model_schema():
    """Create a sample Model schema."""
    return ModelCRD(
        metadata=Metadata(name="test-model", namespace="default"),
        spec=ModelSpec(
            config=ModelConfig(provider="openai", model_name="gpt-4"),
        ),
    )


@pytest.fixture
def shell_schema():
    """Create a sample Shell schema."""
    return ShellCRD(
        metadata=Metadata(name="test-shell", namespace="default"),
        spec=ShellSpec(type="chat"),
    )


@pytest.fixture
def bot_schema(ghost_schema, model_schema, shell_schema):
    """Create a sample Bot schema with valid references."""
    return BotCRD(
        metadata=Metadata(name="test-bot", namespace="default"),
        spec=BotSpec(
            ghost_ref=ResourceRef(
                kind=KindType.GHOST,
                name=ghost_schema.metadata.name,
                namespace=ghost_schema.metadata.namespace,
            ),
            model_ref=ResourceRef(
                kind=KindType.MODEL,
                name=model_schema.metadata.name,
                namespace=model_schema.metadata.namespace,
            ),
            shell_ref=ResourceRef(
                kind=KindType.SHELL,
                name=shell_schema.metadata.name,
                namespace=shell_schema.metadata.namespace,
            ),
        ),
    )


@pytest.fixture
def team_schema(bot_schema):
    """Create a sample Team schema with valid references."""
    return TeamCRD(
        metadata=Metadata(name="test-team", namespace="default"),
        spec=TeamSpec(
            members=[
                TeamMember(
                    bot_ref=ResourceRef(
                        kind=KindType.BOT,
                        name=bot_schema.metadata.name,
                        namespace=bot_schema.metadata.namespace,
                    ),
                    role="leader",
                ),
            ],
        ),
    )
