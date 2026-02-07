"""
Tests for SQLite storage implementation.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from chat_shell.storage.sqlite_storage import SQLiteHistoryStorage, SQLiteStorage
from chat_shell.storage.interfaces import Message


@pytest.fixture
async def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
async def sqlite_storage(temp_db_path):
    """Create and initialize SQLite storage."""
    storage = SQLiteStorage(temp_db_path)
    await storage.initialize()
    yield storage
    await storage.close()


@pytest.fixture
async def sqlite_history_storage(temp_db_path):
    """Create and initialize SQLite history storage."""
    storage = SQLiteHistoryStorage(temp_db_path)
    await storage.initialize()
    yield storage


@pytest.mark.epic_4
@pytest.mark.unit
@pytest.mark.asyncio
class TestSQLiteHistoryStorage:
    """Test SQLite history storage implementation."""

    async def test_initialize_creates_tables(self, temp_db_path):
        """Test that initialization creates required tables."""
        storage = SQLiteHistoryStorage(temp_db_path)
        await storage.initialize()

        # Verify tables exist by querying schema
        conn = storage._get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        conn.close()

        assert "sessions" in tables
        assert "messages" in tables

    async def test_append_and_get_messages(self, sqlite_history_storage):
        """Test appending and retrieving messages."""
        session_id = "test-session-1"
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ]

        await sqlite_history_storage.append_messages(session_id, messages)
        retrieved = await sqlite_history_storage.get_history(session_id)

        assert len(retrieved) == 2
        assert retrieved[0].role == "user"
        assert retrieved[0].content == "Hello"
        assert retrieved[1].role == "assistant"
        assert retrieved[1].content == "Hi there!"

    async def test_get_history_empty_session(self, sqlite_history_storage):
        """Test getting history for non-existent session."""
        history = await sqlite_history_storage.get_history("non-existent")
        assert history == []

    async def test_clear_history(self, sqlite_history_storage):
        """Test clearing history for a session."""
        session_id = "test-session-clear"
        messages = [
            Message(role="user", content="Test message"),
        ]

        await sqlite_history_storage.append_messages(session_id, messages)
        await sqlite_history_storage.clear_history(session_id)

        history = await sqlite_history_storage.get_history(session_id)
        assert history == []

    async def test_multiple_sessions_isolation(self, sqlite_history_storage):
        """Test that sessions are isolated from each other."""
        session1 = "session-1"
        session2 = "session-2"

        await sqlite_history_storage.append_messages(
            session1, [Message(role="user", content="Session 1 message")]
        )
        await sqlite_history_storage.append_messages(
            session2, [Message(role="user", content="Session 2 message")]
        )

        history1 = await sqlite_history_storage.get_history(session1)
        history2 = await sqlite_history_storage.get_history(session2)

        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].content == "Session 1 message"
        assert history2[0].content == "Session 2 message"

    async def test_list_sessions(self, sqlite_history_storage):
        """Test listing all sessions."""
        # Add messages to multiple sessions
        for i in range(3):
            await sqlite_history_storage.append_messages(
                f"session-{i}",
                [Message(role="user", content=f"Message {i}")],
            )

        sessions = await sqlite_history_storage.list_sessions()

        assert len(sessions) == 3
        # Sessions should be ordered by updated_at DESC (most recent first)
        assert "session-0" in sessions
        assert "session-1" in sessions
        assert "session-2" in sessions

    async def test_system_message_support(self, sqlite_history_storage):
        """Test that system messages are stored correctly."""
        session_id = "test-system"
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello"),
        ]

        await sqlite_history_storage.append_messages(session_id, messages)
        retrieved = await sqlite_history_storage.get_history(session_id)

        assert len(retrieved) == 2
        assert retrieved[0].role == "system"
        assert retrieved[0].content == "You are a helpful assistant."


@pytest.mark.epic_4
@pytest.mark.unit
@pytest.mark.asyncio
class TestSQLiteStorage:
    """Test SQLite storage provider implementation."""

    async def test_storage_provider_interface(self, sqlite_storage):
        """Test that SQLiteStorage implements StorageProvider interface."""
        assert sqlite_storage.history is not None

    async def test_default_db_path(self):
        """Test that default database path is created."""
        storage = SQLiteStorage()
        # Should not raise when initializing with default path
        await storage.initialize()
        assert storage._history_storage is not None
        await storage.close()

    async def test_history_property_before_initialize(self, temp_db_path):
        """Test that accessing history before initialize raises error."""
        storage = SQLiteStorage(temp_db_path)

        with pytest.raises(RuntimeError, match="not initialized"):
            _ = storage.history


