"""
Tests for LangGraphAgentBuilder - Epic 1: Core Agent System.
"""

import pytest
from chat_shell_101.agent.builder import LangGraphAgentBuilder
from chat_shell_101.agent.config import AgentConfig
from chat_shell_101.agent.agent import ChatAgent


pytestmark = [pytest.mark.unit, pytest.mark.epic_1]


class TestLangGraphAgentBuilder:
    """Test cases for LangGraphAgentBuilder."""

    def test_default_build(self):
        """Test building agent with default configuration."""
        builder = LangGraphAgentBuilder()
        agent = builder.build()

        assert isinstance(agent, ChatAgent)
        assert agent.config.model == "gpt-4"
        assert agent.config.temperature == 0.7

    def test_with_model(self):
        """Test setting model."""
        agent = LangGraphAgentBuilder().with_model("gpt-4-turbo").build()

        assert agent.config.model == "gpt-4-turbo"

    def test_with_temperature(self):
        """Test setting temperature."""
        agent = LangGraphAgentBuilder().with_temperature(0.5).build()

        assert agent.config.temperature == 0.5

    def test_with_max_iterations(self):
        """Test setting max iterations."""
        agent = LangGraphAgentBuilder().with_max_iterations(5).build()

        assert agent.config.max_iterations == 5

    def test_with_tools(self):
        """Test setting tools."""
        tools = ["calculator", "web_search"]
        agent = LangGraphAgentBuilder().with_tools(tools).build()

        assert agent.config.tools == tools

    def test_with_system_prompt(self):
        """Test setting system prompt."""
        prompt = "You are a coding assistant."
        agent = LangGraphAgentBuilder().with_system_prompt(prompt).build()

        assert agent.config.system_prompt == prompt

    def test_with_memory_checkpoint(self):
        """Test enabling memory checkpoint."""
        agent = LangGraphAgentBuilder().with_memory_checkpoint().build()

        assert agent.config.checkpoint_enabled is True
        assert agent.config.checkpoint_type == "memory"

    @pytest.mark.asyncio
    async def test_with_sqlite_checkpoint(self):
        """Test enabling SQLite checkpoint."""
        db_path = "/tmp/test_checkpoint.db"
        agent = LangGraphAgentBuilder().with_sqlite_checkpoint(db_path).build()

        assert agent.config.checkpoint_enabled is True
        assert agent.config.checkpoint_type == "sqlite"
        assert agent.config.checkpoint_path == db_path

    def test_with_context_compression(self):
        """Test enabling context compression."""
        agent = (
            LangGraphAgentBuilder()
            .with_context_compression(
                max_context_tokens=4000,
                compression_threshold=0.9,
                keep_recent_messages=6,
            )
            .build()
        )

        assert agent.config.compress_context is True
        assert agent.config.max_context_tokens == 4000
        assert agent.config.compression_threshold == 0.9
        assert agent.config.keep_recent_messages == 6

    def test_chained_configuration(self):
        """Test chaining multiple configuration methods."""
        agent = (
            LangGraphAgentBuilder()
            .with_model("gpt-4o")
            .with_temperature(0.3)
            .with_max_iterations(3)
            .with_tools(["calculator"])
            .with_system_prompt("You are a math expert.")
            .with_memory_checkpoint()
            .with_context_compression(max_context_tokens=2000)
            .build()
        )

        assert agent.config.model == "gpt-4o"
        assert agent.config.temperature == 0.3
        assert agent.config.max_iterations == 3
        assert agent.config.tools == ["calculator"]
        assert agent.config.system_prompt == "You are a math expert."
        assert agent.config.checkpoint_enabled is True
        assert agent.config.compress_context is True
        assert agent.config.max_context_tokens == 2000

    def test_with_config(self):
        """Test building from existing AgentConfig."""
        config = AgentConfig(
            model="custom-model",
            temperature=0.9,
            max_iterations=7,
        )
        agent = LangGraphAgentBuilder().with_config(config).build()

        assert agent.config.model == "custom-model"
        assert agent.config.temperature == 0.9
        assert agent.config.max_iterations == 7

    def test_builder_returns_self(self):
        """Test that builder methods return self for chaining."""
        builder = LangGraphAgentBuilder()

        assert builder.with_model("gpt-4") is builder
        assert builder.with_temperature(0.5) is builder
        assert builder.with_tools([]) is builder
        assert builder.with_system_prompt("test") is builder
        assert builder.with_memory_checkpoint() is builder

    def test_multiple_builds_independent(self):
        """Test that multiple builds create independent agents."""
        builder = LangGraphAgentBuilder()

        # Build first agent
        agent1 = builder.with_model("gpt-4").build()

        # Create new builder for second agent to ensure independence
        builder2 = LangGraphAgentBuilder()
        agent2 = builder2.with_model("gpt-4-turbo").build()

        assert agent1.config.model == "gpt-4"
        assert agent2.config.model == "gpt-4-turbo"
