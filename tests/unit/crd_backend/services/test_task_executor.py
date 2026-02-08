"""Tests for TaskExecutor and TaskQueue.

Tests: 18 tests covering task execution and queue management
- Task execution flow
- Error handling and retry
- Bot name extraction
- Event broadcasting
- Queue management

Epic 18: Chat Execution Engine Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from backend.models.tasks import TaskStatus
from backend.schemas.task import TaskResponse
from backend.services.task_executor import (
    TaskExecutionError,
    TaskExecutor,
    TaskQueue,
    get_task_queue,
)

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_18,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_18
@pytest.mark.unit
@pytest.mark.backend
class TestTaskExecutor:
    """Test suite for TaskExecutor - 12 tests."""

    async def test_task_executor_initialization(self, async_session):
        """Test task executor initializes correctly."""
        executor = TaskExecutor(async_session)

        assert executor.session == async_session
        assert executor.MAX_RETRIES == 3
        assert executor.RETRY_DELAY == 1.0

    async def test_extract_bot_name_from_spec(self, async_session):
        """Test extracting bot name from task spec."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.spec = {"bot_name": "my-bot"}

        bot_name = executor._extract_bot_name(task)
        assert bot_name == "my-bot"

    async def test_extract_bot_name_from_botref(self, async_session):
        """Test extracting bot name from botRef."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.spec = {"botRef": {"name": "ref-bot"}}

        bot_name = executor._extract_bot_name(task)
        assert bot_name == "ref-bot"

    async def test_extract_bot_name_default(self, async_session):
        """Test default bot name when not specified."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.spec = {}

        bot_name = executor._extract_bot_name(task)
        assert bot_name == "default"

    async def test_extract_user_id_from_created_by(self, async_session):
        """Test extracting user ID from created_by."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.created_by = "123"

        user_id = executor._extract_user_id(task)
        assert user_id == 123

    async def test_extract_user_id_invalid(self, async_session):
        """Test extracting user ID with invalid value."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.created_by = "not-a-number"

        user_id = executor._extract_user_id(task)
        assert user_id is None

    async def test_execute_task_not_found(self, async_session):
        """Test executing non-existent task raises error."""
        executor = TaskExecutor(async_session)

        with patch.object(executor.task_service, "get", return_value=None):
            with pytest.raises(TaskExecutionError, match="not found"):
                await executor.execute_task(uuid4())

    async def test_execute_task_invalid_bot_config(self, async_session):
        """Test executing with invalid bot config raises error."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.spec = {"bot_name": "test-bot"}
        task.input = "Hello"

        with patch.object(executor.task_service, "get", return_value=task):
            with patch.object(
                executor.chat_service,
                "validate_bot_configuration",
                return_value={"valid": False, "errors": ["Bot not found"]},
            ):
                with pytest.raises(TaskExecutionError, match="Invalid bot"):
                    await executor.execute_task(uuid4())

    async def test_execute_task_stores_user_message(self, async_session):
        """Test execution stores user input as message."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.id = uuid4()
        task.spec = {"bot_name": "test-bot"}
        task.input = "Hello AI"
        task.created_by = None

        with patch.object(executor.task_service, "get", return_value=task):
            with patch.object(
                executor.chat_service,
                "validate_bot_configuration",
                return_value={"valid": True},
            ):
                with patch.object(executor.task_service, "start", return_value=task):
                    with patch.object(
                        executor.message_service,
                        "create_user_message",
                        return_value=MagicMock(),
                    ) as mock_create_msg:
                        # Mock chat execution to succeed
                        async def mock_execute_chat(*args, **kwargs):
                            yield {"type": "content", "data": {"text": "Response"}}

                        with patch.object(
                            executor.chat_service,
                            "execute_chat",
                            side_effect=mock_execute_chat,
                        ):
                            with patch.object(
                                executor.message_service,
                                "create_assistant_message",
                                return_value=MagicMock(),
                            ):
                                with patch.object(
                                    executor.task_service,
                                    "complete",
                                    return_value=task,
                                ):
                                    with patch.object(
                                        executor,
                                        "_broadcast_task_completed",
                                        return_value=None,
                                    ):
                                        await executor.execute_task(task.id)

                                        # Verify user message was stored
                                        assert mock_create_msg.call_count == 1
                                        call_args = mock_create_msg.call_args[1]
                                        assert call_args["content"] == "Hello AI"
                                        assert call_args["task_id"] == task.id

    async def test_broadcast_task_started(self, async_session):
        """Test broadcasting task started event."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.id = uuid4()
        task.name = "test-task"
        task.namespace = "default"
        task.status = TaskStatus.RUNNING
        task.created_by = "123"

        with patch.object(
            executor.event_broadcaster,
            "broadcast_task_started",
            return_value=1,
        ) as mock_broadcast:
            await executor._broadcast_task_started(task)

            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[1]
            assert call_args["task_id"] == task.id
            assert call_args["task_data"]["name"] == "test-task"
            assert call_args["user_id"] == 123

    async def test_broadcast_task_completed(self, async_session):
        """Test broadcasting task completed event."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.id = uuid4()
        task.name = "test-task"
        task.namespace = "default"
        task.status = TaskStatus.COMPLETED
        task.created_by = None

        with patch.object(
            executor.event_broadcaster,
            "broadcast_task_completed",
            return_value=1,
        ) as mock_broadcast:
            await executor._broadcast_task_completed(task, "output text")

            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[1]
            assert call_args["task_id"] == task.id
            assert call_args["output"] == "output text"

    async def test_broadcast_task_failed(self, async_session):
        """Test broadcasting task failed event."""
        executor = TaskExecutor(async_session)

        task = MagicMock(spec=TaskResponse)
        task.id = uuid4()
        task.name = "test-task"
        task.namespace = "default"
        task.status = TaskStatus.FAILED
        task.created_by = "456"

        with patch.object(
            executor.event_broadcaster,
            "broadcast_task_failed",
            return_value=1,
        ) as mock_broadcast:
            await executor._broadcast_task_failed(task, "error message")

            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[1]
            assert call_args["task_id"] == task.id
            assert call_args["error"] == "error message"
            assert call_args["user_id"] == 456


