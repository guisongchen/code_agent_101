"""RESTful API endpoints for Task resources.

Implements Task Management API with lifecycle operations.

Epic 12: Task Management API
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db_session
from backend.models.tasks import TaskStatus
from backend.schemas import TaskCreateRequest, TaskResponse, TaskStatusUpdate
from backend.services import TaskService

router = APIRouter()


# =============================================================================
# Task Endpoints
# =============================================================================


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Task",
    description="Create a new Task resource with the specified configuration. Optionally references a Team.",
)
async def create_task(
    request: TaskCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """Create a new Task resource.

    Args:
        request: Task creation request with name, namespace, team_id, input, spec.
        session: Database session.

    Returns:
        Created TaskResponse.

    Raises:
        HTTPException: 409 if task with same name/namespace already exists.
        HTTPException: 400 if team_id references non-existent team.
    """
    service = TaskService(session)

    try:
        result = await service.create(request, created_by=request.created_by)
        return result
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/tasks",
    response_model=List[TaskResponse],
    summary="List Tasks",
    description="List all Task resources with optional filtering by namespace, status, and team_id.",
)
async def list_tasks(
    namespace: Optional[str] = Query(default="default", description="Namespace filter (omit for all namespaces)"),
    status: Optional[TaskStatus] = Query(default=None, description="Filter by task status"),
    team_id: Optional[UUID] = Query(default=None, description="Filter by team ID"),
    session: AsyncSession = Depends(get_db_session),
) -> List[TaskResponse]:
    """List Task resources with optional filtering.

    Args:
        namespace: Filter by namespace (default: 'default', omit for all).
        status: Filter by task status.
        team_id: Filter by team ID.
        session: Database session.

    Returns:
        List of TaskResponse matching the filters.
    """
    service = TaskService(session)

    include_all_namespaces = namespace is None
    return await service.list(
        namespace=namespace,
        status=status,
        team_id=team_id,
        include_all_namespaces=include_all_namespaces,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get a Task",
    description="Get a specific Task resource by ID.",
)
async def get_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """Get a Task resource by ID.

    Args:
        task_id: Task UUID.
        session: Database session.

    Returns:
        TaskResponse if found.

    Raises:
        HTTPException: 404 if task not found.
    """
    service = TaskService(session)
    task = await service.get(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found",
        )
    return task


@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskResponse,
    summary="Update Task Status",
    description="Update task status (start, complete, fail, cancel). Validates status transitions.",
)
async def update_task_status(
    task_id: UUID,
    update: TaskStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """Update task status with lifecycle transition validation.

    Args:
        task_id: Task UUID.
        update: Status update with new status and optional output/error.
        session: Database session.

    Returns:
        Updated TaskResponse.

    Raises:
        HTTPException: 404 if task not found.
        HTTPException: 400 if status transition is invalid.
    """
    service = TaskService(session)

    try:
        if update.status == TaskStatus.RUNNING:
            return await service.start(task_id)
        elif update.status == TaskStatus.COMPLETED:
            return await service.complete(task_id, output=update.output)
        elif update.status == TaskStatus.FAILED:
            return await service.fail(task_id, error=update.error or "Unknown error")
        elif update.status == TaskStatus.CANCELLED:
            return await service.cancel(task_id)
        elif update.status == TaskStatus.PENDING:
            # Reset to pending - not typically allowed but service handles it
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reset task to PENDING status",
            )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Task",
    description="Soft delete a Task resource by ID.",
)
async def delete_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a Task resource (soft delete).

    Args:
        task_id: Task UUID.
        session: Database session.

    Raises:
        HTTPException: 404 if task not found.
    """
    service = TaskService(session)
    deleted = await service.delete(task_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found",
        )
