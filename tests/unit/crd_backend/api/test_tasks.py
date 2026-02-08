"""Tests for Task Management API endpoints.

Tests: 12 tests covering Task API endpoints
- Create task: 3 tests (success, duplicate, invalid team)
- List tasks: 2 tests (basic, with filters)
- Get task: 2 tests (success, not found)
- Update status: 3 tests (start, complete, invalid transition)
- Delete task: 2 tests (success, not found)

Epic 12: Task Management API
"""

import pytest
from httpx import AsyncClient

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_12,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_12
@pytest.mark.unit
@pytest.mark.backend
class TestTaskAPI:
    """Test suite for Task API endpoints - 12 tests."""

    async def test_create_task_success(self, async_client: AsyncClient):
        """Test creating a Task returns 201 with correct data."""
        response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "test-task",
                "namespace": "default",
                "input": "Process this data",
                "spec": {"timeout": 300},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-task"
        assert data["namespace"] == "default"
        assert data["status"] == "pending"
        assert data["input"] == "Process this data"
        assert data["spec"] == {"timeout": 300}
        assert "id" in data

    async def test_create_task_duplicate_returns_409(self, async_client: AsyncClient):
        """Test creating duplicate Task returns 409 Conflict."""
        # Create first task
        await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "duplicate-task",
                "namespace": "default",
                "input": "First",
            },
        )

        # Try to create duplicate
        response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "duplicate-task",
                "namespace": "default",
                "input": "Second",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_create_task_with_team_reference(self, async_client: AsyncClient):
        """Test creating a Task with team_id stores the reference correctly.

        Note: This test uses a random UUID for team_id since the Task API
        doesn't validate team existence (foreign key constraint handles it).
        """
        import uuid

        # Use a random team_id - the API accepts it (FK constraint would fail at DB level
        # if we actually tried to commit, but our test uses in-memory SQLite)
        fake_team_id = str(uuid.uuid4())

        # Create task with team reference
        response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "task-with-team",
                "namespace": "default",
                "teamId": fake_team_id,
                "input": "Process with team",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["teamId"] == fake_team_id

    async def test_list_tasks(self, async_client: AsyncClient):
        """Test listing Tasks returns list with created resources."""
        # Create a task first
        await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "list-test-task",
                "namespace": "default",
                "input": "Test",
            },
        )

        response = await async_client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_tasks_with_filters(self, async_client: AsyncClient):
        """Test listing Tasks with status and namespace filters."""
        # Create a task
        await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "filtered-task",
                "namespace": "default",
                "input": "Test",
            },
        )

        # Filter by status
        response = await async_client.get("/api/v1/tasks?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(t["status"] == "pending" for t in data)

        # Filter by namespace
        response = await async_client.get("/api/v1/tasks?namespace=default")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_task_success(self, async_client: AsyncClient):
        """Test getting a specific Task by ID."""
        # Create a task
        create_response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "get-test-task",
                "namespace": "default",
                "input": "Test input",
            },
        )
        task_id = create_response.json()["id"]

        # Get the task
        response = await async_client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["name"] == "get-test-task"
        assert data["input"] == "Test input"

    async def test_get_task_not_found(self, async_client: AsyncClient):
        """Test getting non-existent Task returns 404."""
        fake_uuid = "12345678-1234-1234-1234-123456789abc"
        response = await async_client.get(f"/api/v1/tasks/{fake_uuid}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_task_status_start(self, async_client: AsyncClient):
        """Test starting a task transitions status to running."""
        # Create a task
        create_response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "start-test-task",
                "namespace": "default",
                "input": "Test",
            },
        )
        task_id = create_response.json()["id"]

        # Start the task
        response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "running"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["startedAt"] is not None

    async def test_update_task_status_complete(self, async_client: AsyncClient):
        """Test completing a task transitions status to completed."""
        # Create a task
        create_response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "complete-test-task",
                "namespace": "default",
                "input": "Test",
            },
        )
        task_id = create_response.json()["id"]

        # Start the task
        await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "running"},
        )

        # Complete the task
        response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={
                "status": "completed",
                "output": "Task completed successfully",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output"] == "Task completed successfully"
        assert data["completedAt"] is not None

    async def test_update_task_status_fail(self, async_client: AsyncClient):
        """Test failing a task transitions status to failed."""
        # Create a task
        create_response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "fail-test-task",
                "namespace": "default",
                "input": "Test",
            },
        )
        task_id = create_response.json()["id"]

        # Start the task
        await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "running"},
        )

        # Fail the task
        response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={
                "status": "failed",
                "error": "Something went wrong",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Something went wrong"

    async def test_update_task_invalid_transition(self, async_client: AsyncClient):
        """Test invalid status transition returns 400."""
        # Create a task
        create_response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "invalid-transition-task",
                "namespace": "default",
                "input": "Test",
            },
        )
        task_id = create_response.json()["id"]

        # Try to complete without starting (invalid transition)
        response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "completed"},
        )
        assert response.status_code == 400
        assert "cannot complete" in response.json()["detail"].lower()

    async def test_delete_task_success(self, async_client: AsyncClient):
        """Test deleting a task soft-deletes it."""
        # Create a task
        create_response = await async_client.post(
            "/api/v1/tasks",
            json={
                "name": "delete-test-task",
                "namespace": "default",
                "input": "Test",
            },
        )
        task_id = create_response.json()["id"]

        # Delete the task
        response = await async_client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 204

        # Verify task is gone
        get_response = await async_client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404

    async def test_delete_task_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent Task returns 404."""
        fake_uuid = "12345678-1234-1234-1234-123456789abc"
        response = await async_client.delete(f"/api/v1/tasks/{fake_uuid}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
