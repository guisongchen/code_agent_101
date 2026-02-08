"""Task resource service.

Provides CRUD operations for Task resources with lifecycle management.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tasks import Task, TaskStatus
from backend.schemas.task import TaskCreateRequest, TaskResponse


class TaskService:
    """Service for Task resource management with lifecycle operations.

    Unlike CRD resources, Tasks have a separate lifecycle with status transitions:
    PENDING -> RUNNING -> (COMPLETED | FAILED | CANCELLED)
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session for database operations.
        """
        self.session = session

    async def get(
        self,
        task_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[TaskResponse]:
        """Get a task by ID.

        Args:
            task_id: Task UUID.
            include_deleted: Whether to include soft-deleted tasks.

        Returns:
            TaskResponse if found, None otherwise.
        """
        conditions = [Task.id == task_id]

        if not include_deleted:
            conditions.append(Task.deleted_at.is_(None))

        result = await self.session.execute(
            select(Task).where(and_(*conditions))
        )
        task = result.scalar_one_or_none()

        return TaskResponse.from_db_model(task) if task else None

    async def get_by_name(
        self,
        name: str,
        namespace: str = "default",
        include_deleted: bool = False,
    ) -> Optional[TaskResponse]:
        """Get a task by name and namespace.

        Args:
            name: Task name.
            namespace: Task namespace.
            include_deleted: Whether to include soft-deleted tasks.

        Returns:
            TaskResponse if found, None otherwise.
        """
        conditions = [
            Task.name == name,
            Task.namespace == namespace,
        ]

        if not include_deleted:
            conditions.append(Task.deleted_at.is_(None))

        result = await self.session.execute(
            select(Task).where(and_(*conditions))
        )
        task = result.scalar_one_or_none()

        return TaskResponse.from_db_model(task) if task else None

    async def list(
        self,
        namespace: Optional[str] = "default",
        status: Optional[TaskStatus] = None,
        team_id: Optional[UUID] = None,
        include_all_namespaces: bool = False,
        include_deleted: bool = False,
    ) -> List[TaskResponse]:
        """List tasks with optional filtering.

        Args:
            namespace: Filter by namespace.
            status: Filter by task status.
            team_id: Filter by team ID.
            include_all_namespaces: If True, list tasks from all namespaces.
            include_deleted: Whether to include soft-deleted tasks.

        Returns:
            List of TaskResponse schemas.
        """
        conditions = []

        if not include_deleted:
            conditions.append(Task.deleted_at.is_(None))

        if not include_all_namespaces and namespace is not None:
            conditions.append(Task.namespace == namespace)

        if status is not None:
            conditions.append(Task.status == status)

        if team_id is not None:
            conditions.append(Task.team_id == team_id)

        query = select(Task)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Task.created_at.desc())

        result = await self.session.execute(query)
        tasks = result.scalars().all()

        return [TaskResponse.from_db_model(t) for t in tasks]

    async def create(
        self,
        request: TaskCreateRequest,
        created_by: Optional[str] = None,
    ) -> TaskResponse:
        """Create a new task.

        Args:
            request: Task creation request.
            created_by: User creating the task.

        Returns:
            Created TaskResponse.

        Raises:
            ValueError: If task with same name/namespace already exists.
        """
        # Check for existing task with same name/namespace
        existing = await self.get_by_name(request.name, request.namespace)
        if existing:
            raise ValueError(
                f"Task '{request.name}' already exists in namespace '{request.namespace}'"
            )

        task = Task(
            name=request.name,
            namespace=request.namespace,
            team_id=request.team_id,
            input=request.input,
            spec=request.spec or {},
            created_by=created_by or request.created_by,
            status=TaskStatus.PENDING,
        )

        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)

        return TaskResponse.from_db_model(task)

    async def start(self, task_id: UUID) -> TaskResponse:
        """Mark a task as started.

        Args:
            task_id: Task UUID.

        Returns:
            Updated TaskResponse.

        Raises:
            ValueError: If task not found or not in PENDING state.
        """
        task = await self._get_task_or_raise(task_id)

        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {task.status.value} state")

        task.start()
        await self.session.flush()
        await self.session.refresh(task)

        return TaskResponse.from_db_model(task)

    async def complete(
        self,
        task_id: UUID,
        output: Optional[str] = None,
    ) -> TaskResponse:
        """Mark a task as completed.

        Args:
            task_id: Task UUID.
            output: Task output.

        Returns:
            Updated TaskResponse.

        Raises:
            ValueError: If task not found or not in RUNNING state.
        """
        task = await self._get_task_or_raise(task_id)

        if task.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in {task.status.value} state")

        task.complete(output)
        await self.session.flush()
        await self.session.refresh(task)

        return TaskResponse.from_db_model(task)

    async def fail(
        self,
        task_id: UUID,
        error: str,
    ) -> TaskResponse:
        """Mark a task as failed.

        Args:
            task_id: Task UUID.
            error: Error message.

        Returns:
            Updated TaskResponse.

        Raises:
            ValueError: If task not found or in terminal state.
        """
        task = await self._get_task_or_raise(task_id)

        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            raise ValueError(f"Cannot fail task in {task.status.value} state")

        task.fail(error)
        await self.session.flush()
        await self.session.refresh(task)

        return TaskResponse.from_db_model(task)

    async def cancel(self, task_id: UUID) -> TaskResponse:
        """Cancel a task.

        Args:
            task_id: Task UUID.

        Returns:
            Updated TaskResponse.

        Raises:
            ValueError: If task not found or in terminal state.
        """
        task = await self._get_task_or_raise(task_id)

        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            raise ValueError(f"Cannot cancel task in {task.status.value} state")

        task.cancel()
        await self.session.flush()
        await self.session.refresh(task)

        return TaskResponse.from_db_model(task)

    async def delete(
        self,
        task_id: UUID,
    ) -> bool:
        """Soft delete a task.

        Args:
            task_id: Task UUID.

        Returns:
            True if task was deleted, False if not found.
        """
        result = await self.session.execute(
            select(Task).where(
                and_(
                    Task.id == task_id,
                    Task.deleted_at.is_(None),
                )
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        task.soft_delete()
        return True

    async def delete_by_name(
        self,
        name: str,
        namespace: str = "default",
    ) -> bool:
        """Soft delete a task by name.

        Args:
            name: Task name.
            namespace: Task namespace.

        Returns:
            True if task was deleted, False if not found.
        """
        result = await self.session.execute(
            select(Task).where(
                and_(
                    Task.name == name,
                    Task.namespace == namespace,
                    Task.deleted_at.is_(None),
                )
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        task.soft_delete()
        return True

    async def _get_task_or_raise(self, task_id: UUID) -> Task:
        """Get task by ID or raise ValueError.

        Args:
            task_id: Task UUID.

        Returns:
            Task model instance.

        Raises:
            ValueError: If task not found.
        """
        result = await self.session.execute(
            select(Task).where(
                and_(
                    Task.id == task_id,
                    Task.deleted_at.is_(None),
                )
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        return task
