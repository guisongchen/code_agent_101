"""Model resource service.

Provides CRUD operations for Model resources with Model-specific logic.
"""

from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kinds import Kind, KindType
from backend.schemas.model import ModelResponse
from backend.services.base import CRDService


class ModelService(CRDService[ModelResponse]):
    """Service for Model resource management.

    Extends base CRUD service with Model-specific operations like
    finding models by provider or capability.
    """

    kind_type = KindType.MODEL

    def _convert_to_schema(self, kind: Kind) -> ModelResponse:
        """Convert database Kind model to ModelCRD schema.

        Args:
            kind: Database Kind model with kind='model'.

        Returns:
            ModelResponse schema instance.
        """
        return ModelResponse.from_db_model(kind)

    async def find_by_provider(
        self,
        provider: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[ModelResponse]:
        """Find models by provider (openai, anthropic, etc.).

        Args:
            provider: Model provider name.
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of ModelResponse schemas from the provider.
        """
        dialect = self.session.bind.dialect.name

        conditions = [
            Kind.kind == self.kind_type,
            Kind.deleted_at.is_(None),
        ]

        if dialect == "postgresql":
            conditions.append(
                Kind.spec["config"]["provider"].astext == provider
            )

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions))
        )
        kinds = result.scalars().all()

        models = [self._convert_to_schema(k) for k in kinds]

        if dialect != "postgresql":
            models = [
                m for m in models
                if m.spec.config.provider == provider
            ]

        return models

    async def find_by_capability(
        self,
        capability: str,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
    ) -> List[ModelResponse]:
        """Find models that support a specific capability.

        Args:
            capability: Capability to search for (chat, vision, etc.).
            namespace: Filter by namespace.
            include_all_namespaces: If True, search across all namespaces.

        Returns:
            List of ModelResponse schemas with the capability.
        """
        dialect = self.session.bind.dialect.name

        conditions = [
            Kind.kind == self.kind_type,
            Kind.deleted_at.is_(None),
        ]

        if dialect == "postgresql":
            conditions.append(
                Kind.spec["capabilities"].contains([capability])
            )

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions))
        )
        kinds = result.scalars().all()

        models = [self._convert_to_schema(k) for k in kinds]

        if dialect != "postgresql":
            models = [
                m for m in models
                if m.spec.capabilities and capability in m.spec.capabilities
            ]

        return models
