"""
Tests for ChatAgent - Epic 1: Core Agent System.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from chat_shell.agent.agent import ChatAgent, AgentState, ToolIterationLimitError
from chat_shell.agent.config import AgentConfig


pytestmark = [pytest.mark.unit, pytest.mark.epic_1, pytest.mark.chat_shell]


class TestAgentState:
    """Test cases for AgentState."""

    def test_default_state(self):
        """Test default agent state."""
        state = AgentState()

        assert state.messages == []
        assert state.iteration_count == 0
        assert state.system_prompt == "You are a helpful AI assistant."

    def test_custom_state(self):
        """Test custom agent state."""
        state = AgentState(
            messages=[HumanMessage(content="Hello")],
            iteration_count=3,
            system_prompt="Custom prompt",
        )

        assert len(state.messages) == 1
        assert state.iteration_count == 3
        assert state.system_prompt == "Custom prompt"

    def test_state_adds_messages(self):
        """Test that AgentState can accumulate messages."""
        from langgraph.graph.message import add_messages

        state1 = AgentState(messages=[HumanMessage(content="Hello")])
        state2 = AgentState(messages=[AIMessage(content="Hi")])

        combined = add_messages(state1.messages, state2.messages)
        assert len(combined) == 2


class TestChatAgentInitialization:
    """Test cases for ChatAgent initialization."""

    def test_default_initialization(self):
        """Test default agent initialization."""
        agent = ChatAgent()

        assert agent.config.model == "gpt-4"
        assert agent.llm is None
        assert agent._initialized is False
        assert agent._checkpointer is None

    def test_initialization_with_config(self, agent_config):
        """Test agent initialization with config."""
        agent = ChatAgent(agent_config)

        assert agent.config.model == "gpt-4"
        assert agent.config.temperature == 0.7
        assert agent.config.max_iterations == 5

    def test_with_checkpointer(self):
        """Test setting checkpointer."""
        agent = ChatAgent()
        checkpointer = MemorySaver()

        result = agent.with_checkpointer(checkpointer)

        assert result is agent  # Returns self
        assert agent._checkpointer is checkpointer

    def test_compression_initialization(self, agent_config_with_compression):
        """Test compressor is initialized when enabled."""
        agent = ChatAgent(agent_config_with_compression)

        assert agent._compressor is not None
        assert agent._compressor.max_tokens == 1000

    def test_no_compression_initialization(self, agent_config):
        """Test compressor is None when disabled."""
        agent = ChatAgent(agent_config)

        assert agent._compressor is None


class TestToolIterationLimitError:
    """Test cases for ToolIterationLimitError."""

    def test_error_creation(self):
        """Test error creation."""
        error = ToolIterationLimitError("Test message")

        assert str(error) == "Test message"
        assert isinstance(error, Exception)


class TestChatAgentMethods:
    """Test cases for ChatAgent methods."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock-initialized agent."""
        agent = ChatAgent()
        agent._initialized = True
        agent.llm = AsyncMock()
        agent.llm_with_tools = AsyncMock()
        agent.tools_by_name = {}
        return agent

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized(self, agent_config):
        """Test that initialize sets _initialized flag."""
        agent = ChatAgent(agent_config)

        # Mock the LLM and graph building
        with patch.object(agent, '_build_graph', return_value=Mock()):
            await agent.initialize()

        assert agent._initialized is True

    def test_build_graph_creates_compiled_graph(self, agent_config):
        """Test that _build_graph creates a compiled graph."""
        agent = ChatAgent(agent_config)
        agent.llm = Mock()
        agent.llm_with_tools = Mock()
        agent.tools = []
        agent.internal_tools = []

        graph = agent._build_graph()

        assert graph is not None

    def test_build_graph_with_checkpointer(self, agent_config):
        """Test that _build_graph uses checkpointer when provided."""
        agent = ChatAgent(agent_config)
        agent.llm = Mock()
        agent.llm_with_tools = Mock()
        agent.tools = []
        agent.internal_tools = []
        agent._checkpointer = MemorySaver()

        graph = agent._build_graph()

        assert graph is not None


