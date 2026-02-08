"""Unit tests for TeamService.

Tests: 7 tests covering TeamService CRUD and member validation
"""

import pytest
import pytest_asyncio

from backend.services.team import TeamService
from backend.services.bot import BotService
from backend.services.ghost import GhostService
from backend.services.model import ModelService
from backend.services.shell import ShellService
from backend.models.kinds import KindType
from backend.schemas.team import TeamSpec, TeamCRD, TeamMember, Metadata
from backend.schemas.bot import BotSpec, BotCRD
from backend.schemas.base import ResourceRef


@pytest.mark.epic_9
@pytest.mark.unit
@pytest.mark.backend
class TestTeamService:
    """Test suite for TeamService - 7 tests."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create TeamService instance."""
        return TeamService(async_session)

    async def test_create_team_with_valid_members(
        self, service, async_session, ghost_schema, model_schema, shell_schema
    ):
        """Test creating a team with valid bot members."""
        # Create dependencies
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        # Create a bot
        bot = BotCRD(
            metadata=Metadata(name="test-bot", namespace="default"),
            spec=BotSpec(
                ghost_ref=ResourceRef(kind=KindType.GHOST, name=ghost_schema.metadata.name, namespace="default"),
                model_ref=ResourceRef(kind=KindType.MODEL, name=model_schema.metadata.name, namespace="default"),
                shell_ref=ResourceRef(kind=KindType.SHELL, name=shell_schema.metadata.name, namespace="default"),
            ),
        )
        await BotService(async_session).create(bot)

        # Create team with bot
        team = TeamCRD(
            metadata=Metadata(name="test-team", namespace="default"),
            spec=TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="test-bot", namespace="default"),
                        role="leader",
                    ),
                ],
            ),
        )

        result = await service.create(team)
        assert result.metadata.name == "test-team"
        assert len(result.spec.members) == 1
        assert result.spec.members[0].role == "leader"

    async def test_create_team_with_invalid_bot_ref(self, service):
        """Test creating team with non-existent bot reference fails."""
        team = TeamCRD(
            metadata=Metadata(name="test-team", namespace="default"),
            spec=TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="nonexistent-bot", namespace="default"),
                        role="worker",
                    ),
                ],
            ),
        )

        with pytest.raises(ValueError, match="Referenced Bot not found"):
            await service.create(team)

    async def test_create_team_multiple_members(
        self, service, async_session, ghost_schema, model_schema, shell_schema
    ):
        """Test creating a team with multiple bot members."""
        # Create dependencies
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        # Create multiple bots
        bot_service = BotService(async_session)
        for i in range(3):
            bot = BotCRD(
                metadata=Metadata(name=f"bot-{i}", namespace="default"),
                spec=BotSpec(
                    ghost_ref=ResourceRef(kind=KindType.GHOST, name=ghost_schema.metadata.name, namespace="default"),
                    model_ref=ResourceRef(kind=KindType.MODEL, name=model_schema.metadata.name, namespace="default"),
                    shell_ref=ResourceRef(kind=KindType.SHELL, name=shell_schema.metadata.name, namespace="default"),
                ),
            )
            await bot_service.create(bot)

        # Create team with multiple bots
        team = TeamCRD(
            metadata=Metadata(name="multi-bot-team", namespace="default"),
            spec=TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="bot-0", namespace="default"),
                        role="leader",
                        priority=1,
                    ),
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="bot-1", namespace="default"),
                        role="worker",
                        priority=0,
                    ),
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="bot-2", namespace="default"),
                        role="reviewer",
                        priority=2,
                    ),
                ],
            ),
        )

        result = await service.create(team)
        assert len(result.spec.members) == 3

    async def test_get_team(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test retrieving a team by name."""
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
        await BotService(async_session).create(bot)

        team = TeamCRD(
            metadata=Metadata(name="test-team", namespace="default"),
            spec=TeamSpec(
                members=[
                    TeamMember(
                        bot_ref=ResourceRef(kind=KindType.BOT, name="test-bot", namespace="default"),
                        role="leader",
                    ),
                ],
            ),
        )
        created = await service.create(team)

        result = await service.get("test-team", "default")
        assert result is not None
        assert result.id == created.id

    async def test_list_teams(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test listing team resources."""
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
        await BotService(async_session).create(bot)

        team1 = TeamCRD(
            metadata=Metadata(name="team-1", namespace="default"),
            spec=TeamSpec(
                members=[TeamMember(bot_ref=ResourceRef(kind=KindType.BOT, name="test-bot", namespace="default"), role="leader")],
            ),
        )
        team2 = TeamCRD(
            metadata=Metadata(name="team-2", namespace="default"),
            spec=TeamSpec(
                members=[TeamMember(bot_ref=ResourceRef(kind=KindType.BOT, name="test-bot", namespace="default"), role="leader")],
            ),
        )

        await service.create(team1)
        await service.create(team2)

        results = await service.list()
        assert len(results) == 2

    async def test_find_by_bot(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test finding teams that contain a specific bot."""
        # Setup
        await GhostService(async_session).create(ghost_schema)
        await ModelService(async_session).create(model_schema)
        await ShellService(async_session).create(shell_schema)

        # Create two bots
        bot_service = BotService(async_session)
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
        await bot_service.create(bot1)
        await bot_service.create(bot2)

        # Create teams with different bots
        team1 = TeamCRD(
            metadata=Metadata(name="team-1", namespace="default"),
            spec=TeamSpec(
                members=[TeamMember(bot_ref=ResourceRef(kind=KindType.BOT, name="bot-1", namespace="default"), role="leader")],
            ),
        )
        team2 = TeamCRD(
            metadata=Metadata(name="team-2", namespace="default"),
            spec=TeamSpec(
                members=[TeamMember(bot_ref=ResourceRef(kind=KindType.BOT, name="bot-2", namespace="default"), role="leader")],
            ),
        )
        await service.create(team1)
        await service.create(team2)

        # Find teams containing bot-1
        teams_with_bot1 = await service.find_by_bot("bot-1")
        assert len(teams_with_bot1) == 1
        assert teams_with_bot1[0].metadata.name == "team-1"

    async def test_delete_team(self, service, async_session, ghost_schema, model_schema, shell_schema):
        """Test soft deleting a team resource."""
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
        await BotService(async_session).create(bot)

        team = TeamCRD(
            metadata=Metadata(name="test-team", namespace="default"),
            spec=TeamSpec(
                members=[TeamMember(bot_ref=ResourceRef(kind=KindType.BOT, name="test-bot", namespace="default"), role="leader")],
            ),
        )
        await service.create(team)

        deleted = await service.delete("test-team", "default")
        assert deleted is True

        result = await service.get("test-team", "default")
        assert result is None
