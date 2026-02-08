"""Unit tests for ShellService.

Tests: 6 tests covering ShellService CRUD operations
"""

import pytest
import pytest_asyncio

from backend.services.shell import ShellService
from backend.models.kinds import KindType
from backend.schemas.shell import ShellSpec, ShellCRD, Metadata


@pytest.mark.epic_9
@pytest.mark.unit
@pytest.mark.backend
class TestShellService:
    """Test suite for ShellService - 6 tests."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create ShellService instance."""
        return ShellService(async_session)

    async def test_create_shell(self, service, shell_schema):
        """Test creating a shell resource."""
        result = await service.create(shell_schema, created_by="test-user")

        assert result.metadata.name == "test-shell"
        assert result.spec.type == "chat"
        assert result.kind == KindType.SHELL

    async def test_get_shell(self, service, shell_schema):
        """Test retrieving a shell by name."""
        created = await service.create(shell_schema)
        result = await service.get("test-shell", "default")

        assert result is not None
        assert result.metadata.name == "test-shell"
        assert result.id == created.id

    async def test_list_shells(self, service, shell_schema):
        """Test listing shell resources."""
        await service.create(shell_schema)

        # Create another shell
        shell2 = ShellCRD(
            metadata=Metadata(name="code-shell", namespace="default"),
            spec=ShellSpec(type="code"),
        )
        await service.create(shell2)

        results = await service.list()
        assert len(results) == 2

    async def test_find_by_type(self, service, shell_schema):
        """Test finding shells by type."""
        await service.create(shell_schema)

        # Create code shell
        code_shell = ShellCRD(
            metadata=Metadata(name="code-runner", namespace="default"),
            spec=ShellSpec(type="code"),
        )
        await service.create(code_shell)

        chat_shells = await service.find_by_type("chat")
        assert len(chat_shells) == 1
        assert chat_shells[0].metadata.name == "test-shell"

    async def test_find_by_image(self, service):
        """Test finding shells by image."""
        # Create shell with specific image
        shell = ShellCRD(
            metadata=Metadata(name="python-shell", namespace="default"),
            spec=ShellSpec(type="code", image="python:3.11"),
        )
        await service.create(shell)

        python_shells = await service.find_by_image("python:3.11")
        assert len(python_shells) == 1
        assert python_shells[0].metadata.name == "python-shell"

    async def test_delete_shell(self, service, shell_schema):
        """Test soft deleting a shell resource."""
        await service.create(shell_schema)

        deleted = await service.delete("test-shell", "default")
        assert deleted is True

        result = await service.get("test-shell", "default")
        assert result is None
