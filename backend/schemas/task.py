"""Pydantic schemas for Task resources.

Task resources define execution units with a separate lifecycle from CRD resources.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.tasks import TaskStatus


class TaskCreateRequest(BaseModel):
    """Request schema for creating a Task resource.

    Used in POST /api/v1/tasks endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Task name",
        examples=["process-data", "generate-report"],
    )
    namespace: str = Field(
        default="default",
        min_length=1,
        max_length=255,
        description="Namespace for task isolation",
    )
    team_id: Optional[UUID] = Field(
        default=None,
        alias="teamId",
        description="Reference to the Team resource executing this task",
    )
    input: Optional[str] = Field(
        default=None,
        description="Input data or prompt for the task",
    )
    spec: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Task-specific configuration",
    )
    created_by: Optional[str] = Field(
        default=None,
        alias="createdBy",
        description="User who created the task",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name follows Kubernetes naming convention."""
        import re

        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", v):
            raise ValueError(
                "Name must consist of lowercase alphanumeric characters or '-', "
                "and must start and end with an alphanumeric character"
            )
        return v

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Validate namespace follows Kubernetes naming convention."""
        import re

        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", v):
            raise ValueError(
                "Namespace must consist of lowercase alphanumeric characters or '-', "
                "and must start and end with an alphanumeric character"
            )
        return v


class TaskStatusUpdate(BaseModel):
    """Request schema for updating task status.

    Used in PATCH /api/v1/tasks/{id}/status endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    status: TaskStatus = Field(
        ...,
        description="New task status",
    )
    output: Optional[str] = Field(
        default=None,
        description="Task output (when completing)",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message (when failing)",
    )


class TaskResponse(BaseModel):
    """Response schema for Task resources.

    Returned by API endpoints with full task details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the task",
    )
    name: str = Field(
        ...,
        description="Task name",
    )
    namespace: str = Field(
        ...,
        description="Task namespace",
    )
    status: TaskStatus = Field(
        ...,
        description="Current task status",
    )
    team_id: Optional[UUID] = Field(
        default=None,
        alias="teamId",
        description="Reference to the Team resource",
    )
    input: Optional[str] = Field(
        default=None,
        description="Task input",
    )
    output: Optional[str] = Field(
        default=None,
        description="Task output",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if task failed",
    )
    spec: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Task configuration",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        alias="startedAt",
        description="When task started running",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        alias="completedAt",
        description="When task completed/failed/cancelled",
    )
    created_by: Optional[str] = Field(
        default=None,
        alias="createdBy",
        description="User who created the task",
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="When task was created",
    )
    updated_at: datetime = Field(
        ...,
        alias="updatedAt",
        description="When task was last updated",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "TaskResponse":
        """Create TaskResponse from database Task model.

        Args:
            db_model: Task model instance from database.

        Returns:
            TaskResponse instance populated from database model.
        """
        return cls(
            id=db_model.id,
            name=db_model.name,
            namespace=db_model.namespace,
            status=db_model.status,
            team_id=db_model.team_id,
            input=db_model.input,
            output=db_model.output,
            error=db_model.error,
            spec=db_model.spec,
            started_at=db_model.started_at,
            completed_at=db_model.completed_at,
            created_by=db_model.created_by,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )
