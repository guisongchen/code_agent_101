"""Unit tests for SQLAlchemy Task model.

Tests: 4 tests covering Task model functionality
"""

import uuid
from datetime import datetime

import pytest

from backend.models.tasks import Task, TaskStatus


@pytest.mark.epic_7
@pytest.mark.unit
@pytest.mark.backend
class TestTaskModel:
    """Test suite for Task model - 4 tests."""

    def test_task_creation(self, db_session, team):
        """Test basic Task creation."""
        task = Task(
            name="test-task",
            namespace="default",
            team_id=team.id,
            input="Hello, world!",
            spec={"timeout": 30},
            created_by="user123",
        )
        db_session.add(task)
        db_session.commit()

        assert task.id is not None
        assert isinstance(task.id, uuid.UUID)
        assert task.name == "test-task"
        assert task.namespace == "default"
        assert task.status == TaskStatus.PENDING
        assert task.team_id == team.id
        assert task.input == "Hello, world!"
        assert task.spec == {"timeout": 30}
        assert task.created_by == "user123"
        assert task.created_at is not None

    def test_task_status_transitions(self, db_session, team):
        """Test task status lifecycle transitions."""
        task = Task(
            name="lifecycle-task",
            namespace="default",
            team_id=team.id,
            input="Test",
        )
        db_session.add(task)
        db_session.commit()

        # Initial state
        assert task.status == TaskStatus.PENDING

        # Start the task
        task.start()
        db_session.commit()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

        # Complete the task
        task.complete(output="Done!")
        db_session.commit()
        assert task.status == TaskStatus.COMPLETED
        assert task.output == "Done!"
        assert task.completed_at is not None

    def test_task_invalid_transitions(self, db_session, team):
        """Test invalid status transitions are blocked."""
        task = Task(
            name="invalid-task",
            namespace="default",
            team_id=team.id,
        )
        db_session.add(task)
        db_session.commit()

        # Cannot complete from PENDING
        with pytest.raises(ValueError, match="Cannot complete task in.*PENDING.*state"):
            task.complete()

        # Start then complete
        task.start()
        db_session.commit()

        # Cannot start from RUNNING
        with pytest.raises(ValueError, match="Cannot start task in.*RUNNING.*state"):
            task.start()

        # Complete the task
        task.complete()
        db_session.commit()

        # Cannot fail from terminal state (COMPLETED)
        with pytest.raises(ValueError, match="Cannot fail task in.*COMPLETED.*state"):
            task.fail("error")

    def test_task_to_dict(self, db_session, team):
        """Test task dictionary serialization."""
        task = Task(
            name="dict-task",
            namespace="test-ns",
            team_id=team.id,
            input="Test input",
            spec={"key": "value"},
            status=TaskStatus.RUNNING,
            created_by="user456",
        )
        db_session.add(task)
        db_session.commit()

        data = task.to_dict()

        assert data["name"] == "dict-task"
        assert data["namespace"] == "test-ns"
        assert data["status"] == "running"
        assert data["teamId"] == str(team.id)
        assert data["input"] == "Test input"
        assert data["spec"] == {"key": "value"}
        assert data["createdBy"] == "user456"
        assert "id" in data
        assert "createdAt" in data
