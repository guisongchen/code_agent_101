"""Generic CRUD service base class for CRD resources.

Provides common CRUD operations for all CRD types with type safety.
"""

from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kinds import Kind, KindType

T = TypeVar("T", bound=BaseModel)


class CRDService(Generic[T]):
    """Generic CRUD service for CRD resources.

    Provides common operations: get, list, create, delete (soft).
    Subclasses must define kind_type and implement _convert_to_schema().

    Example:
        class GhostService(CRDService[GhostCRD]):
            kind_type = KindType.GHOST

            def _convert_to_schema(self, kind: Kind) -> GhostCRD:
                return GhostCRD.from_db_model(kind)
    """

    kind_type: KindType = None  # Override in subclass

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session for database operations.
        """
        self.session = session

    async def get(
        self,
        name: str,
        namespace: str = "default",
        include_deleted: bool = False,
    ) -> Optional[T]:
        """Get a resource by name and namespace.

        Args:
            name: Resource name.
            namespace: Resource namespace (default: "default").
            include_deleted: Whether to include soft-deleted resources.

        Returns:
            Resource schema if found, None otherwise.
        """
        conditions = [
            Kind.kind == self.kind_type,
            Kind.name == name,
            Kind.namespace == namespace,
        ]

        if not include_deleted:
            conditions.append(Kind.deleted_at.is_(None))

        result = await self.session.execute(select(Kind).where(and_(*conditions)))
        kind = result.scalar_one_or_none()

        return self._convert_to_schema(kind) if kind else None

    async def get_by_id(
        self,
        resource_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[T]:
        """Get a resource by ID.

        Args:
            resource_id: Resource UUID.
            include_deleted: Whether to include soft-deleted resources.

        Returns:
            Resource schema if found, None otherwise.
        """
        conditions = [
            Kind.id == resource_id,
            Kind.kind == self.kind_type,
        ]

        if not include_deleted:
            conditions.append(Kind.deleted_at.is_(None))

        result = await self.session.execute(select(Kind).where(and_(*conditions)))
        kind = result.scalar_one_or_none()

        return self._convert_to_schema(kind) if kind else None

    async def list(
        self,
        namespace: Optional[str] = "default",
        include_all_namespaces: bool = False,
        include_deleted: bool = False,
    ) -> List[T]:
        """List resources with optional filtering.

        Args:
            namespace: Filter by namespace (ignored if include_all_namespaces=True).
            include_all_namespaces: If True, list resources from all namespaces.
            include_deleted: Whether to include soft-deleted resources.

        Returns:
            List of resource schemas.
        """
        conditions = [
            Kind.kind == self.kind_type,
        ]

        if not include_deleted:
            conditions.append(Kind.deleted_at.is_(None))

        if not include_all_namespaces and namespace is not None:
            conditions.append(Kind.namespace == namespace)

        result = await self.session.execute(
            select(Kind).where(and_(*conditions)).order_by(Kind.created_at.desc())
        )
        kinds = result.scalars().all()

        return [self._convert_to_schema(k) for k in kinds]

    async def create(
        self,
        schema: T,
        created_by: Optional[str] = None,
    ) -> T:
        """Create a new resource.

        Args:
            schema: Resource schema to create.
            created_by: User creating the resource.

        Returns:
            Created resource schema with ID and timestamps.

        Raises:
            ValueError: If resource with same name/namespace already exists.
        """
        # Check for existing resource (kind, name, namespace) conflict
        existing = await self.get(schema.metadata.name, schema.metadata.namespace)
        if existing:
            raise ValueError(
                f"{self.kind_type.value} '{schema.metadata.name}' already exists "
                f"in namespace '{schema.metadata.namespace}'"
            )

        # Convert schema to DB model
        db_data = schema.to_db_dict()
        db_data["created_by"] = created_by

        kind = Kind(**db_data)
        self.session.add(kind)
        await self.session.flush()  # Get the ID without committing
        await self.session.refresh(kind)  # Refresh to get timestamps

        return self._convert_to_schema(kind)

    async def delete(
        self,
        name: str,
        namespace: str = "default",
    ) -> bool:
        """Soft delete a resource.

        Args:
            name: Resource name.
            namespace: Resource namespace.

        Returns:
            True if resource was deleted, False if not found.
        """
        result = await self.session.execute(
            select(Kind).where(
                and_(
                    Kind.kind == self.kind_type,
                    Kind.name == name,
                    Kind.namespace == namespace,
                    Kind.deleted_at.is_(None),
                )
            )
        )
        kind = result.scalar_one_or_none()

        if not kind:
            return False

        kind.soft_delete()
        return True

    async def exists(
        self,
        name: str,
        namespace: str = "default",
        include_deleted: bool = False,
    ) -> bool:
        """Check if a resource exists.

        Args:
            name: Resource name.
            namespace: Resource namespace.
            include_deleted: Whether to include soft-deleted resources.

        Returns:
            True if resource exists, False otherwise.
        """
        resource = await self.get(name, namespace, include_deleted)
        return resource is not None

    def _convert_to_schema(self, kind: Kind) -> T:
        """Convert database Kind model to Pydantic schema.

        Args:
            kind: Database Kind model.

        Returns:
            Pydantic schema instance.

        Raises:
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement _convert_to_schema")
