"""Team resource service.

Provides CRUD operations for Team resources with member validation.
"""

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kinds import Kind, KindType
from backend.schemas.base import ResourceRef
from backend.schemas.team import TeamCRD, TeamResponse
from backend.services.base import CRDService


class TeamService(CRDService[TeamResponse]):
    """Service for Team resource management with member validation.

    Extends base CRUD service with Team-specific member validation
    to ensure all referenced Bots exist.
    """

    kind_type = KindType.TEAM

    def _convert_to_schema(self, kind: Kind) -> TeamResponse:
        """Convert database Kind model to TeamResponse schema.

        Args:
            kind: Database Kind model with kind='team'.

        Returns:
            TeamResponse schema instance.
        """
        return TeamResponse.from_db_model(kind)

    async def create(
        self,
        schema: TeamCRD,
        created_by: Optional[str] = None,
    ) -> TeamResponse:
        """Create Team with member validation.

        Validates that all referenced Bot members exist before creating the Team.

        Args:
            schema: TeamCRD schema to create.
            created_by: User creating the resource.

        Returns:
            Created TeamCRD schema.

        Raises:
            ValueError: If any referenced Bot doesn't exist or if
                a Team with the same name/namespace already exists.
        """
        # Validate all bot references exist
        for member in schema.spec.members:
            await self._validate_bot_reference(member.bot_ref)

        return await super().create(schema, created_by)

    async def _validate_bot_reference(
        self,
        bot_ref: ResourceRef,
    ) -> None:
        """Validate that a referenced Bot exists.

        Args:
            bot_ref: Bot resource reference.

        Raises:
            ValueError: If the referenced Bot doesn't exist.
        """
        result = await self.session.execute(
            select(Kind).where(
                and_(
                    Kind.kind == bot_ref.kind,
                    Kind.name == bot_ref.name,
                    Kind.namespace == bot_ref.namespace,
                    Kind.deleted_at.is_(None),
                )
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError(
                f"Referenced Bot not found: {bot_ref.kind.value}/"
                f"{bot_ref.namespace}/{bot_ref.name}"
            )

    async def find_by_bot(
        self,
        bot_name: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[TeamResponse]:
        """Find teams that contain a specific bot.

        Args:
            bot_name: Name of the bot to search for.
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of TeamCRD schemas containing the bot.
        """
        # Fetch all teams and filter in Python due to JSON structure
        teams = await self.list(
            namespace=namespace,
            include_all_namespaces=include_all_namespaces,
        )

        matching_teams = []
        for team in teams:
            for member in team.spec.members:
                if member.bot_ref.name == bot_name:
                    matching_teams.append(team)
                    break

        return matching_teams
