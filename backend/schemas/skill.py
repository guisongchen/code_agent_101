"""Pydantic schemas for Skill CRD resources.

Skill resources define reusable capabilities that can be attached to bots.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.kinds import KindType
from backend.schemas.base import BaseCRD, BaseSpec, Metadata


class ToolDefinition(BaseModel):
    """Definition of a tool provided by a skill.

    Follows OpenAI function calling format.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...,
        description="Tool name",
        examples=["file_reader", "web_search"],
    )
    description: str = Field(
        ...,
        description="Human-readable description of what the tool does",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for tool parameters",
    )


class SkillSpec(BaseSpec):
    """Specification for Skill resources.

    Defines reusable capabilities that can be attached to bots.
    """

    model_config = ConfigDict(populate_by_name=True)

    version: str = Field(
        default="1.0.0",
        description="Skill version (semver)",
        examples=["1.0.0", "2.1.0"],
    )
    author: Optional[str] = Field(
        default=None,
        description="Skill author or maintainer",
    )
    tools: Optional[List[ToolDefinition]] = Field(
        default=None,
        description="Tools provided by this skill",
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="Other skills this skill depends on",
        examples=[["core", "file_ops"]],
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="configSchema",
        description="JSON Schema for skill configuration",
    )
    default_config: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="defaultConfig",
        description="Default configuration values",
    )
    entry_point: Optional[str] = Field(
        default=None,
        alias="entryPoint",
        description="Python module entry point for the skill",
        examples=["my_skill.main"],
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional skill-specific metadata",
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version follows semver format."""
        import re

        if not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$", v):
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        return v


class SkillCRD(BaseCRD):
    """Complete Skill CRD schema.

    Represents a Skill resource with all fields.
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: KindType = KindType.SKILL
    spec: SkillSpec

    @classmethod
    def from_db_model(cls, db_model: Any) -> "SkillCRD":
        """Create SkillCRD from database Kind model.

        Args:
            db_model: Kind model instance with kind='skill'.

        Returns:
            SkillCRD instance populated from database model.
        """
        spec_data = db_model.spec or {}

        # Convert tools to ToolDefinition objects
        if "tools" in spec_data and spec_data["tools"]:
            spec_data["tools"] = [ToolDefinition(**t) for t in spec_data["tools"]]

        return cls(
            api_version=db_model.api_version,
            kind=KindType.SKILL,
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=SkillSpec(**spec_data),
        )


class SkillCreateRequest(BaseModel):
    """Request schema for creating a Skill resource.

    Used in POST /api/v1/kinds/skills endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    metadata: Metadata = Field(
        ...,
        description="Skill metadata (name, namespace)",
    )
    spec: SkillSpec = Field(
        ...,
        description="Skill specification (tools, configuration)",
    )


class SkillResponse(BaseModel):
    """Response schema for Skill resources.

    Returned by API endpoints with full resource details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the skill",
    )
    api_version: str = Field(
        default="v1",
        alias="apiVersion",
        description="API version",
    )
    kind: str = Field(
        default="skill",
        description="Resource type",
    )
    metadata: Metadata = Field(
        ...,
        description="Skill metadata",
    )
    spec: SkillSpec = Field(
        ...,
        description="Skill specification",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "SkillResponse":
        """Create SkillResponse from database Kind model.

        Args:
            db_model: Kind model instance with kind='skill'.

        Returns:
            SkillResponse instance populated from database model.
        """
        spec_data = db_model.spec or {}

        # Convert tools to ToolDefinition objects
        if "tools" in spec_data and spec_data["tools"]:
            spec_data["tools"] = [ToolDefinition(**t) for t in spec_data["tools"]]

        return cls(
            id=db_model.id,
            api_version=db_model.api_version,
            kind="skill",
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=SkillSpec(**spec_data),
        )
