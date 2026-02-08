"""Unit tests for GhostService.

Tests: 6 tests covering GhostService CRUD operations
"""

import pytest
import pytest_asyncio

from backend.services.ghost import GhostService
from backend.models.kinds import KindType


@pytest.mark.epic_9
@pytest.mark.unit
@pytest.mark.backend
class TestGhostService:
    """Test suite for GhostService - 6 tests."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create GhostService instance."""
        return GhostService(async_session)

    async def test_create_ghost(self, service, ghost_schema):
        """Test creating a ghost resource."""
        result = await service.create(ghost_schema, created_by="test-user")

        assert result.metadata.name == "test-ghost"
        assert result.spec.system_prompt == "You are a helpful assistant."
        assert result.kind == KindType.GHOST

    async def test_get_ghost(self, service, ghost_schema):
        """Test retrieving a ghost by name."""
        created = await service.create(ghost_schema)
        result = await service.get("test-ghost", "default")

        assert result is not None
        assert result.metadata.name == "test-ghost"
        assert result.id == created.id

    async def test_get_nonexistent_ghost(self, service):
        """Test retrieving a non-existent ghost returns None."""
        result = await service.get("nonexistent", "default")
        assert result is None

    async def test_list_ghosts(self, service, ghost_schema):
        """Test listing ghost resources."""
        await service.create(ghost_schema)

        # Create another ghost
        from backend.schemas.ghost import GhostCRD, GhostSpec, Metadata
        ghost2 = GhostCRD(
            metadata=Metadata(name="another-ghost", namespace="default"),
            spec=GhostSpec(system_prompt="Another ghost."),
        )
        await service.create(ghost2)

        results = await service.list()
        assert len(results) == 2

    async def test_delete_ghost(self, service, ghost_schema):
        """Test soft deleting a ghost resource."""
        await service.create(ghost_schema)

        deleted = await service.delete("test-ghost", "default")
        assert deleted is True

        # Should not be found after deletion
        result = await service.get("test-ghost", "default")
        assert result is None

    async def test_create_duplicate_ghost(self, service, ghost_schema):
        """Test creating duplicate ghost raises error."""
        await service.create(ghost_schema)

        with pytest.raises(ValueError, match="already exists"):
            await service.create(ghost_schema)
