"""Pydantic schemas for Ghost CRD resources.

Ghost resources define AI system prompts and personalities.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.models.kinds import KindType
from backend.schemas.base import BaseCRD, BaseSpec, Metadata


class GhostSpec(BaseSpec):
    """Specification for Ghost resources.

    Defines system prompts and personality configuration for AI agents.
    """

    model_config = ConfigDict(populate_by_name=True)

    system_prompt: str = Field(
        ...,
        alias="systemPrompt",
        min_length=1,
        description="System prompt that defines the AI's behavior and personality",
        examples=["You are a helpful coding assistant."],
    )
    context_window: Optional[int] = Field(
        default=None,
        alias="contextWindow",
        ge=1,
        description="Maximum context window size in tokens",
        examples=[4096, 8192, 32768],
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic, 2.0 = creative)",
        examples=[0.0, 0.7, 1.0],
    )
    tools_enabled: Optional[List[str]] = Field(
        default=None,
        alias="toolsEnabled",
        description="List of tool names enabled for this ghost",
        examples=[["file_reader", "web_search"]],
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional ghost-specific metadata",
        examples=[{"personality": "friendly", "expertise": "python"}],
    )


class GhostCRD(BaseCRD):
    """Complete Ghost CRD schema.

    Represents a Ghost resource with all fields.
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: KindType = KindType.GHOST
    spec: GhostSpec

    @classmethod
    def from_db_model(cls, db_model: Any) -> "GhostCRD":
        """Create GhostCRD from database Kind model.

        Args:
            db_model: Kind model instance with kind='ghost'.

        Returns:
            GhostCRD instance populated from database model.
        """
        spec_data = db_model.spec or {}
        return cls(
            api_version=db_model.api_version,
            kind=KindType.GHOST,
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=GhostSpec(**spec_data),
        )


class GhostCreateRequest(BaseModel):
    """Request schema for creating a Ghost resource.

    Used in POST /api/v1/kinds/ghosts endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    metadata: Metadata = Field(
        ...,
        description="Ghost metadata (name, namespace)",
    )
    spec: GhostSpec = Field(
        ...,
        description="Ghost specification (system prompt, configuration)",
    )


class GhostResponse(BaseModel):
    """Response schema for Ghost resources.

    Returned by API endpoints with full resource details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the ghost",
    )
    api_version: str = Field(
        default="v1",
        alias="apiVersion",
        description="API version",
    )
    kind: str = Field(
        default="ghost",
        description="Resource type",
    )
    metadata: Metadata = Field(
        ...,
        description="Ghost metadata",
    )
    spec: GhostSpec = Field(
        ...,
        description="Ghost specification",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "GhostResponse":
        """Create GhostResponse from database Kind model.

        Args:
            db_model: Kind model instance with kind='ghost'.

        Returns:
            GhostResponse instance populated from database model.
        """
        spec_data = db_model.spec or {}
        return cls(
            id=db_model.id,
            api_version=db_model.api_version,
            kind="ghost",
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=GhostSpec(**spec_data),
        )
