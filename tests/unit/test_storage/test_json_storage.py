"""
Unit tests for JSONStorage.
"""
import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

from chat_shell_101.storage.json_storage import JSONStorage, JSONHistoryStorage
from chat_shell_101.storage.interfaces import Message


class TestJSONHistoryStorage:
    """Test suite for JSONHistoryStorage."""

    @pytest.fixture
    def temp_storage_dir(self) -> Path:
        """Create temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def json_storage(self, temp_storage_dir: Path) -> JSONHistoryStorage:
        """Create JSON history storage instance."""
        return JSONHistoryStorage(storage_path=temp_storage_dir)

    @pytest.fixture
    def sample_messages(self) -> List[Message]:
        """Create sample messages for testing."""
        return [
            Message(role="user", content="Hello", timestamp=datetime(2024, 1, 1, 12, 0, 0)),
            Message(role="assistant", content="Hi there!", timestamp=datetime(2024, 1, 1, 12, 0, 1)),
            Message(role="user", content="How are you?", timestamp=datetime(2024, 1, 1, 12, 0, 2)),
        ]

    @pytest.mark.asyncio
    async def test_storage_directory_creation(self, temp_storage_dir: Path) -> None:
        """Test that storage directory is created on initialization."""
        # Directory should not exist initially
        sessions_dir = temp_storage_dir / "sessions"
        assert not sessions_dir.exists()

        # Create storage instance
        storage = JSONHistoryStorage(storage_path=temp_storage_dir)

        # Directory should be created
        assert sessions_dir.exists()
        assert sessions_dir.is_dir()

    @pytest.mark.asyncio
    async def test_get_history_empty_session(
        self, json_storage: JSONHistoryStorage
    ) -> None:
        """Test getting history for empty session returns empty list."""
        history = await json_storage.get_history("non-existent-session")
        assert history == []

    @pytest.mark.asyncio
    async def test_append_and_get_history(
        self, json_storage: JSONHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test appending messages and retrieving history."""
        session_id = "test-session"

        # Append messages
        await json_storage.append_messages(session_id, sample_messages)

        # Get history
        history = await json_storage.get_history(session_id)

        assert len(history) == len(sample_messages)
        # Compare message content (timestamps might have microsecond differences)
        for stored_msg, original_msg in zip(history, sample_messages):
            assert stored_msg.role == original_msg.role
            assert stored_msg.content == original_msg.content
            # Timestamps should be close (within 1 second due to serialization)
            time_diff = abs((stored_msg.timestamp - original_msg.timestamp).total_seconds())
            assert time_diff < 1.0

    @pytest.mark.asyncio
    async def test_append_multiple_times(
        self, json_storage: JSONHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test appending messages multiple times to same session."""
        session_id = "test-session"
        additional_messages = [
            Message(role="assistant", content="I'm good!", timestamp=datetime(2024, 1, 1, 12, 0, 3)),
            Message(role="user", content="Great!", timestamp=datetime(2024, 1, 1, 12, 0, 4)),
        ]

        # Append first batch
        await json_storage.append_messages(session_id, sample_messages)

        # Append second batch
        await json_storage.append_messages(session_id, additional_messages)

        # Get history
        history = await json_storage.get_history(session_id)

        assert len(history) == len(sample_messages) + len(additional_messages)
        all_messages = sample_messages + additional_messages

        for stored_msg, original_msg in zip(history, all_messages):
            assert stored_msg.role == original_msg.role
            assert stored_msg.content == original_msg.content

    @pytest.mark.asyncio
    async def test_session_isolation(
        self, json_storage: JSONHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test that sessions are isolated from each other."""
        session1_id = "session-1"
        session2_id = "session-2"

        # Append messages to session 1
        await json_storage.append_messages(session1_id, sample_messages)

        # Session 2 should be empty
        session2_history = await json_storage.get_history(session2_id)
        assert session2_history == []

        # Session 1 should have messages
        session1_history = await json_storage.get_history(session1_id)
        assert len(session1_history) == len(sample_messages)

    @pytest.mark.asyncio
    async def test_clear_history(
        self, json_storage: JSONHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test clearing history for a session."""
        session_id = "test-session"

        # Append messages
        await json_storage.append_messages(session_id, sample_messages)

        # Verify file exists
        session_file = json_storage._get_session_file(session_id)
        assert session_file.exists()

        # Clear history
        await json_storage.clear_history(session_id)

        # Verify file is deleted
        assert not session_file.exists()

        # Verify history is empty
        history_after_clear = await json_storage.get_history(session_id)
        assert history_after_clear == []

    @pytest.mark.asyncio
    async def test_clear_nonexistent_session(self, json_storage: JSONHistoryStorage) -> None:
        """Test clearing history for non-existent session (should not error)."""
        session_id = "non-existent-session"

        # Should not raise any error
        await json_storage.clear_history(session_id)

    @pytest.mark.asyncio
    async def test_empty_messages_list(self, json_storage: JSONHistoryStorage) -> None:
        """Test appending empty messages list."""
        session_id = "test-session"

        # Append empty list
        await json_storage.append_messages(session_id, [])

        # Get history
        history = await json_storage.get_history(session_id)

        assert history == []

    @pytest.mark.asyncio
    async def test_large_number_of_messages(
        self, json_storage: JSONHistoryStorage
    ) -> None:
        """Test handling large number of messages."""
        session_id = "large-session"
        num_messages = 100

        # Create many messages
        messages = [
            Message(role="user", content=f"Message {i}", timestamp=datetime(2024, 1, 1, 12, 0, i))
            for i in range(num_messages)
        ]

        # Append all messages
        await json_storage.append_messages(session_id, messages)

        # Get history
        history = await json_storage.get_history(session_id)

        assert len(history) == num_messages
        for i, msg in enumerate(history):
            assert msg.content == f"Message {i}"

    @pytest.mark.asyncio
    async def test_corrupt_json_file_handling(
        self, json_storage: JSONHistoryStorage, temp_storage_dir: Path
    ) -> None:
        """Test handling of corrupt JSON files."""
        session_id = "corrupt-session"
        session_file = json_storage._get_session_file(session_id)

        # Write corrupt JSON
        session_file.write_text("{invalid json")

        # Should return empty list without raising exception
        history = await json_storage.get_history(session_id)
        assert history == []

    @pytest.mark.asyncio
    async def test_missing_timestamp_handling(
        self, json_storage: JSONHistoryStorage, temp_storage_dir: Path
    ) -> None:
        """Test handling of messages without timestamps."""
        session_id = "no-timestamp-session"
        session_file = json_storage._get_session_file(session_id)

        # Create JSON without timestamps
        data = {
            "session_id": session_id,
            "updated_at": datetime.now().isoformat(),
            "messages": [
                {"role": "user", "content": "Hello"},  # No timestamp
                {"role": "assistant", "content": "Hi"},  # No timestamp
            ]
        }

        session_file.write_text(json.dumps(data, indent=2))

        # Should load messages with None timestamps
        history = await json_storage.get_history(session_id)

        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[0].timestamp is None
        assert history[1].role == "assistant"
        assert history[1].content == "Hi"
        assert history[1].timestamp is None

    @pytest.mark.asyncio
    async def test_file_permission_error_handling(
        self, json_storage: JSONHistoryStorage, temp_storage_dir: Path
    ) -> None:
        """Test handling of file permission errors."""
        session_id = "permission-error-session"
        session_file = json_storage._get_session_file(session_id)

        # Mock read_text to raise IOError
        with patch.object(session_file, 'read_text', side_effect=IOError("Permission denied")):
            # Should return empty list without raising exception
            history = await json_storage.get_history(session_id)
            assert history == []

    @pytest.mark.asyncio
    async def test_write_permission_error_handling(
        self, json_storage: JSONHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test handling of write permission errors."""
        session_id = "write-error-session"
        session_file = json_storage._get_session_file(session_id)

        # Mock write_text to raise IOError
        with patch.object(session_file, 'write_text', side_effect=IOError("Permission denied")):
            # Should not raise exception
            await json_storage.append_messages(session_id, sample_messages)

    @pytest.mark.asyncio
    async def test_delete_permission_error_handling(
        self, json_storage: JSONHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test handling of delete permission errors."""
        session_id = "delete-error-session"

        # First create a session
        await json_storage.append_messages(session_id, sample_messages)

        session_file = json_storage._get_session_file(session_id)
        assert session_file.exists()

        # Mock unlink to raise IOError
        with patch.object(session_file, 'unlink', side_effect=IOError("Permission denied")):
            # Should not raise exception
            await json_storage.clear_history(session_id)

    @pytest.mark.asyncio
    async def test_json_serialization_format(
        self, json_storage: JSONHistoryStorage, sample_messages: List[Message]
    ) -> None:
        """Test that JSON serialization format is correct."""
        session_id = "format-test-session"

        # Append messages
        await json_storage.append_messages(session_id, sample_messages)

        # Read raw JSON file
        session_file = json_storage._get_session_file(session_id)
        raw_content = session_file.read_text()
        data = json.loads(raw_content)

        # Check structure
        assert "session_id" in data
        assert "updated_at" in data
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == len(sample_messages)

        # Check message format
        for i, msg_data in enumerate(data["messages"]):
            assert "role" in msg_data
            assert "content" in msg_data
            assert "timestamp" in msg_data
            assert msg_data["role"] == sample_messages[i].role
            assert msg_data["content"] == sample_messages[i].content
            # Timestamp should be ISO format string
            assert isinstance(msg_data["timestamp"], str)

    @pytest.mark.asyncio
    async def test_message_with_none_timestamp(
        self, json_storage: JSONHistoryStorage
    ) -> None:
        """Test handling of messages with None timestamp."""
        session_id = "none-timestamp-session"
        messages = [
            Message(role="user", content="Hello", timestamp=None),
        ]

        # Append message with None timestamp
        await json_storage.append_messages(session_id, messages)

        # Get history
        history = await json_storage.get_history(session_id)

        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[0].timestamp is None


class TestJSONStorage:
    """Test suite for JSONStorage provider."""

    @pytest.fixture
    def temp_storage_dir(self) -> Path:
        """Create temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def json_storage_provider(self, temp_storage_dir: Path) -> JSONStorage:
        """Create JSON storage provider instance."""
        return JSONStorage(storage_path=temp_storage_dir)

    @pytest.mark.asyncio
    async def test_initialize_creates_directory(
        self, json_storage_provider: JSONStorage, temp_storage_dir: Path
    ) -> None:
        """Test initialize creates storage directory."""
        # Directory might not exist yet
        if temp_storage_dir.exists():
            import shutil
            shutil.rmtree(temp_storage_dir)

        assert not temp_storage_dir.exists()

        # Initialize
        await json_storage_provider.initialize()

        # Directory should be created
        assert temp_storage_dir.exists()
        assert temp_storage_dir.is_dir()

    @pytest.mark.asyncio
    async def test_initialize_existing_directory(
        self, json_storage_provider: JSONStorage, temp_storage_dir: Path
    ) -> None:
        """Test initialize with existing directory."""
        # Create directory first
        temp_storage_dir.mkdir(parents=True, exist_ok=True)
        assert temp_storage_dir.exists()

        # Initialize should not error
        await json_storage_provider.initialize()

    @pytest.mark.asyncio
    async def test_close(self, json_storage_provider: JSONStorage) -> None:
        """Test close method (should do nothing but not error)."""
        # Should not raise any error
        await json_storage_provider.close()

    @pytest.mark.asyncio
    async def test_history_property_before_initialize(
        self, json_storage_provider: JSONStorage
    ) -> None:
        """Test history property raises error if not initialized."""
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = json_storage_provider.history

    @pytest.mark.asyncio
    async def test_history_property_after_initialize(
        self, json_storage_provider: JSONStorage
    ) -> None:
        """Test history property returns HistoryStorage after initialization."""
        await json_storage_provider.initialize()
        history_storage = json_storage_provider.history

        assert isinstance(history_storage, JSONHistoryStorage)
        assert hasattr(history_storage, "get_history")
        assert hasattr(history_storage, "append_messages")
        assert hasattr(history_storage, "clear_history")

    @pytest.mark.asyncio
    async def test_integration_with_history_storage(
        self, json_storage_provider: JSONStorage, sample_messages: List[Message]
    ) -> None:
        """Test integration between JSONStorage and its HistoryStorage."""
        session_id = "test-session"

        # Initialize first
        await json_storage_provider.initialize()

        # Get history storage
        history_storage = json_storage_provider.history

        # Use history storage methods
        await history_storage.append_messages(session_id, sample_messages)
        history = await history_storage.get_history(session_id)

        assert len(history) == len(sample_messages)

        # Clear history
        await history_storage.clear_history(session_id)
        history_after_clear = await history_storage.get_history(session_id)

        assert history_after_clear == []

    @pytest.mark.asyncio
    async def test_default_storage_path(self) -> None:
        """Test default storage path from config."""
        from chat_shell_101.config import config as app_config

        # Mock config.get_storage_path
        with patch('chat_shell_101.storage.json_storage.config') as mock_config:
            mock_storage_path = Path("/mock/storage/path")
            mock_config.get_storage_path.return_value = mock_storage_path

            # Create storage without explicit path
            storage = JSONStorage()

            assert storage.storage_path == mock_storage_path
            mock_config.get_storage_path.assert_called_once()

    @pytest.mark.asyncio
    async def test_custom_storage_path(self) -> None:
        """Test custom storage path override."""
        custom_path = Path("/custom/storage/path")

        # Create storage with custom path
        storage = JSONStorage(storage_path=custom_path)

        assert storage.storage_path == custom_path

    @pytest.mark.asyncio
    async def test_multiple_instances_isolation(
        self, temp_storage_dir: Path, sample_messages: List[Message]
    ) -> None:
        """Test that multiple JSONStorage instances share same directory."""
        storage1 = JSONStorage(storage_path=temp_storage_dir)
        storage2 = JSONStorage(storage_path=temp_storage_dir)

        await storage1.initialize()
        await storage2.initialize()

        session_id = "shared-session"

        # Append to storage1
        await storage1.history.append_messages(session_id, sample_messages)

        # Storage2 should see the same messages (same directory)
        history2 = await storage2.history.get_history(session_id)
        assert len(history2) == len(sample_messages)

        # Clear from storage2
        await storage2.history.clear_history(session_id)

        # Storage1 should see empty history
        history1 = await storage1.history.get_history(session_id)
        assert history1 == []