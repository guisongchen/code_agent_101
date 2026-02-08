"""Pydantic schemas for Shell CRD resources.

Shell resources define runtime environments for executing tasks.
"""

from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.models.kinds import KindType
from backend.schemas.base import BaseCRD, BaseSpec, Metadata


class EnvironmentVariable(BaseModel):
    """Environment variable configuration.

    Defines a single environment variable with optional secret handling.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...,
        description="Environment variable name",
        examples=["API_KEY", "DATABASE_URL"],
    )
    value: Optional[str] = Field(
        default=None,
        description="Environment variable value (omit if using secretRef)",
    )
    secret_ref: Optional[str] = Field(
        default=None,
        alias="secretRef",
        description="Reference to a secret containing the value",
    )


class ResourceLimits(BaseModel):
    """Resource limits for shell execution.

    Defines CPU, memory, and other resource constraints.
    """

    model_config = ConfigDict(populate_by_name=True)

    cpu: Optional[str] = Field(
        default=None,
        description="CPU limit (e.g., '500m' for 0.5 cores, '2' for 2 cores)",
        examples=["500m", "1", "2"],
    )
    memory: Optional[str] = Field(
        default=None,
        description="Memory limit (e.g., '512Mi', '2Gi')",
        examples=["512Mi", "1Gi", "4Gi"],
    )
    timeout: Optional[int] = Field(
        default=300,
        ge=1,
        le=3600,
        description="Execution timeout in seconds",
    )


class ShellSpec(BaseSpec):
    """Specification for Shell resources.

    Defines runtime environment configuration for executing tasks.
    """

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["chat", "code", "notebook"] = Field(
        default="chat",
        description="Shell type (chat, code, or notebook)",
    )
    image: Optional[str] = Field(
        default=None,
        description="Container image or runtime environment identifier",
        examples=["python:3.11", "node:18-alpine"],
    )
    command: Optional[List[str]] = Field(
        default=None,
        description="Default command to execute",
        examples=[["python", "-u"], ["node"]],
    )
    working_dir: Optional[str] = Field(
        default=None,
        alias="workingDir",
        description="Working directory for execution",
        examples=["/workspace", "/app"],
    )
    env: Optional[List[EnvironmentVariable]] = Field(
        default=None,
        description="Environment variables",
    )
    resources: Optional[ResourceLimits] = Field(
        default=None,
        description="Resource limits",
    )
    allowed_tools: Optional[List[str]] = Field(
        default=None,
        alias="allowedTools",
        description="List of tools allowed in this shell",
        examples=[["file_reader", "web_search", "code_executor"]],
    )
    network_access: Optional[bool] = Field(
        default=True,
        alias="networkAccess",
        description="Whether network access is allowed",
    )
    persistent_storage: Optional[bool] = Field(
        default=False,
        alias="persistentStorage",
        description="Whether to persist storage between sessions",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional shell-specific metadata",
    )


class ShellCRD(BaseCRD):
    """Complete Shell CRD schema.

    Represents a Shell resource with all fields.
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: KindType = KindType.SHELL
    spec: ShellSpec

    @classmethod
    def from_db_model(cls, db_model: Any) -> "ShellCRD":
        """Create ShellCRD from database Kind model.

        Args:
            db_model: Kind model instance with kind='shell'.

        Returns:
            ShellCRD instance populated from database model.
        """
        spec_data = db_model.spec or {}
        return cls(
            api_version=db_model.api_version,
            kind=KindType.SHELL,
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=ShellSpec(**spec_data),
        )


class ShellCreateRequest(BaseModel):
    """Request schema for creating a Shell resource.

    Used in POST /api/v1/kinds/shells endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    metadata: Metadata = Field(
        ...,
        description="Shell metadata (name, namespace)",
    )
    spec: ShellSpec = Field(
        ...,
        description="Shell specification (runtime configuration)",
    )


class ShellResponse(BaseModel):
    """Response schema for Shell resources.

    Returned by API endpoints with full resource details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the shell",
    )
    api_version: str = Field(
        default="v1",
        alias="apiVersion",
        description="API version",
    )
    kind: str = Field(
        default="shell",
        description="Resource type",
    )
    metadata: Metadata = Field(
        ...,
        description="Shell metadata",
    )
    spec: ShellSpec = Field(
        ...,
        description="Shell specification",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "ShellResponse":
        """Create ShellResponse from database Kind model.

        Args:
            db_model: Kind model instance with kind='shell'.

        Returns:
            ShellResponse instance populated from database model.
        """
        spec_data = db_model.spec or {}
        return cls(
            id=db_model.id,
            api_version=db_model.api_version,
            kind="shell",
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=ShellSpec(**spec_data),
        )
