"""Unit tests for BotService.

Tests: 8 tests covering BotService CRUD and reference validation
"""

import pytest
import pytest_asyncio

from backend.services.bot import BotService
from backend.services.ghost import GhostService
from backend.services.model import ModelService
from backend.services.shell import ShellService
from backend.models.kinds import KindType
from backend.schemas.bot import BotSpec, BotCRD, Metadata
from backend.schemas.base import ResourceRef


@pytest.mark.epic_9
@pytest.mark.unit
@pytest.mark.backend
class TestBotService:
    """Test suite for BotService - 8 tests."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create BotService instance."""
        return BotService(async_session)

    async def test_create_bot_with_valid_refs(
        self, service, async_session, ghost_schema, model_schema, shell_schema
    ):
        """Test creating a bot with valid references."""
        # Create dependencies first
        ghost_service = GhostService(async_session)
        model_service = ModelService(async_session)
        shell_service = ShellService(async_session)

        await ghost_service.create(ghost_schema)
        await model_service.create(model_schema)
        await shell_service.create(shell_schema)

        # Now create bot
        bot = BotCRD(
            metadata=Metadata(name="test-bot", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(
                    kind=KindType.GHOST,
                    name=ghost_schema.metadata.name,
                    namespace="default",
                ),
                model_ref=ResourceRef(
                    kind=KindType.MODEL,
                    name=model_schema.metadata.name,
                    namespace="default",
                ),
                shell_ref=ResourceRef(
                    kind=KindType.SHELL,
                    name=shell_schema.metadata.name,
                    namespace="default",
                ),
            ),
        )

        result = await service.create(bot)
        assert result.metadata.name == "test-bot"
        assert result.spec.ghost_ref.name == ghost_schema.metadata.name

    async def test_create_bot_with_invalid_ghost_ref(self, service):
        """Test creating bot with non-existent ghost reference fails."""
        from backend.schemas.ghost import GhostSpec, GhostCRD

        bot = BotCRD(
            metadata=Metadata(name="test-bot", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(
                    kind=KindType.GHOST,
                    name="nonexistent-ghost",
                    namespace="default",
                ),
                model_ref=ResourceRef(
                    kind=KindType.MODEL,
                    name="nonexistent-model",
                    namespace="default",
                ),
                shell_ref=ResourceRef(
                    kind=KindType.SHELL,
                    name="nonexistent-shell",
                    namespace="default",
                ),
            ),
        )

        with pytest.raises(ValueError, match="Referenced resource not found"):
            await service.create(bot)

    async def test_create_bot_with_skills(
        self, service, async_session, ghost_schema, model_schema, shell_schema
    ):
        """Test creating bot with skill references."""
        from backend.services.skill import SkillService
        from backend.schemas.skill import SkillSpec, SkillCRD

        # Create dependencies
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        # Create a skill
        skill = SkillCRD(
            metadata=Metadata(name="file-reader", namespace="default"),
            spec=SkillSpec(),
        )
        await SkillService(async_session).create(skill)

        # Create bot with skill
        bot = BotCRD(
            metadata=Metadata(name="skilled-bot", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(
                    kind=KindType.GHOST,
                    name=ghost_schema.metadata.name,
                    namespace="default",
                ),
                model_ref=ResourceRef(
                    kind=KindType.MODEL,
                    name=model_schema.metadata.name,
                    namespace="default",
                ),
                shell_ref=ResourceRef(
                    kind=KindType.SHELL,
                    name=shell_schema.metadata.name,
                    namespace="default",
                ),
                skills=[
                    ResourceRef(
                        kind=KindType.SKILL,
                        name="file-reader",
                        namespace="default",
                    ),
                ],
            ),
        )

        result = await service.create(bot)
        assert len(result.spec.skills) == 1
        assert result.spec.skills[0].name == "file-reader"

    async def test_get_bot(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test retrieving a bot by name."""
        # Setup
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        bot = BotCRD(
            metadata=Metadata(name="test-bot", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(
                    kind=KindType.GHOST,
                    name=ghost_schema.metadata.name,
                    namespace="default",
                ),
                model_ref=ResourceRef(
                    kind=KindType.MODEL,
                    name=model_schema.metadata.name,
                    namespace="default",
                ),
                shell_ref=ResourceRef(
                    kind=KindType.SHELL,
                    name=shell_schema.metadata.name,
                    namespace="default",
                ),
            ),
        )
        created = await service.create(bot)

        result = await service.get("test-bot", "default")
        assert result is not None
        assert result.id == created.id

    async def test_list_bots(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test listing bot resources."""
        # Setup
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        bot1 = BotCRD(
            metadata=Metadata(name="bot-1", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name=ghost_schema.metadata.name, namespace="default"),
                model_ref=ResourceRef(kind=KindType.MODEL, name=model_schema.metadata.name, namespace="default"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name=shell_schema.metadata.name, namespace="default"),
            ),
        )
        bot2 = BotCRD(
            metadata=Metadata(name="bot-2", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name=ghost_schema.metadata.name, namespace="default"),
                model_ref=ResourceRef(kind=KindType.MODEL, name=model_schema.metadata.name, namespace="default"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name=shell_schema.metadata.name, namespace="default"),
            ),
        )

        await service.create(bot1)
        await service.create(bot2)

        results = await service.list()
        assert len(results) == 2

    async def test_delete_bot(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test soft deleting a bot resource."""
        # Setup
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        bot = BotCRD(
            metadata=Metadata(name="test-bot", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name=ghost_schema.metadata.name, namespace="default"),
                model_ref=ResourceRef(kind=KindType.MODEL, name=model_schema.metadata.name, namespace="default"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name=shell_schema.metadata.name, namespace="default"),
            ),
        )
        await service.create(bot)

        deleted = await service.delete("test-bot", "default")
        assert deleted is True

        result = await service.get("test-bot", "default")
        assert result is None

    async def test_exists(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test checking if a bot exists."""
        # Setup
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        bot = BotCRD(
            metadata=Metadata(name="test-bot", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name=ghost_schema.metadata.name, namespace="default"),
                model_ref=ResourceRef(kind=KindType.MODEL, name=model_schema.metadata.name, namespace="default"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name=shell_schema.metadata.name, namespace="default"),
            ),
        )
        await service.create(bot)

        assert await service.exists("test-bot", "default") is True
        assert await service.exists("nonexistent", "default") is False
