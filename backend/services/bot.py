"""Bot resource service.

Provides CRUD operations for Bot resources with reference validation.
"""

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kinds import Kind, KindType
from backend.schemas.bot import BotCRD, BotResponse
from backend.services.base import CRDService


class BotService(CRDService[BotResponse]):
    """Service for Bot resource management with reference validation.

    Extends base CRUD service with Bot-specific reference validation
    to ensure Ghost, Model, Shell, and Skill references exist.
    """

    kind_type = KindType.BOT

    def _convert_to_schema(self, kind: Kind) -> BotResponse:
        """Convert database Kind model to BotResponse schema.

        Args:
            kind: Database Kind model with kind='bot'.

        Returns:
            BotResponse schema instance.
        """
        return BotResponse.from_db_model(kind)

    async def create(
        self,
        schema: BotCRD,
        created_by: Optional[str] = None,
    ) -> BotResponse:
        """Create Bot with reference validation.

        Validates that all referenced resources (Ghost, Model, Shell, Skills)
        exist before creating the Bot.

        Args:
            schema: BotCRD schema to create.
            created_by: User creating the resource.

        Returns:
            Created BotCRD schema.

        Raises:
            ValueError: If any referenced resource doesn't exist or if
                a Bot with the same name/namespace already exists.
        """
        # Validate Ghost reference exists
        await self._validate_reference(
            schema.spec.ghost_ref.kind,
            schema.spec.ghost_ref.name,
            schema.spec.ghost_ref.namespace,
        )

        # Validate Model reference exists
        await self._validate_reference(
            schema.spec.model_ref.kind,
            schema.spec.model_ref.name,
            schema.spec.model_ref.namespace,
        )

        # Validate Shell reference exists
        await self._validate_reference(
            schema.spec.shell_ref.kind,
            schema.spec.shell_ref.name,
            schema.spec.shell_ref.namespace,
        )

        # Validate Skills if provided
        if schema.spec.skills:
            for skill_ref in schema.spec.skills:
                await self._validate_reference(
                    skill_ref.kind,
                    skill_ref.name,
                    skill_ref.namespace,
                )

        return await super().create(schema, created_by)

    async def _validate_reference(
        self,
        kind: KindType,
        name: str,
        namespace: str,
    ) -> None:
        """Validate that a referenced resource exists.

        Args:
            kind: Resource kind type.
            name: Resource name.
            namespace: Resource namespace.

        Raises:
            ValueError: If the referenced resource doesn't exist.
        """
        result = await self.session.execute(
            select(Kind).where(
                and_(
                    Kind.kind == kind,
                    Kind.name == name,
                    Kind.namespace == namespace,
                    Kind.deleted_at.is_(None),
                )
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError(
                f"Referenced resource not found: {kind.value}/{namespace}/{name}"
            )
