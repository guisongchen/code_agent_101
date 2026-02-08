"""Base Pydantic schemas for CRD resources.

Provides foundational schemas used across all CRD types.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.kinds import KindType


class Metadata(BaseModel):
    """Metadata schema for all CRD resources.

    Mirrors the common fields stored in the Kind model.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Resource name (Kubernetes-style: lowercase alphanumeric with hyphens)",
        examples=["my-ghost", "gpt-4-model"],
    )
    namespace: str = Field(
        default="default",
        min_length=1,
        max_length=255,
        description="Namespace for resource isolation",
        examples=["default", "production", "team-alpha"],
    )
    created_by: Optional[str] = Field(
        default=None,
        alias="createdBy",
        description="User who created the resource",
        examples=["user@example.com"],
    )
    created_at: Optional[datetime] = Field(
        default=None,
        alias="createdAt",
        description="Timestamp when resource was created",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        alias="updatedAt",
        description="Timestamp when resource was last updated",
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


class ResourceRef(BaseModel):
    """Reference to another CRD resource.

    Used for establishing relationships between resources (e.g., Bot references Ghost).
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: KindType = Field(
        ...,
        description="Type of resource being referenced",
        examples=["ghost", "model", "shell"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the referenced resource",
        examples=["my-ghost", "gpt-4"],
    )
    namespace: str = Field(
        default="default",
        min_length=1,
        max_length=255,
        description="Namespace of the referenced resource",
        examples=["default", "production"],
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


class BaseSpec(BaseModel):
    """Base specification schema.

    All specific spec schemas inherit from this.
    """

    model_config = ConfigDict(extra="allow")

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the resource",
        examples=["Production GPT-4 configuration"],
    )


class BaseCRD(BaseModel):
    """Base CRD schema that all resource types extend.

    Follows Kubernetes-style resource structure with apiVersion, kind, metadata, and spec.
    """

    model_config = ConfigDict(populate_by_name=True)

    api_version: str = Field(
        default="v1",
        alias="apiVersion",
        description="API version for this resource",
        examples=["v1"],
    )
    kind: KindType = Field(
        ...,
        description="Type of CRD resource",
        examples=["ghost", "model", "bot"],
    )
    metadata: Metadata = Field(
        ...,
        description="Resource metadata (name, namespace, timestamps)",
    )
    spec: BaseSpec = Field(
        ...,
        description="Resource-specific specification",
    )

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format suitable for database storage.

        Returns:
            Dict with keys matching the Kind model columns.
        """
        return {
            "kind": self.kind.value,
            "api_version": self.api_version,
            "name": self.metadata.name,
            "namespace": self.metadata.namespace,
            "spec": self.spec.model_dump(by_alias=True, exclude_none=True),
            "created_by": self.metadata.created_by,
        }

    @classmethod
    def from_db_model(cls, db_model: Any) -> "BaseCRD":
        """Create schema instance from database model.

        Args:
            db_model: Kind model instance from database.

        Returns:
            BaseCRD instance populated from database model.
        """
        raise NotImplementedError("Subclasses must implement from_db_model")
