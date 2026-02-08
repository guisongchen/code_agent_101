"""Pydantic schemas for Team CRD resources.

Team resources define multi-bot teams for collaborative task execution.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.kinds import KindType
from backend.schemas.base import BaseCRD, BaseSpec, Metadata, ResourceRef


class TeamMember(BaseModel):
    """Team member configuration.

    Defines a bot's role within a team.
    """

    model_config = ConfigDict(populate_by_name=True)

    bot_ref: ResourceRef = Field(
        ...,
        alias="botRef",
        description="Reference to the Bot resource",
    )
    role: str = Field(
        ...,
        description="Role of this bot in the team",
        examples=["leader", "worker", "reviewer", "specialist"],
    )
    priority: Optional[int] = Field(
        default=0,
        description="Execution priority (higher = earlier)",
    )


class TeamSpec(BaseSpec):
    """Specification for Team resources.

    Defines a team of bots for collaborative task execution.
    """

    model_config = ConfigDict(populate_by_name=True)

    members: List[TeamMember] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of bots in the team",
    )
    coordination_strategy: Optional[str] = Field(
        default="sequential",
        alias="coordinationStrategy",
        description="How bots coordinate (sequential, parallel, hierarchical)",
        examples=["sequential", "parallel", "hierarchical"],
    )
    shared_context: Optional[bool] = Field(
        default=True,
        alias="sharedContext",
        description="Whether bots share context/memory",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional team-specific metadata",
    )

    @field_validator("members")
    @classmethod
    def validate_members(cls, v: List[TeamMember]) -> List[TeamMember]:
        """Ensure all bot references point to Bot resources."""
        for member in v:
            if member.bot_ref.kind != KindType.BOT:
                raise ValueError(
                    f"Team members must reference Bot resources, got {member.bot_ref.kind}"
                )
        return v


class TeamCRD(BaseCRD):
    """Complete Team CRD schema.

    Represents a Team resource with all fields.
    """

    model_config = ConfigDict(populate_by_name=True)

    kind: KindType = KindType.TEAM
    spec: TeamSpec

    @classmethod
    def from_db_model(cls, db_model: Any) -> "TeamCRD":
        """Create TeamCRD from database Kind model.

        Args:
            db_model: Kind model instance with kind='team'.

        Returns:
            TeamCRD instance populated from database model.
        """
        spec_data = db_model.spec or {}

        # Convert nested dicts to TeamMember objects
        if "members" in spec_data and spec_data["members"]:
            members = []
            for m in spec_data["members"]:
                if "botRef" in m:
                    m["botRef"] = ResourceRef(**m["botRef"])
                members.append(TeamMember(**m))
            spec_data["members"] = members

        return cls(
            api_version=db_model.api_version,
            kind=KindType.TEAM,
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=TeamSpec(**spec_data),
        )


class TeamCreateRequest(BaseModel):
    """Request schema for creating a Team resource.

    Used in POST /api/v1/kinds/teams endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    metadata: Metadata = Field(
        ...,
        description="Team metadata (name, namespace)",
    )
    spec: TeamSpec = Field(
        ...,
        description="Team specification (members, coordination)",
    )


class TeamResponse(BaseModel):
    """Response schema for Team resources.

    Returned by API endpoints with full resource details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the team",
    )
    api_version: str = Field(
        default="v1",
        alias="apiVersion",
        description="API version",
    )
    kind: str = Field(
        default="team",
        description="Resource type",
    )
    metadata: Metadata = Field(
        ...,
        description="Team metadata",
    )
    spec: TeamSpec = Field(
        ...,
        description="Team specification",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "TeamResponse":
        """Create TeamResponse from database Kind model.

        Args:
            db_model: Kind model instance with kind='team'.

        Returns:
            TeamResponse instance populated from database model.
        """
        spec_data = db_model.spec or {}

        # Convert nested dicts to TeamMember objects
        if "members" in spec_data and spec_data["members"]:
            members = []
            for m in spec_data["members"]:
                if "botRef" in m:
                    m["botRef"] = ResourceRef(**m["botRef"])
                members.append(TeamMember(**m))
            spec_data["members"] = members

        return cls(
            id=db_model.id,
            api_version=db_model.api_version,
            kind="team",
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=TeamSpec(**spec_data),
        )
