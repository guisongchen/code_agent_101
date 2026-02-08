"""
Pytest configuration and shared fixtures for all tests.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from chat_shell.agent.config import AgentConfig


# =============================================================================
# pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure custom markers for all tests."""
    # Epic markers
    config.addinivalue_line("markers", "epic_1: Epic 1 - Core Agent System")
    config.addinivalue_line("markers", "epic_2: Epic 2 - Multi-Model LLM Integration")
    config.addinivalue_line("markers", "epic_3: Epic 3 - Tools System")
    config.addinivalue_line("markers", "epic_4: Epic 4 - Deployment Modes")
    config.addinivalue_line("markers", "epic_5: Epic 5 - Streaming Response System")
    config.addinivalue_line("markers", "epic_6: Epic 6 - Storage Layer")
    config.addinivalue_line("markers", "epic_7: Epic 7 - Database Schema & Models")
    config.addinivalue_line("markers", "epic_8: Epic 8 - Pydantic Schemas & Validation")
    config.addinivalue_line("markers", "epic_9: Epic 9 - CRUD Service Layer")
    config.addinivalue_line("markers", "epic_10: Epic 10 - RESTful API Endpoints")
    config.addinivalue_line("markers", "epic_11: Epic 11 - Authentication & Authorization")
    config.addinivalue_line("markers", "epic_12: Epic 12 - Task Management API")
    config.addinivalue_line("markers", "epic_13: Epic 13 - Chat Shell Integration")

    # Component markers
    config.addinivalue_line("markers", "backend: Backend CRD management tests")
    config.addinivalue_line("markers", "chat_shell: Chat shell tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")


# =============================================================================
# Chat Shell Fixtures
# =============================================================================

@pytest.fixture
def agent_config():
    """Default agent configuration for testing."""
    return AgentConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=4096,
        max_iterations=5,
        system_prompt="You are a helpful test assistant.",
        tools=[],
        checkpoint_enabled=False,
        compress_context=False,
    )


@pytest.fixture
def agent_config_with_compression():
    """Agent configuration with compression enabled."""
    return AgentConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=4096,
        max_iterations=5,
        system_prompt="You are a helpful test assistant.",
        tools=[],
        checkpoint_enabled=False,
        compress_context=True,
        max_context_tokens=1000,
        compression_threshold=0.8,
        keep_recent_messages=2,
    )


# =============================================================================
# Backend Fixtures
# =============================================================================

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.database.base import Base

    # Use SQLite for unit tests
    TEST_DATABASE_URL = "sqlite:///:memory:"

    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def team(db_session):
    """Create a team kind for task relationships."""
    from backend.models.kinds import Kind, KindType

    team = Kind(
        kind=KindType.TEAM,
        name="test-team",
        namespace="default",
        spec={"bots": ["bot1"]},
    )
    db_session.add(team)
    db_session.commit()
    return team
