"""Tests for MessageService.

Tests: 8 tests covering message storage functionality
- Message creation
- User/assistant/tool message creation
- History retrieval
- Pagination

Epic 15: Message History Management
"""

import pytest
import pytest_asyncio
from uuid import UUID, uuid4

from backend.models.messages import MessageRole, MessageType
from backend.schemas.message import MessageCreateRequest, MessageHistoryRequest
from backend.services.message import MessageService

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_15,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_15
@pytest.mark.unit
@pytest.mark.backend
class TestMessageService:
    """Test suite for MessageService - 8 tests."""

    async def test_create_message(self, async_session):
        """Test creating a basic message."""
        service = MessageService(async_session)
        task_id = uuid4()

        request = MessageCreateRequest(
            task_id=task_id,
            role=MessageRole.USER,
            content="Hello, world!",
            thread_id="test-thread",
        )

        message = await service.create(request)
        await async_session.commit()

        assert message.task_id == task_id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.thread_id == "test-thread"
        assert message.sequence == 0
        assert message.message_type == MessageType.TEXT

    async def test_create_user_message(self, async_session):
        """Test creating a user message with convenience method."""
        service = MessageService(async_session)
        task_id = uuid4()

        message = await service.create_user_message(
            task_id=task_id,
            content="User message",
            thread_id="test-thread",
            metadata={"user_id": 1},
        )
        await async_session.commit()

        assert message.role == MessageRole.USER
        assert message.content == "User message"
        assert message.meta == {"user_id": 1}

    async def test_create_assistant_message(self, async_session):
        """Test creating an assistant message with convenience method."""
        service = MessageService(async_session)
        task_id = uuid4()

        message = await service.create_assistant_message(
            task_id=task_id,
            content="Assistant response",
            thread_id="test-thread",
            model="gpt-4",
            tokens_used=100,
            prompt_tokens=50,
            completion_tokens=50,
            metadata={"tool_calls": []},
        )
        await async_session.commit()

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Assistant response"
        assert message.model == "gpt-4"
        assert message.tokens_used == 100
        assert message.prompt_tokens == 50
        assert message.completion_tokens == 50

    async def test_create_tool_message(self, async_session):
        """Test creating a tool message with convenience method."""
        service = MessageService(async_session)
        task_id = uuid4()

        message = await service.create_tool_message(
            task_id=task_id,
            content="Tool result",
            tool_name="web_search",
            tool_call_id="call_123",
            message_type=MessageType.TOOL_RESULT,
            thread_id="test-thread",
        )
        await async_session.commit()

        assert message.role == MessageRole.TOOL
        assert message.content == "Tool result"
        assert message.tool_name == "web_search"
        assert message.tool_call_id == "call_123"
        assert message.message_type == MessageType.TOOL_RESULT

    async def test_get_message(self, async_session):
        """Test retrieving a message by ID."""
        service = MessageService(async_session)
        task_id = uuid4()

        created = await service.create_user_message(
            task_id=task_id,
            content="Test message",
        )
        await async_session.commit()

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == "Test message"

    async def test_get_message_not_found(self, async_session):
        """Test retrieving a non-existent message."""
        service = MessageService(async_session)

        result = await service.get(uuid4())

        assert result is None

    async def test_sequence_auto_increment(self, async_session):
        """Test that sequence numbers auto-increment within a thread."""
        service = MessageService(async_session)
        task_id = uuid4()
        thread_id = "test-thread"

        msg1 = await service.create_user_message(
            task_id=task_id,
            content="Message 1",
            thread_id=thread_id,
        )
        msg2 = await service.create_user_message(
            task_id=task_id,
            content="Message 2",
            thread_id=thread_id,
        )
        msg3 = await service.create_assistant_message(
            task_id=task_id,
            content="Message 3",
            thread_id=thread_id,
        )
        await async_session.commit()

        assert msg1.sequence == 0
        assert msg2.sequence == 1
        assert msg3.sequence == 2

    async def test_sequence_per_thread(self, async_session):
        """Test that sequence numbers are per-thread."""
        service = MessageService(async_session)
        task_id = uuid4()

        msg1 = await service.create_user_message(
            task_id=task_id,
            content="Thread A message",
            thread_id="thread-a",
        )
        msg2 = await service.create_user_message(
            task_id=task_id,
            content="Thread B message",
            thread_id="thread-b",
        )
        msg3 = await service.create_user_message(
            task_id=task_id,
            content="Thread A message 2",
            thread_id="thread-a",
        )
        await async_session.commit()

        assert msg1.sequence == 0
        assert msg2.sequence == 0  # New thread starts at 0
        assert msg3.sequence == 1  # Continues thread A


