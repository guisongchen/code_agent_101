"""Unit tests for TaskService.

Tests: 10 tests covering TaskService CRUD and lifecycle operations
"""

import pytest
import pytest_asyncio
from uuid import uuid4

from backend.services.task import TaskService
from backend.schemas.task import TaskCreateRequest, TaskResponse
from backend.models.tasks import TaskStatus


@pytest.mark.epic_9
@pytest.mark.unit
@pytest.mark.backend
class TestTaskService:
    """Test suite for TaskService - 10 tests."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create TaskService instance."""
        return TaskService(async_session)

    @pytest_asyncio.fixture
    async def task_request(self):
        """Create a sample task request."""
        return TaskCreateRequest(
            name="test-task",
            namespace="default",
            input="Process this data",
            spec={"timeout": 60},
        )

    async def test_create_task(self, service, task_request):
        """Test creating a task."""
        result = await service.create(task_request, created_by="test-user")

        assert result.name == "test-task"
        assert result.namespace == "default"
        assert result.input == "Process this data"
        assert result.status == TaskStatus.PENDING
        assert result.created_by == "test-user"

    async def test_get_task(self, service, task_request):
        """Test retrieving a task by ID."""
        created = await service.create(task_request)
        result = await service.get(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "test-task"

    async def test_get_task_by_name(self, service, task_request):
        """Test retrieving a task by name."""
        await service.create(task_request)
        result = await service.get_by_name("test-task", "default")

        assert result is not None
        assert result.name == "test-task"
        assert result.namespace == "default"

    async def test_list_tasks(self, service, task_request):
        """Test listing tasks."""
        await service.create(task_request)

        # Create another task
        task2 = TaskCreateRequest(name="another-task", namespace="default")
        await service.create(task2)

        results = await service.list()
        assert len(results) == 2

    async def test_list_tasks_by_status(self, service, task_request):
        """Test listing tasks filtered by status."""
        created = await service.create(task_request)

        # Start the task
        await service.start(created.id)

        running_tasks = await service.list(status=TaskStatus.RUNNING)
        assert len(running_tasks) == 1

        pending_tasks = await service.list(status=TaskStatus.PENDING)
        assert len(pending_tasks) == 0

    async def test_task_lifecycle(self, service, task_request):
        """Test full task lifecycle: pending -> running -> completed."""
        # Create task
        created = await service.create(task_request)
        assert created.status == TaskStatus.PENDING

        # Start task
        started = await service.start(created.id)
        assert started.status == TaskStatus.RUNNING
        assert started.started_at is not None

        # Complete task
        completed = await service.complete(created.id, output="Task completed successfully")
        assert completed.status == TaskStatus.COMPLETED
        assert completed.output == "Task completed successfully"
        assert completed.completed_at is not None

    async def test_fail_task(self, service, task_request):
        """Test failing a task."""
        created = await service.create(task_request)
        await service.start(created.id)

        failed = await service.fail(created.id, error="Something went wrong")
        assert failed.status == TaskStatus.FAILED
        assert failed.error == "Something went wrong"
        assert failed.completed_at is not None

    async def test_cancel_task(self, service, task_request):
        """Test cancelling a task."""
        created = await service.create(task_request)

        cancelled = await service.cancel(created.id)
        assert cancelled.status == TaskStatus.CANCELLED
        assert cancelled.completed_at is not None

    async def test_invalid_status_transitions(self, service, task_request):
        """Test invalid status transitions are blocked."""
        created = await service.create(task_request)

        # Cannot complete from PENDING
        with pytest.raises(ValueError, match="Cannot complete task in pending state"):
            await service.complete(created.id)

        # Start then try to start again
        await service.start(created.id)
        with pytest.raises(ValueError, match="Cannot start task in running state"):
            await service.start(created.id)

        # Complete then try to fail
        await service.complete(created.id)
        with pytest.raises(ValueError, match="Cannot fail task in completed state"):
            await service.fail(created.id, error="too late")

    async def test_delete_task(self, service, task_request):
        """Test soft deleting a task."""
        created = await service.create(task_request)

        deleted = await service.delete(created.id)
        assert deleted is True

        result = await service.get(created.id)
        assert result is None
