"""Skill resource service.

Provides CRUD operations for Skill resources with Skill-specific logic.
"""

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kinds import Kind, KindType
from backend.schemas.skill import SkillCRD, SkillResponse
from backend.services.base import CRDService


class SkillService(CRDService[SkillResponse]):
    """Service for Skill resource management.

    Extends base CRUD service with Skill-specific operations like
    finding skills by tool name or author.
    """

    kind_type = KindType.SKILL

    def _convert_to_schema(self, kind: Kind) -> SkillResponse:
        """Convert database Kind model to SkillResponse schema.

        Args:
            kind: Database Kind model with kind='skill'.

        Returns:
            SkillResponse schema instance.
        """
        return SkillResponse.from_db_model(kind)

    async def find_by_author(
        self,
        author: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[SkillResponse]:
        """Find skills by author.

        Args:
            author: Skill author name.
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of SkillCRD schemas by the author.
        """
        dialect = self.session.bind.dialect.name

        conditions = [
            Kind.kind == self.kind_type,
            Kind.deleted_at.is_(None),
        ]

        if dialect == "postgresql":
            conditions.append(
                Kind.spec["author"].astext == author
            )

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions))
        )
        kinds = result.scalars().all()

        skills = [self._convert_to_schema(k) for k in kinds]

        if dialect != "postgresql":
            skills = [
                s for s in skills
                if s.spec.author == author
            ]

        return skills

    async def find_by_tool_name(
        self,
        tool_name: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[SkillResponse]:
        """Find skills that provide a specific tool.

        Args:
            tool_name: Name of the tool to search for.
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of SkillCRD schemas providing the tool.
        """
        # Fetch all skills and filter in Python due to nested JSON structure
        skills = await self.list(
            namespace=namespace,
            include_all_namespaces=include_all_namespaces,
        )

        matching_skills = []
        for skill in skills:
            if skill.spec.tools:
                for tool in skill.spec.tools:
                    if tool.name == tool_name:
                        matching_skills.append(skill)
                        break

        return matching_skills