@pytest.mark.epic_18
@pytest.mark.unit
@pytest.mark.backend
class TestTaskQueue:
    """Test suite for TaskQueue - 6 tests."""

    async def test_task_queue_initialization(self):
        """Test task queue initializes correctly."""
        queue = TaskQueue()

        assert queue._queue.qsize() == 0
        assert queue._running == set()
        assert queue._worker_task is None
        assert queue._shutdown is False

    async def test_enqueue_task(self):
        """Test enqueueing a task."""
        queue = TaskQueue()
        task_id = uuid4()

        await queue.enqueue(task_id)

        assert queue._queue.qsize() == 1

    async def test_is_running(self):
        """Test checking if task is running."""
        queue = TaskQueue()
        task_id = uuid4()

        assert queue.is_running(task_id) is False

        queue._running.add(task_id)
        assert queue.is_running(task_id) is True

    async def test_get_running_count(self):
        """Test getting running task count."""
        queue = TaskQueue()

        assert queue.get_running_count() == 0

        queue._running.add(uuid4())
        queue._running.add(uuid4())
        assert queue.get_running_count() == 2

    async def test_get_task_queue_singleton(self):
        """Test get_task_queue returns singleton instance."""
        queue1 = get_task_queue()
        queue2 = get_task_queue()

        assert queue1 is queue2

    async def test_stop_queue(self):
        """Test stopping the queue."""
        queue = TaskQueue()

        # Start the queue
        async def mock_factory():
            return AsyncMock()

        await queue.start(mock_factory)
        assert queue._worker_task is not None

        # Stop the queue
        await queue.stop()
        assert queue._shutdown is True
