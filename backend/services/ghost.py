"""Ghost resource service.

Provides CRUD operations for Ghost resources with Ghost-specific logic.
"""

from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kinds import Kind, KindType
from backend.schemas.ghost import GhostCRD, GhostResponse
from backend.services.base import CRDService


class GhostService(CRDService[GhostResponse]):
    """Service for Ghost resource management.

    Extends base CRUD service with Ghost-specific operations like
    searching by system prompt content.
    """

    kind_type = KindType.GHOST

    def _convert_to_schema(self, kind: Kind) -> GhostResponse:
        """Convert database Kind model to GhostResponse schema.

        Args:
            kind: Database Kind model with kind='ghost'.

        Returns:
            GhostResponse schema instance.
        """
        return GhostResponse.from_db_model(kind)

    async def find_by_system_prompt(
        self,
        prompt_substring: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[GhostResponse]:
        """Search ghosts by system prompt content.

        Args:
            prompt_substring: Substring to search for in system prompts.
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of GhostCRD schemas matching the search.
        """
        from backend.database.base import Base

        dialect = self.session.bind.dialect.name

        conditions = [
            Kind.kind == self.kind_type,
            Kind.deleted_at.is_(None),
        ]

        # JSON query depends on database dialect
        if dialect == "postgresql":
            # PostgreSQL JSONB query
            conditions.append(
                Kind.spec["systemPrompt"].astext.ilike(f"%{prompt_substring}%")
            )
        else:
            # SQLite JSON query - fetch all and filter in Python
            pass  # Will filter after fetching

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions))
        )
        kinds = result.scalars().all()

        # Convert to schemas and filter for SQLite
        ghosts = [self._convert_to_schema(k) for k in kinds]

        if dialect != "postgresql":
            # Filter in Python for SQLite
            ghosts = [
                g for g in ghosts
                if prompt_substring.lower() in g.spec.system_prompt.lower()
            ]

        return ghosts

    async def find_by_tools_enabled(
        self,
        tool_name: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[GhostResponse]:
        """Find ghosts that have a specific tool enabled.

        Args:
            tool_name: Name of the tool to search for.
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of GhostCRD schemas with the tool enabled.
        """
        dialect = self.session.bind.dialect.name

        conditions = [
            Kind.kind == self.kind_type,
            Kind.deleted_at.is_(None),
        ]

        # JSON query depends on database dialect
        if dialect == "postgresql":
            # PostgreSQL: check if tool_name is in the toolsEnabled array
            conditions.append(
                Kind.spec["toolsEnabled"].contains([tool_name])
            )
        else:
            # SQLite: will filter in Python
            pass

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions))
        )
        kinds = result.scalars().all()

        ghosts = [self._convert_to_schema(k) for k in kinds]

        if dialect != "postgresql":
            # Filter in Python for SQLite
            ghosts = [
                g for g in ghosts
                if g.spec.tools_enabled and tool_name in g.spec.tools_enabled
            ]

        return ghosts