@pytest.mark.epic_15
@pytest.mark.unit
@pytest.mark.backend
class TestMessageHistory:
    """Test suite for message history retrieval - 6 tests."""

    async def test_get_history_basic(self, async_session):
        """Test basic history retrieval."""
        service = MessageService(async_session)
        task_id = uuid4()

        await service.create_user_message(task_id=task_id, content="User 1")
        await service.create_assistant_message(task_id=task_id, content="Assistant 1")
        await service.create_user_message(task_id=task_id, content="User 2")
        await async_session.commit()

        history = await service.get_history(task_id)

        assert history.total == 3
        assert len(history.messages) == 3
        assert history.has_more is False

    async def test_get_history_pagination(self, async_session):
        """Test history pagination."""
        service = MessageService(async_session)
        task_id = uuid4()

        # Create 5 messages
        for i in range(5):
            await service.create_user_message(task_id=task_id, content=f"Message {i}")
        await async_session.commit()

        # Get first 2
        request = MessageHistoryRequest(limit=2, offset=0)
        history = await service.get_history(task_id, request)

        assert history.total == 5
        assert len(history.messages) == 2
        assert history.has_more is True
        assert history.messages[0].content == "Message 0"
        assert history.messages[1].content == "Message 1"

        # Get next 2
        request = MessageHistoryRequest(limit=2, offset=2)
        history = await service.get_history(task_id, request)

        assert len(history.messages) == 2
        assert history.has_more is True
        assert history.messages[0].content == "Message 2"
        assert history.messages[1].content == "Message 3"

        # Get last page
        request = MessageHistoryRequest(limit=2, offset=4)
        history = await service.get_history(task_id, request)

        assert len(history.messages) == 1
        assert history.has_more is False
        assert history.messages[0].content == "Message 4"

    async def test_get_history_by_thread(self, async_session):
        """Test filtering history by thread."""
        service = MessageService(async_session)
        task_id = uuid4()

        await service.create_user_message(task_id=task_id, content="Thread A", thread_id="thread-a")
        await service.create_user_message(task_id=task_id, content="Thread B", thread_id="thread-b")
        await service.create_user_message(task_id=task_id, content="Thread A 2", thread_id="thread-a")
        await async_session.commit()

        # Get all messages for thread-a
        request = MessageHistoryRequest(thread_id="thread-a")
        history = await service.get_history(task_id, request)

        assert history.total == 2
        assert len(history.messages) == 2
        assert history.messages[0].content == "Thread A"
        assert history.messages[1].content == "Thread A 2"

    async def test_get_thread_messages(self, async_session):
        """Test getting all messages for a thread."""
        service = MessageService(async_session)
        task_id = uuid4()

        await service.create_user_message(task_id=task_id, content="User 1", thread_id="thread-1")
        await service.create_assistant_message(task_id=task_id, content="Assistant 1", thread_id="thread-1")
        await service.create_user_message(task_id=task_id, content="User 2", thread_id="thread-2")
        await async_session.commit()

        messages = await service.get_thread_messages(task_id, thread_id="thread-1")

        assert len(messages) == 2
        assert messages[0].content == "User 1"
        assert messages[1].content == "Assistant 1"

    async def test_get_latest_messages(self, async_session):
        """Test getting latest messages."""
        service = MessageService(async_session)
        task_id = uuid4()

        for i in range(10):
            await service.create_user_message(task_id=task_id, content=f"Message {i}")
        await async_session.commit()

        # Get latest 3
        messages = await service.get_latest_messages(task_id, count=3)

        assert len(messages) == 3
        # Should be ordered oldest first within the last 3
        assert messages[0].content == "Message 7"
        assert messages[1].content == "Message 8"
        assert messages[2].content == "Message 9"

    async def test_count_messages(self, async_session):
        """Test counting messages."""
        service = MessageService(async_session)
        task_id = uuid4()

        await service.create_user_message(task_id=task_id, content="A", thread_id="t1")
        await service.create_user_message(task_id=task_id, content="B", thread_id="t1")
        await service.create_user_message(task_id=task_id, content="C", thread_id="t2")
        await async_session.commit()

        # Count all messages for task
        total = await service.count_messages(task_id)
        assert total == 3

        # Count messages for specific thread
        t1_count = await service.count_messages(task_id, thread_id="t1")
        assert t1_count == 2

        t2_count = await service.count_messages(task_id, thread_id="t2")
        assert t2_count == 1


@pytest.mark.epic_15
@pytest.mark.unit
@pytest.mark.backend
class TestMessageDeletion:
    """Test suite for message deletion - 4 tests."""

    async def test_delete_task_messages(self, async_session):
        """Test deleting all messages for a task."""
        service = MessageService(async_session)
        task_id = uuid4()

        await service.create_user_message(task_id=task_id, content="Message 1")
        await service.create_user_message(task_id=task_id, content="Message 2")
        await async_session.commit()

        deleted_count = await service.delete_task_messages(task_id)
        await async_session.commit()

        assert deleted_count == 2

        # Verify messages are deleted
        count = await service.count_messages(task_id)
        assert count == 0

    async def test_delete_thread_messages(self, async_session):
        """Test deleting messages for a specific thread."""
        service = MessageService(async_session)
        task_id = uuid4()

        await service.create_user_message(task_id=task_id, content="A", thread_id="t1")
        await service.create_user_message(task_id=task_id, content="B", thread_id="t1")
        await service.create_user_message(task_id=task_id, content="C", thread_id="t2")
        await async_session.commit()

        deleted_count = await service.delete_thread_messages(task_id, "t1")
        await async_session.commit()

        assert deleted_count == 2

        # Verify only t1 messages deleted
        t1_count = await service.count_messages(task_id, thread_id="t1")
        assert t1_count == 0

        t2_count = await service.count_messages(task_id, thread_id="t2")
        assert t2_count == 1

    async def test_delete_task_messages_empty(self, async_session):
        """Test deleting messages for task with no messages."""
        service = MessageService(async_session)
        task_id = uuid4()

        deleted_count = await service.delete_task_messages(task_id)

        assert deleted_count == 0

    async def test_delete_thread_messages_empty(self, async_session):
        """Test deleting messages for non-existent thread."""
        service = MessageService(async_session)
        task_id = uuid4()

        deleted_count = await service.delete_thread_messages(task_id, "non-existent")

        assert deleted_count == 0
