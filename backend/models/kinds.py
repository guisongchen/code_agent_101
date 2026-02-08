"""SQLAlchemy model for CRD Kinds (Ghost, Model, Shell, Bot, Team, Skill)."""

import enum
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Enum, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.database.base import Base, SoftDeleteMixin, TimestampMixin


class KindType(str, enum.Enum):
    """Enumeration of supported CRD kind types."""

    GHOST = "ghost"
    MODEL = "model"
    SHELL = "shell"
    BOT = "bot"
    TEAM = "team"
    SKILL = "skill"


class Kind(Base, TimestampMixin, SoftDeleteMixin):
    """Generic model for storing CRD resources.

    This single table stores all CRD kinds (Ghost, Model, Shell, Bot, Team, Skill)
    with a flexible JSON spec field for kind-specific attributes.
    """

    __tablename__ = "kinds"

    # Primary key using UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Kind type (ghost, model, shell, bot, team, skill)
    kind: Mapped[KindType] = mapped_column(
        Enum(KindType, name="kind_type_enum"),
        nullable=False,
        index=True,
    )

    # API version (e.g., "v1")
    api_version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="v1",
    )

    # Resource name (unique within kind + namespace)
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

    # Flexible spec storage as JSON
    spec: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Optional reference to the user who created this resource
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore # noqa: F821
        "Task",
        back_populates="team",
        foreign_keys="Task.team_id",
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "kind",
            "name",
            "namespace",
            name="uix_kind_name_namespace",
        ),
        Index("ix_kinds_kind_namespace", "kind", "namespace"),
        Index("ix_kinds_created_by", "created_by"),
        Index("ix_kinds_deleted_at", "deleted_at"),
    )

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate resource name format."""
        if not name:
            raise ValueError("Name cannot be empty")
        if len(name) > 255:
            raise ValueError("Name cannot exceed 255 characters")
        # Kubernetes-style naming: lowercase alphanumeric with hyphens
        import re
        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", name):
            raise ValueError(
                "Name must consist of lowercase alphanumeric characters or '-', "
                "and must start and end with an alphanumeric character"
            )
        return name

    @validates("namespace")
    def validate_namespace(self, key: str, namespace: str) -> str:
        """Validate namespace format."""
        if not namespace:
            raise ValueError("Namespace cannot be empty")
        if len(namespace) > 255:
            raise ValueError("Namespace cannot exceed 255 characters")
        return namespace

    def __repr__(self) -> str:
        return f"<Kind(id={self.id}, kind={self.kind.value}, name={self.name}, namespace={self.namespace})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary representation."""
        return {
            "apiVersion": self.api_version,
            "kind": self.kind.value,
            "metadata": {
                "id": str(self.id),
                "name": self.name,
                "namespace": self.namespace,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
                "createdBy": self.created_by,
            },
            "spec": self.spec,
        }
