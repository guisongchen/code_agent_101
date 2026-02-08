"""Pydantic schemas for Bot CRD resources.

Bot resources define AI agents that combine Ghost, Model, and Shell configurations.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.models.kinds import KindType
from backend.schemas.base import BaseCRD, BaseSpec, Metadata, ResourceRef


class BotSpec(BaseSpec):
    """Specification for Bot resources.

    Defines AI agent configuration by referencing Ghost, Model, and Shell resources.
    """

    model_config = ConfigDict(populate_by_name=True)

    ghost_ref: ResourceRef = Field(
        ...,
        alias="ghostRef",
        description="Reference to the Ghost resource (system prompt/personality)",
    )
    model_ref: ResourceRef = Field(
        ...,
        alias="modelRef",
        description="Reference to the Model resource (AI model configuration)",
    )
    shell_ref: ResourceRef = Field(
        ...,
        alias="shellRef",
        description="Reference to the Shell resource (runtime environment)",
    )
    skills: Optional[List[ResourceRef]] = Field(
        default=None,
        description="List of Skill references to enable for this bot",
    )
    auto_invoke_tools: Optional[bool] = Field(
        default=True,
        alias="autoInvokeTools",
        description="Whether to automatically invoke tools without confirmation",
    )
    max_iterations: Optional[int] = Field(
        default=10,
        alias="maxIterations",
        ge=1,
        le=100,
        description="Maximum number of tool invocation iterations per request",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional bot-specific metadata",
    )

    @field_validator("ghost_ref")
    @classmethod
    def validate_ghost_ref(cls, v: ResourceRef) -> ResourceRef:
        """Ensure ghost_ref points to a Ghost resource."""
        if v.kind != KindType.GHOST:
            raise ValueError(f"ghostRef must reference a Ghost resource, got {v.kind}")
        return v

    @field_validator("model_ref")
    @classmethod
    def validate_model_ref(cls, v: ResourceRef) -> ResourceRef:
        """Ensure model_ref points to a Model resource."""
        if v.kind != KindType.MODEL:
            raise ValueError(f"modelRef must reference a Model resource, got {v.kind}")
        return v

    @field_validator("shell_ref")
    @classmethod
    def validate_shell_ref(cls, v: ResourceRef) -> ResourceRef:
        """Ensure shell_ref points to a Shell resource."""
        if v.kind != KindType.SHELL:
            raise ValueError(f"shellRef must reference a Shell resource, got {v.kind}")
        return v

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: Optional[List[ResourceRef]]) -> Optional[List[ResourceRef]]:
        """Ensure all skill references point to Skill resources."""
        if v is None:
            return v
        for skill_ref in v:
            if skill_ref.kind != KindType.SKILL:
                raise ValueError(f"skills must reference Skill resources, got {skill_ref.kind}")
        return v


class BotCRD(BaseCRD):
    """Complete Bot CRD schema.

    Represents a Bot resource with all fields.
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: KindType = KindType.BOT
    spec: BotSpec

    @classmethod
    def from_db_model(cls, db_model: Any) -> "BotCRD":
        """Create BotCRD from database Kind model.

        Args:
            db_model: Kind model instance with kind='bot'.

        Returns:
            BotCRD instance populated from database model.
        """
        spec_data = db_model.spec or {}

        # Convert nested dicts to ResourceRef objects
        if "ghostRef" in spec_data:
            spec_data["ghostRef"] = ResourceRef(**spec_data["ghostRef"])
        if "modelRef" in spec_data:
            spec_data["modelRef"] = ResourceRef(**spec_data["modelRef"])
        if "shellRef" in spec_data:
            spec_data["shellRef"] = ResourceRef(**spec_data["shellRef"])
        if "skills" in spec_data and spec_data["skills"]:
            spec_data["skills"] = [ResourceRef(**s) for s in spec_data["skills"]]

        return cls(
            api_version=db_model.api_version,
            kind=KindType.BOT,
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=BotSpec(**spec_data),
        )


class BotCreateRequest(BaseModel):
    """Request schema for creating a Bot resource.

    Used in POST /api/v1/kinds/bots endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    metadata: Metadata = Field(
        ...,
        description="Bot metadata (name, namespace)",
    )
    spec: BotSpec = Field(
        ...,
        description="Bot specification (Ghost, Model, Shell references)",
    )


class BotResponse(BaseModel):
    """Response schema for Bot resources.

    Returned by API endpoints with full resource details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the bot",
    )
    api_version: str = Field(
        default="v1",
        alias="apiVersion",
        description="API version",
    )
    kind: str = Field(
        default="bot",
        description="Resource type",
    )
    metadata: Metadata = Field(
        ...,
        description="Bot metadata",
    )
    spec: BotSpec = Field(
        ...,
        description="Bot specification",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "BotResponse":
        """Create BotResponse from database Kind model.

        Args:
            db_model: Kind model instance with kind='bot'.

        Returns:
            BotResponse instance populated from database model.
        """
        spec_data = db_model.spec or {}

        # Convert nested dicts to ResourceRef objects
        if "ghostRef" in spec_data:
            spec_data["ghostRef"] = ResourceRef(**spec_data["ghostRef"])
        if "modelRef" in spec_data:
            spec_data["modelRef"] = ResourceRef(**spec_data["modelRef"])
        if "shellRef" in spec_data:
            spec_data["shellRef"] = ResourceRef(**spec_data["shellRef"])
        if "skills" in spec_data and spec_data["skills"]:
            spec_data["skills"] = [ResourceRef(**s) for s in spec_data["skills"]]

        return cls(
            id=db_model.id,
            api_version=db_model.api_version,
            kind="bot",
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=BotSpec(**spec_data),
        )
