"""
Pytest configuration and shared fixtures.
"""

import pytest
from chat_shell_101.agent.config import AgentConfig


@pytest.fixture
def agent_config():
    """Default agent configuration for testing."""
    return AgentConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=4096,
        max_iterations=5,
        system_prompt="You are a helpful test assistant.",
        tools=[],
        checkpoint_enabled=False,
        compress_context=False,
    )


@pytest.fixture
def agent_config_with_compression():
    """Agent configuration with compression enabled."""
    return AgentConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=4096,
        max_iterations=5,
        system_prompt="You are a helpful test assistant.",
        tools=[],
        checkpoint_enabled=False,
        compress_context=True,
        max_context_tokens=1000,
        compression_threshold=0.8,
        keep_recent_messages=2,
    )
