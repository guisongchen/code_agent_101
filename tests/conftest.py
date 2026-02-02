"""
Test configuration and fixtures for Chat Shell 101.
"""
import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, Generator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Register pytest-asyncio plugin
pytest_plugins = ["pytest_asyncio"]

from pydantic import BaseModel

# Mock problematic imports at the module level before importing anything
# These imports may fail in newer versions of langgraph, so we mock them
import langgraph.prebuilt
if not hasattr(langgraph.prebuilt, 'ToolExecutor'):
    langgraph.prebuilt.ToolExecutor = MagicMock()
if not hasattr(langgraph.prebuilt, 'ToolInvocation'):
    langgraph.prebuilt.ToolInvocation = MagicMock()

# Now import our modules
from chat_shell_101.storage.interfaces import Message
from chat_shell_101.tools.calculator import CalculatorTool
from chat_shell_101.tools.registry import tool_registry
from chat_shell_101.storage.json_storage import JSONStorage
from chat_shell_101.storage.memory_storage import MemoryStorage


@pytest.fixture
def temp_storage_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_messages() -> List[Message]:
    """Create sample messages for testing."""
    return [
        Message(role="user", content="Hello, world!", timestamp=datetime(2024, 1, 1, 0, 0, 0)),
        Message(role="assistant", content="Hi there!", timestamp=datetime(2024, 1, 1, 0, 0, 1)),
        Message(role="user", content="What's 2+2?", timestamp=datetime(2024, 1, 1, 0, 0, 2)),
        Message(role="assistant", content="4", timestamp=datetime(2024, 1, 1, 0, 0, 3)),
    ]


@pytest.fixture
def calculator_tool() -> CalculatorTool:
    """Create a calculator tool instance."""
    return CalculatorTool()


@pytest.fixture
def json_storage(temp_storage_dir: Path) -> JSONStorage:
    """Create a JSON storage instance with temporary directory."""
    return JSONStorage(storage_path=temp_storage_dir)


@pytest.fixture
def memory_storage() -> MemoryStorage:
    """Create a memory storage instance."""
    return MemoryStorage()


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clean environment variables for isolation."""
    original_env = os.environ.copy()
    # Remove CHAT_SHELL_* environment variables
    keys_to_remove = [k for k in os.environ.keys() if k.startswith("CHAT_SHELL_")]
    for key in keys_to_remove:
        os.environ.pop(key, None)

    # Also remove OPENAI_API_KEY and BASE_URL
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("BASE_URL", None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_openai() -> Generator[MagicMock, None, None]:
    """Mock OpenAI API calls."""
    with patch("chat_shell_101.agent.ChatOpenAI") as mock_chat_openai:
        mock_instance = AsyncMock()
        mock_instance.ainvoke = AsyncMock()
        mock_instance.bind_tools = MagicMock(return_value=mock_instance)
        mock_chat_openai.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_langgraph() -> Generator[Dict[str, MagicMock], None, None]:
    """Mock LangGraph components."""
    with patch("chat_shell_101.agent.StateGraph") as mock_state_graph, \
         patch("chat_shell_101.agent.ToolExecutor") as mock_tool_executor:

        mock_graph_instance = MagicMock()
        mock_graph_instance.add_node = MagicMock()
        mock_graph_instance.add_edge = MagicMock()
        mock_graph_instance.add_conditional_edges = MagicMock()
        mock_graph_instance.compile = MagicMock(return_value=AsyncMock())
        mock_state_graph.return_value = mock_graph_instance

        mock_executor_instance = AsyncMock()
        mock_tool_executor.return_value = mock_executor_instance

        yield {
            "state_graph": mock_state_graph,
            "graph_instance": mock_graph_instance,
            "tool_executor": mock_tool_executor,
            "executor_instance": mock_executor_instance,
        }


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def corrupt_json_file(temp_storage_dir: Path) -> Path:
    """Create a corrupt JSON file for testing error handling."""
    corrupt_file = temp_storage_dir / "corrupt.json"
    corrupt_file.write_text("{invalid json")
    return corrupt_file


@pytest.fixture
def read_only_dir(temp_storage_dir: Path) -> Path:
    """Create a read-only directory for testing permission errors."""
    read_only = temp_storage_dir / "readonly"
    read_only.mkdir()
    read_only.chmod(0o444)  # Read-only
    return read_only


@pytest.fixture(autouse=True)
def reset_tool_registry() -> Generator[None, None, None]:
    """Reset tool registry before each test to ensure isolation."""
    # Save original tools
    original_tools = tool_registry._tools.copy()
    tool_registry._tools.clear()

    yield

    # Restore original tools
    tool_registry._tools.clear()
    tool_registry._tools.update(original_tools)