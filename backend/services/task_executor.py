"""Task executor for running tasks with chat_shell integration.

Orchestrates task execution by integrating Task management, chat_shell,
and event broadcasting into a complete execution pipeline.

Epic 18: Chat Execution Engine Integration
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tasks import TaskStatus
from backend.schemas.task import TaskResponse
from backend.services.chat import ChatService, ChatServiceError
from backend.services.message import MessageService
from backend.services.task import TaskService
from backend.websocket.task_events import get_task_event_broadcaster

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """Raised when task execution fails."""

    pass


class TaskExecutor:
    """Executor for running tasks with chat_shell integration.

    Orchestrates the complete task execution flow:
    1. Validate task and bot configuration
    2. Start task and broadcast status
    3. Execute chat with AI agent
    4. Store messages and results
    5. Complete task and broadcast status
    """

    # Maximum retry attempts for failed executions
    MAX_RETRIES = 3

    # Retry delay in seconds
    RETRY_DELAY = 1.0

    def __init__(self, session: AsyncSession):
        """Initialize executor with database session.

        Args:
            session: Async SQLAlchemy session for database operations.
        """
        self.session = session
        self.task_service = TaskService(session)
        self.chat_service = ChatService(session)
        self.message_service = MessageService(session)
        self.event_broadcaster = get_task_event_broadcaster()

    async def execute_task(
        self,
        task_id: UUID,
        bot_name: Optional[str] = None,
        namespace: str = "default",
    ) -> TaskResponse:
        """Execute a task with chat_shell integration.

        Args:
            task_id: Task ID to execute.
            bot_name: Optional bot name (extracted from task spec if not provided).
            namespace: Namespace for bot lookup.

        Returns:
            Completed TaskResponse.

        Raises:
            TaskExecutionError: If execution fails after retries.
        """
        # Get task
        task = await self.task_service.get(task_id)
        if not task:
            raise TaskExecutionError(f"Task {task_id} not found")

        # Extract bot name from task spec if not provided
        if not bot_name:
            bot_name = self._extract_bot_name(task)

        # Validate bot configuration
        try:
            validation = await self.chat_service.validate_bot_configuration(
                bot_name, namespace
            )
            if not validation["valid"]:
                errors = "; ".join(validation["errors"])
                raise TaskExecutionError(f"Invalid bot configuration: {errors}")
        except ChatServiceError as e:
            raise TaskExecutionError(f"Bot validation failed: {e}") from e

        # Start task
        task = await self.task_service.start(task_id)
        await self._broadcast_task_started(task)

        # Execute with retry logic
        attempt = 0
        last_error = None

        while attempt < self.MAX_RETRIES:
            try:
                result = await self._execute_with_chat(
                    task_id, bot_name, namespace, task
                )
                return result
            except Exception as e:
                attempt += 1
                last_error = e
                logger.warning(
                    f"Task {task_id} execution attempt {attempt} failed: {e}"
                )
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAY * attempt)

        # All retries exhausted
        error_msg = f"Task execution failed after {self.MAX_RETRIES} attempts: {last_error}"
        logger.error(error_msg)
        task = await self.task_service.fail(task_id, error_msg)
        await self._broadcast_task_failed(task, error_msg)
        raise TaskExecutionError(error_msg) from last_error

    async def _execute_with_chat(
        self,
        task_id: UUID,
        bot_name: str,
        namespace: str,
        task: TaskResponse,
    ) -> TaskResponse:
        """Execute task using chat service.

        Args:
            task_id: Task ID.
            bot_name: Bot name to use.
            namespace: Namespace for bot.
            task: Task response.

        Returns:
            Completed TaskResponse.
        """
        # Store user input as first message
        if task.input:
            await self.message_service.create_user_message(
                task_id=task_id,
                content=task.input,
                thread_id=str(task_id),
                metadata={"source": "task_input"},
            )

        # Prepare messages for chat
        messages: List[Dict[str, str]] = []
        if task.input:
            messages.append({"role": "user", "content": task.input})

        # Execute chat
        content_parts = []
        tool_calls = []
        error = None

        try:
            async for event in self.chat_service.execute_chat(
                bot_name=bot_name,
                messages=messages,
                namespace=namespace,
                thread_id=str(task_id),
                show_thinking=True,
            ):
                event_type = event.get("type")
                event_data = event.get("data", {})

                if event_type == "content":
                    content_parts.append(event_data.get("text", ""))
                elif event_type == "tool_call":
                    tool_calls.append({
                        "tool": event_data.get("tool"),
                        "args": event_data.get("args"),
                    })
                elif event_type == "error":
                    error = event_data.get("error", "Unknown error")

        except ChatServiceError as e:
            error = str(e)
            logger.error(f"Chat service error for task {task_id}: {e}")

        # Store assistant response
        content = "".join(content_parts)
        if content:
            await self.message_service.create_assistant_message(
                task_id=task_id,
                content=content,
                thread_id=str(task_id),
                metadata={"tool_calls": tool_calls} if tool_calls else None,
            )

        # Complete or fail task
        if error:
            task = await self.task_service.fail(task_id, error)
            await self._broadcast_task_failed(task, error)
            raise TaskExecutionError(error)
        else:
            task = await self.task_service.complete(task_id, output=content)
            await self._broadcast_task_completed(task, content)
            return task

    def _extract_bot_name(self, task: TaskResponse) -> str:
        """Extract bot name from task spec.

        Args:
            task: Task response.

        Returns:
            Bot name.

        Raises:
            TaskExecutionError: If bot name cannot be determined.
        """
        spec = task.spec or {}

        # Check spec for bot reference
        if "bot_name" in spec:
            return spec["bot_name"]

        if "botRef" in spec:
            return spec["botRef"].get("name", "default")

        # Default bot name
        return "default"

    async def _broadcast_task_started(self, task: TaskResponse) -> None:
        """Broadcast task started event.

        Args:
            task: Task response.
        """
        try:
            await self.event_broadcaster.broadcast_task_started(
                task_id=task.id,
                task_data={
                    "name": task.name,
                    "namespace": task.namespace,
                    "status": task.status.value,
                },
                user_id=self._extract_user_id(task),
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast task started event: {e}")

    async def _broadcast_task_completed(
        self, task: TaskResponse, output: str
    ) -> None:
        """Broadcast task completed event.

        Args:
            task: Task response.
            output: Task output.
        """
        try:
            await self.event_broadcaster.broadcast_task_completed(
                task_id=task.id,
                task_data={
                    "name": task.name,
                    "namespace": task.namespace,
                    "status": task.status.value,
                },
                output=output,
                user_id=self._extract_user_id(task),
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast task completed event: {e}")

    async def _broadcast_task_failed(self, task: TaskResponse, error: str) -> None:
        """Broadcast task failed event.

        Args:
            task: Task response.
            error: Error message.
        """
        try:
            await self.event_broadcaster.broadcast_task_failed(
                task_id=task.id,
                task_data={
                    "name": task.name,
                    "namespace": task.namespace,
                    "status": task.status.value,
                },
                error=error,
                user_id=self._extract_user_id(task),
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast task failed event: {e}")

    def _extract_user_id(self, task: TaskResponse) -> Optional[int]:
        """Extract user ID from task.

        Args:
            task: Task response.

        Returns:
            User ID if available, None otherwise.
        """
        if task.created_by:
            try:
                return int(task.created_by)
            except (ValueError, TypeError):
                pass
        return None


class TaskQueue:
    """Simple in-memory task queue for background processing.

    Provides asynchronous task execution with queue management.
    """

    def __init__(self):
        """Initialize the task queue."""
        self._queue: asyncio.Queue[UUID] = asyncio.Queue()
        self._running: set[UUID] = set()
        self._worker_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def start(self, session_factory) -> None:
        """Start the queue worker.

        Args:
            session_factory: Factory function to create database sessions.
        """
        self._worker_task = asyncio.create_task(
            self._worker_loop(session_factory)
        )
        logger.info("Task queue started")

    async def stop(self) -> None:
        """Stop the queue worker."""
        self._shutdown = True
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Task queue stopped")

    async def enqueue(self, task_id: UUID) -> None:
        """Add a task to the queue.

        Args:
            task_id: Task ID to execute.
        """
        await self._queue.put(task_id)
        logger.info(f"Task {task_id} enqueued")

    def is_running(self, task_id: UUID) -> bool:
        """Check if a task is currently running.

        Args:
            task_id: Task ID.

        Returns:
            True if task is running, False otherwise.
        """
        return task_id in self._running

    def get_running_count(self) -> int:
        """Get the number of currently running tasks.

        Returns:
            Number of running tasks.
        """
        return len(self._running)

    async def _worker_loop(self, session_factory) -> None:
        """Worker loop that processes tasks from the queue.

        Args:
            session_factory: Factory function to create database sessions.
        """
        while not self._shutdown:
            try:
                task_id = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            # Skip if already running
            if task_id in self._running:
                logger.warning(f"Task {task_id} already running, skipping")
                self._queue.task_done()
                continue

            # Execute task
            self._running.add(task_id)
            try:
                async with session_factory() as session:
                    executor = TaskExecutor(session)
                    await executor.execute_task(task_id)
            except Exception as e:
                logger.error(f"Task {task_id} execution failed: {e}")
            finally:
                self._running.discard(task_id)
                self._queue.task_done()


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get the global task queue instance.

    Returns:
        The global TaskQueue instance.
    """
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
