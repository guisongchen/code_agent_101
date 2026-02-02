"""
Unit tests for storage interfaces.
"""
import pytest
from datetime import datetime
from typing import List

from chat_shell_101.storage.interfaces import Message, HistoryStorage, StorageProvider


class TestMessage:
    """Test suite for Message dataclass."""

    def test_message_creation_with_timestamp(self) -> None:
        """Test Message creation with explicit timestamp."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        message = Message(role="user", content="Hello", timestamp=timestamp)

        assert message.role == "user"
        assert message.content == "Hello"
        assert message.timestamp == timestamp

    def test_message_creation_without_timestamp(self) -> None:
        """Test Message creation without timestamp (auto-generated)."""
        before = datetime.now()
        message = Message(role="assistant", content="Hi there!")
        after = datetime.now()

        assert message.role == "assistant"
        assert message.content == "Hi there!"
        assert before <= message.timestamp <= after

    def test_message_equality(self) -> None:
        """Test Message equality comparison."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        message1 = Message(role="user", content="Hello", timestamp=timestamp)
        message2 = Message(role="user", content="Hello", timestamp=timestamp)
        message3 = Message(role="assistant", content="Hello", timestamp=timestamp)

        assert message1 == message2
        assert message1 != message3

    def test_message_representation(self) -> None:
        """Test Message string representation."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        message = Message(role="user", content="Hello", timestamp=timestamp)

        repr_str = repr(message)
        assert "Message" in repr_str
        assert "role='user'" in repr_str
        assert "content='Hello'" in repr_str

    def test_message_serialization(self) -> None:
        """Test that Message can be converted to dict and back."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        message = Message(role="user", content="Hello", timestamp=timestamp)

        # Convert to dict
        message_dict = {
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp,
        }

        # Recreate from dict
        recreated = Message(**message_dict)

        assert recreated == message

    @pytest.mark.parametrize(
        "role, content",
        [
            ("user", "Hello"),
            ("assistant", "Hi there!"),
            ("system", "You are a helpful assistant"),
            ("", ""),  # Empty strings allowed
            ("user", "A" * 1000),  # Long content
        ]
    )
    def test_message_valid_roles_and_content(self, role: str, content: str) -> None:
        """Test Message with various valid roles and content."""
        message = Message(role=role, content=content)

        assert message.role == role
        assert message.content == content
        assert isinstance(message.timestamp, datetime)


class TestHistoryStorageInterface:
    """Test suite for HistoryStorage abstract class."""

    def test_history_storage_is_abstract(self) -> None:
        """Test that HistoryStorage cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            HistoryStorage()  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_history_storage_abstract_methods(self) -> None:
        """Test that HistoryStorage has required abstract methods."""
        abstract_methods = {
            "get_history",
            "append_messages",
            "clear_history",
        }

        for method_name in abstract_methods:
            method = getattr(HistoryStorage, method_name)
            assert hasattr(method, "__isabstractmethod__")
            assert method.__isabstractmethod__ is True

    def test_concrete_history_storage_implementation(self) -> None:
        """Test that a concrete HistoryStorage implementation works."""
        class ConcreteHistoryStorage(HistoryStorage):
            """Concrete implementation for testing."""

            def __init__(self):
                self._storage = {}

            async def get_history(self, session_id: str) -> List[Message]:
                return self._storage.get(session_id, [])

            async def append_messages(self, session_id: str, messages: List[Message]) -> None:
                if session_id not in self._storage:
                    self._storage[session_id] = []
                self._storage[session_id].extend(messages)

            async def clear_history(self, session_id: str) -> None:
                self._storage.pop(session_id, None)

        # Should be able to instantiate concrete implementation
        storage = ConcreteHistoryStorage()
        assert isinstance(storage, HistoryStorage)

        # Test the methods
        import asyncio
        asyncio.run(storage.get_history("test"))
        asyncio.run(storage.append_messages("test", []))
        asyncio.run(storage.clear_history("test"))


class TestStorageProviderInterface:
    """Test suite for StorageProvider abstract class."""

    def test_storage_provider_is_abstract(self) -> None:
        """Test that StorageProvider cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            StorageProvider()  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_storage_provider_abstract_methods(self) -> None:
        """Test that StorageProvider has required abstract methods."""
        abstract_methods = {
            "initialize",
            "close",
        }

        for method_name in abstract_methods:
            method = getattr(StorageProvider, method_name)
            assert hasattr(method, "__isabstractmethod__")
            assert method.__isabstractmethod__ is True

    def test_storage_provider_history_property(self) -> None:
        """Test that StorageProvider has abstract history property."""
        history_property = StorageProvider.history

        # Check it's a property
        assert isinstance(history_property, property)

        # Check it's abstract
        assert hasattr(history_property.fget, "__isabstractmethod__")
        assert history_property.fget.__isabstractmethod__ is True

    def test_concrete_storage_provider_implementation(self) -> None:
        """Test that a concrete StorageProvider implementation works."""
        class ConcreteHistoryStorage(HistoryStorage):
            """Concrete history storage for testing."""

            def __init__(self):
                self._storage = {}

            async def get_history(self, session_id: str) -> List[Message]:
                return self._storage.get(session_id, [])

            async def append_messages(self, session_id: str, messages: List[Message]) -> None:
                if session_id not in self._storage:
                    self._storage[session_id] = []
                self._storage[session_id].extend(messages)

            async def clear_history(self, session_id: str) -> None:
                self._storage.pop(session_id, None)

        class ConcreteStorageProvider(StorageProvider):
            """Concrete implementation for testing."""

            def __init__(self):
                self._history_storage = ConcreteHistoryStorage()

            async def initialize(self) -> None:
                pass

            async def close(self) -> None:
                pass

            @property
            def history(self) -> HistoryStorage:
                return self._history_storage

        # Should be able to instantiate concrete implementation
        provider = ConcreteStorageProvider()
        assert isinstance(provider, StorageProvider)

        # Test the methods
        import asyncio
        asyncio.run(provider.initialize())
        asyncio.run(provider.close())

        # Test history property
        history = provider.history
        assert isinstance(history, HistoryStorage)


def test_message_timestamp_serialization_roundtrip() -> None:
    """Test that Message timestamps can be serialized and deserialized."""
    from datetime import datetime
    import json

    # Create a message with timestamp
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    message = Message(role="user", content="Hello", timestamp=timestamp)

    # Convert to JSON-serializable dict
    message_dict = {
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp.isoformat(),
    }

    # Serialize to JSON
    json_str = json.dumps(message_dict)

    # Deserialize from JSON
    loaded_dict = json.loads(json_str)

    # Recreate timestamp
    loaded_timestamp = datetime.fromisoformat(loaded_dict["timestamp"])

    # Recreate message
    loaded_message = Message(
        role=loaded_dict["role"],
        content=loaded_dict["content"],
        timestamp=loaded_timestamp,
    )

    # Should be equal (within microsecond precision due to JSON serialization)
    assert loaded_message.role == message.role
    assert loaded_message.content == message.content
    # Compare timestamps with microsecond precision tolerance
    time_diff = abs((loaded_message.timestamp - message.timestamp).total_seconds())
    assert time_diff < 0.001  # Within 1 millisecond