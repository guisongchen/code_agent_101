"""
Tests for Package Mode interface.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chat_shell_101.package.interface import (
    ChatInput,
    ChatOutput,
    ChatInterface,
    DirectChatInterface,
    InterfaceConfig,
    StreamingChatOutput,
)


@pytest.mark.asyncio
class TestChatInput:
    """Test ChatInput model."""

    def test_basic_creation(self):
        """Test basic ChatInput creation."""
        inp = ChatInput(message="Hello")
        assert inp.message == "Hello"
        assert inp.session_id is None
        assert inp.system_prompt is None

    def test_full_creation(self):
        """Test ChatInput with all fields."""
        inp = ChatInput(
            message="Hello",
            session_id="test-session",
            system_prompt="You are helpful.",
            context=[{"role": "user", "content": "Previous"}],
            metadata={"key": "value"},
        )
        assert inp.message == "Hello"
        assert inp.session_id == "test-session"
        assert inp.system_prompt == "You are helpful."
        assert inp.context == [{"role": "user", "content": "Previous"}]
        assert inp.metadata == {"key": "value"}


@pytest.mark.asyncio
class TestInterfaceConfig:
    """Test InterfaceConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = InterfaceConfig()
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.max_iterations == 10
        assert config.tools is None
        assert config.enable_streaming is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = InterfaceConfig(
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=2048,
            max_iterations=5,
            tools=["calculator"],
            enable_streaming=False,
        )
        assert config.model == "deepseek-chat"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.max_iterations == 5
        assert config.tools == ["calculator"]
        assert config.enable_streaming is False


@pytest.mark.asyncio
class TestDirectChatInterface:
    """Test DirectChatInterface implementation."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return InterfaceConfig(
            model="gpt-4",
            temperature=0.7,
            max_iterations=5,
        )

    @pytest.fixture
    def mock_agent(self):
        """Create mock ChatAgent."""
        with patch("chat_shell_101.agent.agent.ChatAgent") as mock:
            agent_instance = AsyncMock()
            agent_instance.initialize = AsyncMock()
            mock.return_value = agent_instance
            yield mock, agent_instance

    async def test_initialize(self, config, mock_agent):
        """Test interface initialization."""
        mock_class, mock_instance = mock_agent
        interface = DirectChatInterface(config)

        await interface.initialize()

        assert interface._initialized is True
        mock_class.assert_called_once()
        mock_instance.initialize.assert_called_once()

    async def test_initialize_with_config_values(self, mock_agent):
        """Test that agent is initialized with correct config."""
        from chat_shell_101.agent.config import AgentConfig

        mock_class, _ = mock_agent
        config = InterfaceConfig(
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=2048,
            max_iterations=3,
            tools=["calculator"],
        )

        interface = DirectChatInterface(config)
        await interface.initialize()

        mock_class.assert_called_once()
        call_args = mock_class.call_args[0][0]
        assert isinstance(call_args, AgentConfig)
        assert call_args.model == "deepseek-chat"
        assert call_args.temperature == 0.5
        assert call_args.max_tokens == 2048
        assert call_args.max_iterations == 3
        assert call_args.tools == ["calculator"]

    async def test_chat_not_initialized(self, config):
        """Test that chat raises error if not initialized."""
        interface = DirectChatInterface(config)

        with pytest.raises(RuntimeError, match="not initialized"):
            await interface.chat("Hello")

    async def test_stream_chat_not_initialized(self, config):
        """Test that stream_chat raises error if not initialized."""
        interface = DirectChatInterface(config)

        with pytest.raises(RuntimeError, match="not initialized"):
            async for _ in interface.stream_chat("Hello"):
                pass

    async def test_shutdown(self, config, mock_agent):
        """Test interface shutdown."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        # Add some session data
        interface._sessions["test"] = [{"role": "user", "content": "test"}]

        await interface.shutdown()

        assert interface._initialized is False
        assert interface._sessions == {}

    async def test_get_history_empty(self, config, mock_agent):
        """Test getting history for non-existent session."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        history = await interface.get_history("non-existent")
        assert history == []

    async def test_list_sessions_empty(self, config, mock_agent):
        """Test listing sessions when none exist."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        sessions = await interface.list_sessions()
        assert sessions == []

    async def test_clear_history(self, config, mock_agent):
        """Test clearing history for a session."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        interface._sessions["test"] = [{"role": "user", "content": "test"}]
        await interface.clear_history("test")

        assert "test" not in interface._sessions

    async def test_normalize_input_string(self, config, mock_agent):
        """Test normalizing string input."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        result = interface._normalize_input("Hello")
        assert isinstance(result, ChatInput)
        assert result.message == "Hello"

    async def test_normalize_input_chatinput(self, config, mock_agent):
        """Test normalizing ChatInput input."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        inp = ChatInput(message="Hello", session_id="test")
        result = interface._normalize_input(inp)
        assert result is inp

    async def test_generate_session_id(self, config, mock_agent):
        """Test session ID generation."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        sid1 = interface._generate_session_id()
        sid2 = interface._generate_session_id()

        assert sid1 != sid2
        assert len(sid1) > 0

    async def test_build_messages_with_system_prompt(self, config, mock_agent):
        """Test building messages with system prompt."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        inp = ChatInput(
            message="Hello",
            system_prompt="You are helpful.",
            session_id="test",
        )
        messages = interface._build_messages(inp, "test")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    async def test_build_messages_with_context(self, config, mock_agent):
        """Test building messages with context."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        context = [{"role": "user", "content": "Previous message"}]
        inp = ChatInput(message="Hello", context=context, session_id="test")
        messages = interface._build_messages(inp, "test")

        assert len(messages) == 2
        assert messages[0] == context[0]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    async def test_build_messages_with_session_history(self, config, mock_agent):
        """Test building messages with session history."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        # Add history to session
        interface._sessions["test"] = [
            {"role": "user", "content": "Previous"},
            {"role": "assistant", "content": "Response"},
        ]

        inp = ChatInput(message="Hello", session_id="test")
        messages = interface._build_messages(inp, "test")

        assert len(messages) == 3
        assert messages[0]["content"] == "Previous"
        assert messages[1]["content"] == "Response"
        assert messages[2]["content"] == "Hello"

    async def test_store_messages(self, config, mock_agent):
        """Test storing messages in session."""
        interface = DirectChatInterface(config)
        await interface.initialize()

        interface._store_messages("test", "User message", "Assistant response")

        assert "test" in interface._sessions
        assert len(interface._sessions["test"]) == 2
        assert interface._sessions["test"][0]["role"] == "user"
        assert interface._sessions["test"][0]["content"] == "User message"
        assert interface._sessions["test"][1]["role"] == "assistant"
        assert interface._sessions["test"][1]["content"] == "Assistant response"


@pytest.mark.epic_4
@pytest.mark.unit
class TestPackageModeEpic4:
    """Epic 4 specific tests for Package Mode."""

    def test_chat_interface_is_abstract(self):
        """Test that ChatInterface is abstract."""
        with pytest.raises(TypeError):
            ChatInterface()

    def test_direct_chat_interface_instantiation(self):
        """Test that DirectChatInterface can be instantiated."""
        config = InterfaceConfig()
        interface = DirectChatInterface(config)
        assert interface is not None
        assert interface.config == config
