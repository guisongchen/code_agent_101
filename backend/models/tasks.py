"""SQLAlchemy model for Task resources with separate lifecycle."""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.database.base import Base, SoftDeleteMixin, TimestampMixin


class TaskStatus(str, enum.Enum):
    """Enumeration of task statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base, TimestampMixin, SoftDeleteMixin):
    """Model for Task resources with separate lifecycle from Kinds.

    Tasks represent execution units that reference a Team and track
    their own status through the lifecycle.
    """

    __tablename__ = "tasks"

    # Primary key using UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Task name
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Resource namespace for isolation
    namespace: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="default",
    )

    # Task status
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum"),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
    )

    # Reference to the Team (Kind) this task belongs to
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kinds.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Task input/prompt
    input: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Task output/result
    output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Error message if failed
    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Flexible spec storage as JSON for task-specific configuration
    spec: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Timestamps for task lifecycle
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Optional reference to the user who created this task
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    team: Mapped[Optional["Kind"]] = relationship(  # type: ignore # noqa: F821
        "Kind",
        back_populates="tasks",
        foreign_keys=[team_id],
    )

    messages: Mapped[List["Message"]] = relationship(  # type: ignore # noqa: F821
        "Message",
        back_populates="task",
        foreign_keys="Message.task_id",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    sessions: Mapped[List["ChatSession"]] = relationship(  # type: ignore # noqa: F821
        "ChatSession",
        back_populates="task",
        foreign_keys="ChatSession.task_id",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Table constraints
    __table_args__ = (
        Index("ix_tasks_status_namespace", "status", "namespace"),
        Index("ix_tasks_created_by", "created_by"),
        Index("ix_tasks_deleted_at", "deleted_at"),
    )

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate task name format."""
        if not name:
            raise ValueError("Name cannot be empty")
        if len(name) > 255:
            raise ValueError("Name cannot exceed 255 characters")
        return name

    @validates("namespace")
    def validate_namespace(self, key: str, namespace: str) -> str:
        """Validate namespace format."""
        if not namespace:
            raise ValueError("Namespace cannot be empty")
        if len(namespace) > 255:
            raise ValueError("Namespace cannot exceed 255 characters")
        return namespace

    @validates("status")
    def validate_status_transition(self, key: str, new_status: TaskStatus) -> TaskStatus:
        """Validate status transitions."""
        # Terminal states cannot be changed
        if self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            if new_status != self.status:
                raise ValueError(
                    f"Cannot transition from terminal state {self.status} to {new_status}"
                )
        return new_status

    def start(self) -> None:
        """Mark the task as started."""
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {self.status} state")
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, output: Optional[str] = None) -> None:
        """Mark the task as completed."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in {self.status} state")
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        if output:
            self.output = output

    def fail(self, error: str) -> None:
        """Mark the task as failed."""
        if self.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise ValueError(f"Cannot fail task in {self.status} state")
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def cancel(self) -> None:
        """Mark the task as cancelled."""
        if self.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise ValueError(f"Cannot cancel task in {self.status} state")
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, status={self.status.value}, team_id={self.team_id})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "namespace": self.namespace,
            "status": self.status.value,
            "teamId": str(self.team_id) if self.team_id else None,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "spec": self.spec,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "createdBy": self.created_by,
        }