class TestPromptModifierIntegration:
    """Test cases for PromptModifierTool integration."""

    def test_get_modified_system_prompt_no_modifiers(self, agent_config):
        """Test prompt without modifiers."""
        agent = ChatAgent(agent_config)
        agent.internal_tools = []

        state = AgentState(system_prompt="Original prompt")
        result = agent._get_modified_system_prompt(state)

        assert result == "Original prompt"

    def test_get_modified_system_prompt_with_modifier(self, agent_config):
        """Test prompt with modifier tools."""
        from chat_shell.tools.base import PromptModifierTool

        class MockModifierTool:
            def modify_prompt(self, current_prompt, state):
                return current_prompt + " [MODIFIED]"

        agent = ChatAgent(agent_config)
        agent.internal_tools = [MockModifierTool()]

        state = AgentState(system_prompt="Original")
        result = agent._get_modified_system_prompt(state)

        assert result == "Original [MODIFIED]"

    def test_get_modified_system_prompt_multiple_modifiers(self, agent_config):
        """Test prompt with multiple modifier tools."""

        class Modifier1:
            def modify_prompt(self, current_prompt, state):
                return current_prompt + " [M1]"

        class Modifier2:
            def modify_prompt(self, current_prompt, state):
                return current_prompt + " [M2]"

        agent = ChatAgent(agent_config)
        agent.internal_tools = [Modifier1(), Modifier2()]

        state = AgentState(system_prompt="Start")
        result = agent._get_modified_system_prompt(state)

        assert result == "Start [M1] [M2]"


class TestToolExecution:
    """Test cases for tool execution."""

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, agent_config):
        """Test executing non-existent tool."""
        agent = ChatAgent(agent_config)
        agent.tools_by_name = {}

        with pytest.raises(ValueError, match="Tool not found"):
            await agent._execute_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self, agent_config):
        """Test executing tool that returns error."""
        from chat_shell.tools.base import BaseTool, ToolInput, ToolOutput

        class ErrorTool(BaseTool):
            name = "error_tool"
            description = "A tool that errors"
            input_schema = ToolInput

            async def execute(self, input_data):
                return ToolOutput(error="Something went wrong")

        agent = ChatAgent(agent_config)
        agent.tools_by_name = {"error_tool": ErrorTool()}

        with pytest.raises(ValueError, match="Something went wrong"):
            await agent._execute_tool("error_tool", {})

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, agent_config):
        """Test successful tool execution."""
        from chat_shell.tools.base import BaseTool, ToolInput, ToolOutput

        class SuccessTool(BaseTool):
            name = "success_tool"
            description = "A successful tool"
            input_schema = ToolInput

            async def execute(self, input_data):
                return ToolOutput(result="Success!")

        agent = ChatAgent(agent_config)
        agent.tools_by_name = {"success_tool": SuccessTool()}

        result = await agent._execute_tool("success_tool", {})

        assert result == "Success!"


class TestStreaming:
    """Test cases for streaming functionality."""

    @pytest.mark.asyncio
    async def test_stream_not_initialized(self, agent_config):
        """Test that stream calls initialize if not initialized."""
        agent = ChatAgent(agent_config)

        # Should call initialize
        with pytest.raises(Exception):  # Will fail due to no API key
            async for _ in agent.stream([{"role": "user", "content": "Hello"}]):
                pass

    @pytest.mark.asyncio
    async def test_invoke_returns_string(self, agent_config):
        """Test that invoke returns a string response."""
        agent = ChatAgent(agent_config)
        agent._initialized = True

        # Mock the stream method
        async def mock_stream(*args, **kwargs):
            yield {"type": "content", "data": {"text": "Hello"}}
            yield {"type": "content", "data": {"text": " world"}}

        agent.stream = mock_stream

        result = await agent.invoke([{"role": "user", "content": "Hi"}])

        assert result == "Hello world"
