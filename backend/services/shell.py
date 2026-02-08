"""Shell resource service.

Provides CRUD operations for Shell resources with Shell-specific logic.
"""

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kinds import Kind, KindType
from backend.schemas.shell import ShellResponse
from backend.services.base import CRDService


class ShellService(CRDService[ShellResponse]):
    """Service for Shell resource management.

    Extends base CRUD service with Shell-specific operations like
    finding shells by type or image.
    """

    kind_type = KindType.SHELL

    def _convert_to_schema(self, kind: Kind) -> ShellResponse:
        """Convert database Kind model to ShellResponse schema.

        Args:
            kind: Database Kind model with kind='shell'.

        Returns:
            ShellResponse schema instance.
        """
        return ShellResponse.from_db_model(kind)

    async def find_by_type(
        self,
        shell_type: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[ShellResponse]:
        """Find shells by type (chat, code, notebook).

        Args:
            shell_type: Shell type to search for.
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of ShellCRD schemas of the specified type.
        """
        dialect = self.session.bind.dialect.name

        conditions = [
            Kind.kind == self.kind_type,
            Kind.deleted_at.is_(None),
        ]

        if dialect == "postgresql":
            conditions.append(
                Kind.spec["type"].astext == shell_type
            )

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions))
        )
        kinds = result.scalars().all()

        shells = [self._convert_to_schema(k) for k in kinds]

        if dialect != "postgresql":
            shells = [
                s for s in shells
                if s.spec.type == shell_type
            ]

        return shells

    async def find_by_image(
        self,
        image: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[ShellResponse]:
        """Find shells by container image.

        Args:
            image: Container image name (e.g., 'python:3.11').
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of ShellResponse schemas using the image.
        """
        dialect = self.session.bind.dialect.name

        conditions = [
            Kind.kind == self.kind_type,
            Kind.deleted_at.is_(None),
        ]

        if dialect == "postgresql":
            conditions.append(
                Kind.spec["image"].astext == image
            )

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions))
        )
        kinds = result.scalars().all()

        shells = [self._convert_to_schema(k) for k in kinds]

        if dialect != "postgresql":
            shells = [
                s for s in shells
                if s.spec.image == image
            ]

        return shells
