"""Unit tests for Task Pydantic schemas.

Tests: 5 tests covering TaskCreateRequest, TaskResponse, TaskStatusUpdate
"""

import pytest
from pydantic import ValidationError

from backend.schemas.task import TaskCreateRequest, TaskResponse, TaskStatusUpdate
from backend.models.tasks import TaskStatus


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTaskCreateRequest:
    """Test suite for TaskCreateRequest - 4 tests."""

    def test_valid_request(self):
        """Test creating valid task request."""
        from uuid import uuid4

        team_id = uuid4()
        request = TaskCreateRequest(
            name="my-task",
            namespace="default",
            team_id=team_id,
            input="Process this data",
            spec={"timeout": 60},
            created_by="user@test.com",
        )
        assert request.name == "my-task"
        assert request.namespace == "default"
        assert request.team_id == team_id
        assert request.input == "Process this data"
        assert request.spec == {"timeout": 60}

    def test_default_namespace(self):
        """Test default namespace is 'default'."""
        request = TaskCreateRequest(name="test-task")
        assert request.namespace == "default"
        assert request.team_id is None

    def test_invalid_name_format(self):
        """Test name validation rejects invalid formats."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreateRequest(name="Invalid_Name")
        assert "Name must consist of lowercase alphanumeric" in str(exc_info.value)

    def test_optional_fields(self):
        """Test optional fields can be omitted."""
        request = TaskCreateRequest(name="minimal-task")
        assert request.input is None
        assert request.spec is None
        assert request.created_by is None


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTaskStatusUpdate:
    """Test suite for TaskStatusUpdate - 3 tests."""

    def test_valid_status_update(self):
        """Test valid status update."""
        update = TaskStatusUpdate(
            status=TaskStatus.COMPLETED,
            output="Task completed successfully",
        )
        assert update.status == TaskStatus.COMPLETED
        assert update.output == "Task completed successfully"

    def test_status_only_update(self):
        """Test status update without output/error."""
        update = TaskStatusUpdate(status=TaskStatus.RUNNING)
        assert update.status == TaskStatus.RUNNING
        assert update.output is None
        assert update.error is None

    def test_failed_status_with_error(self):
        """Test failed status with error message."""
        update = TaskStatusUpdate(
            status=TaskStatus.FAILED,
            error="Something went wrong",
        )
        assert update.status == TaskStatus.FAILED
        assert update.error == "Something went wrong"


@pytest.mark.epic_8
@pytest.mark.unit
@pytest.mark.backend
class TestTaskResponse:
    """Test suite for TaskResponse - 3 tests."""

    def test_response_structure(self):
        """Test response schema structure."""
        from uuid import uuid4
        from datetime import datetime

        task_id = uuid4()
        team_id = uuid4()
        now = datetime.now()

        response = TaskResponse(
            id=task_id,
            name="test-task",
            namespace="default",
            status=TaskStatus.RUNNING,
            team_id=team_id,
            input="Test input",
            output=None,
            error=None,
            spec={"timeout": 30},
            started_at=now,
            completed_at=None,
            created_by="user@test.com",
            created_at=now,
            updated_at=now,
        )
        assert response.id == task_id
        assert response.name == "test-task"
        assert response.status == TaskStatus.RUNNING
        assert response.team_id == team_id

    def test_all_status_values(self):
        """Test response with all status values."""
        from uuid import uuid4
        from datetime import datetime

        for status in TaskStatus:
            response = TaskResponse(
                id=uuid4(),
                name=f"task-{status.value}",
                namespace="default",
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            assert response.status == status

    def test_optional_datetime_fields(self):
        """Test optional datetime fields can be None."""
        from uuid import uuid4
        from datetime import datetime

        response = TaskResponse(
            id=uuid4(),
            name="pending-task",
            namespace="default",
            status=TaskStatus.PENDING,
            started_at=None,
            completed_at=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert response.started_at is None
        assert response.completed_at is None
