"""
Tests for AgentConfig data class - Epic 1: Core Agent System.
"""

import pytest
from chat_shell_101.agent.config import AgentConfig


pytestmark = [pytest.mark.unit, pytest.mark.epic_1]


class TestAgentConfig:
    """Test cases for AgentConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AgentConfig()

        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.max_iterations == 10
        assert config.system_prompt == "You are a helpful AI assistant."
        assert config.tools == []
        assert config.checkpoint_enabled is True
        assert config.checkpoint_type == "memory"
        assert config.checkpoint_path is None
        assert config.compress_context is True
        assert config.max_context_tokens == 8000
        assert config.compression_threshold == 0.8
        assert config.keep_recent_messages == 4

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AgentConfig(
            model="gpt-4-turbo",
            temperature=0.5,
            max_tokens=2048,
            max_iterations=5,
            system_prompt="Custom prompt",
            tools=["calculator"],
            checkpoint_enabled=False,
            checkpoint_type="sqlite",
            checkpoint_path="/tmp/test.db",
            compress_context=False,
            max_context_tokens=4000,
            compression_threshold=0.9,
            keep_recent_messages=6,
        )

        assert config.model == "gpt-4-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.max_iterations == 5
        assert config.system_prompt == "Custom prompt"
        assert config.tools == ["calculator"]
        assert config.checkpoint_enabled is False
        assert config.checkpoint_type == "sqlite"
        assert config.checkpoint_path == "/tmp/test.db"
        assert config.compress_context is False
        assert config.max_context_tokens == 4000
        assert config.compression_threshold == 0.9
        assert config.keep_recent_messages == 6

    def test_temperature_validation(self):
        """Test temperature range validation."""
        # Valid temperatures
        AgentConfig(temperature=0.0)
        AgentConfig(temperature=2.0)
        AgentConfig(temperature=1.5)

    def test_max_iterations_validation(self):
        """Test max_iterations must be positive."""
        config = AgentConfig(max_iterations=1)
        assert config.max_iterations == 1

        config = AgentConfig(max_iterations=100)
        assert config.max_iterations == 100

    def test_compression_threshold_range(self):
        """Test compression threshold is between 0 and 1 (exclusive 0, inclusive 1)."""
        # Valid values (> 0 and <= 1)
        config = AgentConfig(compression_threshold=0.01)
        assert config.compression_threshold == 0.01

        config = AgentConfig(compression_threshold=1.0)
        assert config.compression_threshold == 1.0

        config = AgentConfig(compression_threshold=0.5)
        assert config.compression_threshold == 0.5

        # Invalid values
        with pytest.raises(ValueError, match="compression_threshold"):
            AgentConfig(compression_threshold=0.0)

        with pytest.raises(ValueError, match="compression_threshold"):
            AgentConfig(compression_threshold=-0.1)

        with pytest.raises(ValueError, match="compression_threshold"):
            AgentConfig(compression_threshold=1.1)

    def test_tools_list_mutation(self):
        """Test that tools list can be modified after creation."""
        config = AgentConfig()
        config.tools.append("new_tool")
        assert "new_tool" in config.tools

    def test_checkpoint_type_values(self):
        """Test valid checkpoint types."""
        config_memory = AgentConfig(checkpoint_type="memory")
        assert config_memory.checkpoint_type == "memory"

        # SQLite requires checkpoint_path
        config_sqlite = AgentConfig(
            checkpoint_type="sqlite",
            checkpoint_path="/tmp/test.db"
        )
        assert config_sqlite.checkpoint_type == "sqlite"

        with pytest.raises(ValueError, match="checkpoint_path"):
            AgentConfig(checkpoint_type="sqlite")
