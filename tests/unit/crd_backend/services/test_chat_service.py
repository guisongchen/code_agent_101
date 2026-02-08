"""Tests for ChatService.

Tests: 10 tests covering ChatService functionality
- Bot configuration fetching: 3 tests
- AgentConfig building: 2 tests
- Chat execution: 3 tests
- Error handling: 2 tests

Epic 13: Chat Shell Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.chat import ChatService, BotConfigurationError, ChatExecutionError

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_13,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_13
@pytest.mark.unit
@pytest.mark.backend
class TestChatService:
    """Test suite for ChatService - 10 tests."""

    async def test_chat_service_initialization(self, async_session):
        """Test ChatService initializes with correct dependencies."""
        service = ChatService(async_session)

        assert service.session == async_session
        assert service.bot_service is not None
        assert service.ghost_service is not None
        assert service.model_service is not None
        assert service.shell_service is not None

    async def test_validate_bot_configuration_not_found(self, async_session):
        """Test validation fails when bot doesn't exist."""
        service = ChatService(async_session)

        with pytest.raises(BotConfigurationError) as exc_info:
            await service.validate_bot_configuration("nonexistent-bot", "default")

        assert "not found" in str(exc_info.value).lower()

    async def test_validate_bot_configuration_success(self, async_session):
        """Test validation succeeds with properly configured bot."""
        # First create required resources
        from backend.models.kinds import Kind, KindType

        # Create Ghost
        ghost = Kind(
            kind=KindType.GHOST,
            name="test-ghost",
            namespace="default",
            spec={"systemPrompt": "You are a helpful assistant"},
        )
        async_session.add(ghost)

        # Create Model
        model = Kind(
            kind=KindType.MODEL,
            name="test-model",
            namespace="default",
            spec={
                "config": {
                    "provider": "openai",
                    "modelName": "gpt-4",
                },
                "defaultTemperature": 0.7,
            },
        )
        async_session.add(model)

        # Create Shell
        shell = Kind(
            kind=KindType.SHELL,
            name="test-shell",
            namespace="default",
            spec={"type": "chat"},
        )
        async_session.add(shell)

        # Create Bot
        bot = Kind(
            kind=KindType.BOT,
            name="test-bot",
            namespace="default",
            spec={
                "ghostRef": {"kind": "ghost", "name": "test-ghost", "namespace": "default"},
                "modelRef": {"kind": "model", "name": "test-model", "namespace": "default"},
                "shellRef": {"kind": "shell", "name": "test-shell", "namespace": "default"},
            },
        )
        async_session.add(bot)
        await async_session.commit()

        service = ChatService(async_session)
        result = await service.validate_bot_configuration("test-bot", "default")

        assert result["valid"] is True
        assert result["bot"] == "test-bot"
        assert result["ghost"] == "test-ghost"
        assert result["model"] == "test-model"
        assert result["shell"] == "test-shell"
        assert len(result["errors"]) == 0

    async def test_validate_bot_configuration_missing_ghost(self, async_session):
        """Test validation fails when ghost reference is missing."""
        from backend.models.kinds import Kind, KindType

        # Create Model and Shell but not Ghost
        model = Kind(
            kind=KindType.MODEL,
            name="test-model",
            namespace="default",
            spec={"config": {"provider": "openai", "modelName": "gpt-4"}},
        )
        async_session.add(model)

        shell = Kind(
            kind=KindType.SHELL,
            name="test-shell",
            namespace="default",
            spec={"type": "chat"},
        )
        async_session.add(shell)

        # Create Bot with missing ghost reference
        bot = Kind(
            kind=KindType.BOT,
            name="test-bot",
            namespace="default",
            spec={
                "ghostRef": {"kind": "ghost", "name": "missing-ghost", "namespace": "default"},
                "modelRef": {"kind": "model", "name": "test-model", "namespace": "default"},
                "shellRef": {"kind": "shell", "name": "test-shell", "namespace": "default"},
            },
        )
        async_session.add(bot)
        await async_session.commit()

        service = ChatService(async_session)
        result = await service.validate_bot_configuration("test-bot", "default")

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("ghost" in err.lower() for err in result["errors"])

    async def test_build_agent_config(self, async_session):
        """Test AgentConfig is built correctly from resources."""
        from backend.schemas import BotResponse, GhostResponse, ModelResponse, ShellResponse
        from backend.schemas.base import Metadata

        service = ChatService(async_session)

        # Create mock resources
        ghost = GhostResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            metadata=Metadata(name="test-ghost", namespace="default"),
            spec={
                "systemPrompt": "You are a test assistant",
                "temperature": 0.5,
            },
        )

        model = ModelResponse(
            id="123e4567-e89b-12d3-a456-426614174001",
            metadata=Metadata(name="test-model", namespace="default"),
            spec={
                "config": {"provider": "openai", "modelName": "gpt-4"},
                "defaultTemperature": 0.7,
                "contextLength": 8192,
            },
        )

        shell = ShellResponse(
            id="123e4567-e89b-12d3-a456-426614174002",
            metadata=Metadata(name="test-shell", namespace="default"),
            spec={"type": "chat", "allowedTools": ["file_reader"]},
        )

        bot = BotResponse(
            id="123e4567-e89b-12d3-a456-426614174003",
            metadata=Metadata(name="test-bot", namespace="default"),
            spec={
                "ghostRef": {"kind": "ghost", "name": "test-ghost", "namespace": "default"},
                "modelRef": {"kind": "model", "name": "test-model", "namespace": "default"},
                "shellRef": {"kind": "shell", "name": "test-shell", "namespace": "default"},
                "maxIterations": 5,
            },
        )

        config = service._build_agent_config(ghost, model, shell, bot)

        assert config.system_prompt == "You are a test assistant"
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5  # Ghost temperature takes precedence
        assert config.max_tokens == 8192
        assert config.max_iterations == 5
        assert config.tools == ["file_reader"]

    async def test_build_agent_config_default_values(self, async_session):
        """Test AgentConfig uses default values when not specified."""
        from backend.schemas import BotResponse, GhostResponse, ModelResponse, ShellResponse
        from backend.schemas.base import Metadata

        service = ChatService(async_session)

        # Create resources with minimal config
        ghost = GhostResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            metadata=Metadata(name="test-ghost", namespace="default"),
            spec={"systemPrompt": "Test prompt"},  # No temperature
        )

        model = ModelResponse(
            id="123e4567-e89b-12d3-a456-426614174001",
            metadata=Metadata(name="test-model", namespace="default"),
            spec={
                "config": {"provider": "anthropic", "modelName": "claude-3"},
                # No defaultTemperature or contextLength
            },
        )

        shell = ShellResponse(
            id="123e4567-e89b-12d3-a456-426614174002",
            metadata=Metadata(name="test-shell", namespace="default"),
            spec={"type": "chat"},  # No allowedTools
        )

        bot = BotResponse(
            id="123e4567-e89b-12d3-a456-426614174003",
            metadata=Metadata(name="test-bot", namespace="default"),
            spec={
                "ghostRef": {"kind": "ghost", "name": "test-ghost", "namespace": "default"},
                "modelRef": {"kind": "model", "name": "test-model", "namespace": "default"},
                "shellRef": {"kind": "shell", "name": "test-shell", "namespace": "default"},
                # No maxIterations
            },
        )

        config = service._build_agent_config(ghost, model, shell, bot)

        # Should use model's default temperature or 0.7
        assert config.temperature == 0.7
        # Should use default max_tokens
        assert config.max_tokens == 4096
        # Should use default max_iterations
        assert config.max_iterations == 10
        # Should have empty tools list
        assert config.tools == []

    async def test_chat_service_error_classes(self):
        """Test custom exception classes."""
        from backend.services.chat import ChatServiceError

        # Test exception hierarchy
        assert issubclass(BotConfigurationError, ChatServiceError)
        assert issubclass(ChatExecutionError, ChatServiceError)

        # Test exception messages
        err1 = BotConfigurationError("Test config error")
        assert str(err1) == "Test config error"

        err2 = ChatExecutionError("Test execution error")
        assert str(err2) == "Test execution error"

    async def test_chat_service_imports_chat_shell(self, async_session):
        """Test that ChatService properly imports chat_shell components."""
        service = ChatService(async_session)

        # This should raise BotConfigurationError (bot not found)
        # rather than ImportError (chat_shell not available)
        with pytest.raises(BotConfigurationError):
            await service.create_chat_agent("nonexistent-bot", "default")

    async def test_build_agent_config_tools_priority(self, async_session):
        """Test that shell allowed_tools takes priority over ghost tools_enabled."""
        from backend.schemas import BotResponse, GhostResponse, ModelResponse, ShellResponse
        from backend.schemas.base import Metadata

        service = ChatService(async_session)

        ghost = GhostResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            metadata=Metadata(name="test-ghost", namespace="default"),
            spec={
                "systemPrompt": "Test",
                "toolsEnabled": ["web_search", "calculator"],  # Ghost tools
            },
        )

        model = ModelResponse(
            id="123e4567-e89b-12d3-a456-426614174001",
            metadata=Metadata(name="test-model", namespace="default"),
            spec={"config": {"provider": "openai", "modelName": "gpt-4"}},
        )

        # Shell has specific allowed_tools
        shell = ShellResponse(
            id="123e4567-e89b-12d3-a456-426614174002",
            metadata=Metadata(name="test-shell", namespace="default"),
            spec={"type": "chat", "allowedTools": ["file_reader"]},
        )

        bot = BotResponse(
            id="123e4567-e89b-12d3-a456-426614174003",
            metadata=Metadata(name="test-bot", namespace="default"),
            spec={
                "ghostRef": {"kind": "ghost", "name": "test-ghost", "namespace": "default"},
                "modelRef": {"kind": "model", "name": "test-model", "namespace": "default"},
                "shellRef": {"kind": "shell", "name": "test-shell", "namespace": "default"},
            },
        )

        config = service._build_agent_config(ghost, model, shell, bot)

        # Shell's allowed_tools should take priority
        assert config.tools == ["file_reader"]

    async def test_build_agent_config_ghost_tools_fallback(self, async_session):
        """Test that ghost tools_enabled is used when shell has no allowed_tools."""
        from backend.schemas import BotResponse, GhostResponse, ModelResponse, ShellResponse
        from backend.schemas.base import Metadata

        service = ChatService(async_session)

        ghost = GhostResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            metadata=Metadata(name="test-ghost", namespace="default"),
            spec={
                "systemPrompt": "Test",
                "toolsEnabled": ["web_search", "calculator"],
            },
        )

        model = ModelResponse(
            id="123e4567-e89b-12d3-a456-426614174001",
            metadata=Metadata(name="test-model", namespace="default"),
            spec={"config": {"provider": "openai", "modelName": "gpt-4"}},
        )

        # Shell has no allowed_tools
        shell = ShellResponse(
            id="123e4567-e89b-12d3-a456-426614174002",
            metadata=Metadata(name="test-shell", namespace="default"),
            spec={"type": "chat"},  # No allowedTools
        )

        bot = BotResponse(
            id="123e4567-e89b-12d3-a456-426614174003",
            metadata=Metadata(name="test-bot", namespace="default"),
            spec={
                "ghostRef": {"kind": "ghost", "name": "test-ghost", "namespace": "default"},
                "modelRef": {"kind": "model", "name": "test-model", "namespace": "default"},
                "shellRef": {"kind": "shell", "name": "test-shell", "namespace": "default"},
            },
        )

        config = service._build_agent_config(ghost, model, shell, bot)

        # Should fall back to ghost's tools_enabled
        assert config.tools == ["web_search", "calculator"]
