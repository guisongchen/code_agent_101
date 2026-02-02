"""
Unit tests for MemoryStorage.
"""
import pytest
from datetime import datetime
from typing import List

from chat_shell_101.storage.memory_storage import MemoryStorage, MemoryHistoryStorage
from chat_shell_101.storage.interfaces import Message


class TestMemoryHistoryStorage:
    """Test suite for MemoryHistoryStorage."""

    @pytest.fixture
    def storage(self) -> MemoryHistoryStorage:
        """Create memory history storage instance."""
        return MemoryHistoryStorage()

    @pytest.fixture
    def sample_messages(self) -> List[Message]:
        """Create sample messages for testing."""
        return [
            Message(role="user", content="Hello", timestamp=datetime(2024, 1, 1, 12, 0, 0)),
            Message(role="assistant", content="Hi there!", timestamp=datetime(2024, 1, 1, 12, 0, 1)),
            Message(role="user", content="How are you?", timestamp=datetime(2024, 1, 1, 12, 0, 2)),
        ]

    @pytest.mark.asyncio
    async def test_get_history_empty_session(self, storage: MemoryHistoryStorage) -> None:
        """Test getting history for empty session returns empty list."""
        history = await storage.get_history("session-1")
        assert history == []

    @pytest.mark.asyncio
    async def test_append_and_get_history(
        self, storage: MemoryHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test appending messages and retrieving history."""
        session_id = "test-session"

        # Append messages
        await storage.append_messages(session_id, sample_messages)

        # Get history
        history = await storage.get_history(session_id)

        assert len(history) == len(sample_messages)
        assert history == sample_messages

    @pytest.mark.asyncio
    async def test_append_multiple_times(
        self, storage: MemoryHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test appending messages multiple times to same session."""
        session_id = "test-session"
        additional_messages = [
            Message(role="assistant", content="I'm good!", timestamp=datetime(2024, 1, 1, 12, 0, 3)),
            Message(role="user", content="Great!", timestamp=datetime(2024, 1, 1, 12, 0, 4)),
        ]

        # Append first batch
        await storage.append_messages(session_id, sample_messages)

        # Append second batch
        await storage.append_messages(session_id, additional_messages)

        # Get history
        history = await storage.get_history(session_id)

        assert len(history) == len(sample_messages) + len(additional_messages)
        assert history == sample_messages + additional_messages

    @pytest.mark.asyncio
    async def test_session_isolation(
        self, storage: MemoryHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test that sessions are isolated from each other."""
        session1_id = "session-1"
        session2_id = "session-2"

        # Append messages to session 1
        await storage.append_messages(session1_id, sample_messages)

        # Session 2 should be empty
        session2_history = await storage.get_history(session2_id)
        assert session2_history == []

        # Session 1 should have messages
        session1_history = await storage.get_history(session1_id)
        assert session1_history == sample_messages

    @pytest.mark.asyncio
    async def test_clear_history(
        self, storage: MemoryHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test clearing history for a session."""
        session_id = "test-session"

        # Append messages
        await storage.append_messages(session_id, sample_messages)

        # Verify messages are there
        history = await storage.get_history(session_id)
        assert len(history) == len(sample_messages)

        # Clear history
        await storage.clear_history(session_id)

        # Verify history is empty
        history_after_clear = await storage.get_history(session_id)
        assert history_after_clear == []

    @pytest.mark.asyncio
    async def test_clear_nonexistent_session(self, storage: MemoryHistoryStorage) -> None:
        """Test clearing history for non-existent session (should not error)."""
        session_id = "non-existent-session"

        # Should not raise any error
        await storage.clear_history(session_id)

        # Verify session doesn't exist
        history = await storage.get_history(session_id)
        assert history == []

    @pytest.mark.asyncio
    async def test_empty_messages_list(self, storage: MemoryHistoryStorage) -> None:
        """Test appending empty messages list."""
        session_id = "test-session"

        # Append empty list
        await storage.append_messages(session_id, [])

        # Get history
        history = await storage.get_history(session_id)

        assert history == []

    @pytest.mark.asyncio
    async def test_large_number_of_messages(self, storage: MemoryHistoryStorage) -> None:
        """Test handling large number of messages."""
        session_id = "large-session"
        num_messages = 1000

        # Create many messages
        messages = [
            Message(role="user", content=f"Message {i}", timestamp=datetime(2024, 1, 1, 12, 0, i))
            for i in range(num_messages)
        ]

        # Append all messages
        await storage.append_messages(session_id, messages)

        # Get history
        history = await storage.get_history(session_id)

        assert len(history) == num_messages
        assert history == messages

    @pytest.mark.asyncio
    async def test_message_immutability(
        self, storage: MemoryHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test that stored messages are not modified after storage."""
        session_id = "test-session"

        # Append messages
        await storage.append_messages(session_id, sample_messages)

        # Modify original list (should not affect stored messages)
        sample_messages.append(Message(role="system", content="Modified", timestamp=datetime.now()))

        # Get history
        history = await storage.get_history(session_id)

        # Should still have original 3 messages, not 4
        assert len(history) == 3
        assert history == sample_messages[:3]  # Original 3 messages

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(
        self, storage: MemoryHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test operations on multiple concurrent sessions."""
        sessions = [f"session-{i}" for i in range(5)]

        # Append different messages to each session
        for i, session_id in enumerate(sessions):
            session_messages = [
                Message(role="user", content=f"Message from session {i}", timestamp=datetime(2024, 1, 1, 12, 0, i))
            ]
            await storage.append_messages(session_id, session_messages)

        # Verify each session has its own messages
        for i, session_id in enumerate(sessions):
            history = await storage.get_history(session_id)
            assert len(history) == 1
            assert history[0].content == f"Message from session {i}"

        # Clear one session
        await storage.clear_history(sessions[2])

        # Verify cleared session is empty, others still have messages
        for i, session_id in enumerate(sessions):
            history = await storage.get_history(session_id)
            if i == 2:
                assert history == []
            else:
                assert len(history) == 1


class TestMemoryStorage:
    """Test suite for MemoryStorage provider."""

    @pytest.fixture
    def memory_storage(self) -> MemoryStorage:
        """Create memory storage instance."""
        return MemoryStorage()

    @pytest.mark.asyncio
    async def test_initialize(self, memory_storage: MemoryStorage) -> None:
        """Test initialize method (should do nothing but not error)."""
        # Should not raise any error
        await memory_storage.initialize()

    @pytest.mark.asyncio
    async def test_close(self, memory_storage: MemoryStorage) -> None:
        """Test close method (should do nothing but not error)."""
        # Should not raise any error
        await memory_storage.close()

    def test_history_property(self, memory_storage: MemoryStorage) -> None:
        """Test history property returns HistoryStorage instance."""
        history_storage = memory_storage.history

        assert isinstance(history_storage, MemoryHistoryStorage)
        assert hasattr(history_storage, "get_history")
        assert hasattr(history_storage, "append_messages")
        assert hasattr(history_storage, "clear_history")

    @pytest.mark.asyncio
    async def test_integration_with_history_storage(
        self, memory_storage: MemoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test integration between MemoryStorage and its HistoryStorage."""
        session_id = "test-session"

        # Get history storage
        history_storage = memory_storage.history

        # Use history storage methods
        await history_storage.append_messages(session_id, sample_messages)
        history = await history_storage.get_history(session_id)

        assert history == sample_messages

        # Clear history
        await history_storage.clear_history(session_id)
        history_after_clear = await history_storage.get_history(session_id)

        assert history_after_clear == []

    @pytest.mark.asyncio
    async def test_multiple_instances_isolation(self) -> None:
        """Test that multiple MemoryStorage instances are isolated."""
        storage1 = MemoryStorage()
        storage2 = MemoryStorage()

        session_id = "shared-session"
        messages1 = [Message(role="user", content="From storage1", timestamp=datetime.now())]
        messages2 = [Message(role="user", content="From storage2", timestamp=datetime.now())]

        # Append to storage1
        await storage1.history.append_messages(session_id, messages1)

        # Storage2 should not see storage1's messages
        history2 = await storage2.history.get_history(session_id)
        assert history2 == []

        # Append to storage2
        await storage2.history.append_messages(session_id, messages2)

        # Each storage should see only its own messages
        history1 = await storage1.history.get_history(session_id)
        history2 = await storage2.history.get_history(session_id)

        assert history1 == messages1
        assert history2 == messages2

    @pytest.mark.asyncio
    async def test_storage_persistence_within_process(self) -> None:
        """Test that storage persists within same instance lifecycle."""
        storage = MemoryStorage()
        session_id = "persistent-session"
        messages = [Message(role="user", content="Persistent message", timestamp=datetime.now())]

        # Append messages
        await storage.history.append_messages(session_id, messages)

        # Get history multiple times - should persist
        for _ in range(3):
            history = await storage.history.get_history(session_id)
            assert history == messages

        # Clear and verify
        await storage.history.clear_history(session_id)
        history = await storage.history.get_history(session_id)
        assert history == []