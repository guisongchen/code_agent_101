"""
Unit tests for ToolRegistry.
"""
import pytest
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from chat_shell_101.tools.registry import ToolRegistry, tool_registry
from chat_shell_101.tools.base import BaseTool, ToolInput, ToolOutput
from chat_shell_101.tools.calculator import CalculatorTool
from pydantic import BaseModel, Field


class TestToolRegistry:
    """Test suite for ToolRegistry."""

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        """Create fresh tool registry instance."""
        return ToolRegistry()

    @pytest.fixture
    def calculator_tool(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    @pytest.fixture
    def mock_tool(self) -> BaseTool:
        """Create a mock tool for testing."""
        class MockToolInput(ToolInput):
            param: str = Field(..., description="Test parameter")

        class MockTool(BaseTool):
            name = "mock_tool"
            description = "A mock tool for testing"
            input_schema = MockToolInput

            async def execute(self, input_data: MockToolInput) -> ToolOutput:
                return ToolOutput(result=f"Processed: {input_data.param}")

        return MockTool()

    def test_initial_state(self, registry: ToolRegistry) -> None:
        """Test initial state of registry."""
        assert registry.get_all_tools() == []
        assert registry.get_tool_names() == []

    def test_register_tool(self, registry: ToolRegistry, calculator_tool: CalculatorTool) -> None:
        """Test registering a tool."""
        registry.register(calculator_tool)

        assert len(registry.get_all_tools()) == 1
        assert registry.get_tool_names() == ["calculator"]
        assert registry.get_all_tools()[0] == calculator_tool

    def test_register_multiple_tools(
        self, registry: ToolRegistry, calculator_tool: CalculatorTool, mock_tool: BaseTool
    ) -> None:
        """Test registering multiple tools."""
        registry.register(calculator_tool)
        registry.register(mock_tool)

        tools = registry.get_all_tools()
        tool_names = registry.get_tool_names()

        assert len(tools) == 2
        assert len(tool_names) == 2
        assert "calculator" in tool_names
        assert "mock_tool" in tool_names
        assert calculator_tool in tools
        assert mock_tool in tools

    def test_get_tool_existing(self, registry: ToolRegistry, calculator_tool: CalculatorTool) -> None:
        """Test getting an existing tool."""
        registry.register(calculator_tool)

        tool = registry.get_tool("calculator")
        assert tool == calculator_tool
        assert tool.name == "calculator"
        assert "arithmetic expressions" in tool.description.lower()

    def test_get_tool_nonexistent(self, registry: ToolRegistry) -> None:
        """Test getting a non-existent tool raises KeyError."""
        with pytest.raises(KeyError, match="Tool not found: non_existent"):
            registry.get_tool("non_existent")

    def test_get_all_tools_empty(self, registry: ToolRegistry) -> None:
        """Test getting all tools from empty registry."""
        tools = registry.get_all_tools()
        assert tools == []

    def test_get_tool_names_empty(self, registry: ToolRegistry) -> None:
        """Test getting tool names from empty registry."""
        names = registry.get_tool_names()
        assert names == []

    def test_register_duplicate_tool_overwrites(
        self, registry: ToolRegistry, calculator_tool: CalculatorTool
    ) -> None:
        """Test that registering duplicate tool overwrites previous."""
        # Create a modified calculator tool
        class ModifiedCalculatorTool(CalculatorTool):
            name = "calculator"
            description = "Modified calculator tool"

        modified_tool = ModifiedCalculatorTool()

        # Register original
        registry.register(calculator_tool)
        assert registry.get_tool("calculator").description == calculator_tool.description

        # Register modified (should overwrite)
        registry.register(modified_tool)
        assert registry.get_tool("calculator").description == "Modified calculator tool"

        # Should only have one tool
        assert len(registry.get_all_tools()) == 1

    def test_tool_registry_isolation(self) -> None:
        """Test that different registry instances are isolated."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        calculator_tool = CalculatorTool()

        # Register in registry1 only
        registry1.register(calculator_tool)

        # registry1 should have the tool
        assert len(registry1.get_all_tools()) == 1
        assert registry1.get_tool_names() == ["calculator"]

        # registry2 should be empty
        assert len(registry2.get_all_tools()) == 0
        assert registry2.get_tool_names() == []

    @pytest.mark.asyncio
    async def test_to_langchain_tools_empty(self, registry: ToolRegistry) -> None:
        """Test converting empty registry to LangChain tools."""
        langchain_tools = registry.to_langchain_tools()

        assert isinstance(langchain_tools, list)
        assert len(langchain_tools) == 0

    @pytest.mark.asyncio
    async def test_to_langchain_tools_single(
        self, registry: ToolRegistry, calculator_tool: CalculatorTool
    ) -> None:
        """Test converting single tool to LangChain format."""
        registry.register(calculator_tool)

        langchain_tools = registry.to_langchain_tools()

        assert isinstance(langchain_tools, list)
        assert len(langchain_tools) == 1

        # Check tool properties
        langchain_tool = langchain_tools[0]
        assert hasattr(langchain_tool, "name")
        assert hasattr(langchain_tool, "description")
        assert hasattr(langchain_tool, "args_schema")

        # Tool should have async invoke method
        assert hasattr(langchain_tool, "ainvoke")
        assert callable(langchain_tool.ainvoke)

    @pytest.mark.asyncio
    async def test_to_langchain_tools_multiple(
        self, registry: ToolRegistry, calculator_tool: CalculatorTool, mock_tool: BaseTool
    ) -> None:
        """Test converting multiple tools to LangChain format."""
        registry.register(calculator_tool)
        registry.register(mock_tool)

        langchain_tools = registry.to_langchain_tools()

        assert isinstance(langchain_tools, list)
        assert len(langchain_tools) == 2

        # Check tool names
        tool_names = [tool.name for tool in langchain_tools]
        assert "calculator" in tool_names
        assert "mock_tool" in tool_names

    @pytest.mark.asyncio
    async def test_langchain_tool_execution(
        self, registry: ToolRegistry, mock_tool: BaseTool
    ) -> None:
        """Test that LangChain tools can execute."""
        registry.register(mock_tool)

        langchain_tools = registry.to_langchain_tools()
        assert len(langchain_tools) == 1

        langchain_tool = langchain_tools[0]

        # Execute the tool
        result = await langchain_tool.ainvoke({"param": "test_value"})

        assert result == "Processed: test_value"

    @pytest.mark.asyncio
    async def test_langchain_tool_error_handling(
        self, registry: ToolRegistry
    ) -> None:
        """Test LangChain tool error handling."""
        class ErrorToolInput(ToolInput):
            param: str = Field(..., description="Test parameter")

        class ErrorTool(BaseTool):
            name = "error_tool"
            description = "A tool that returns errors"
            input_schema = ErrorToolInput

            async def execute(self, input_data: ErrorToolInput) -> ToolOutput:
                return ToolOutput(result="", error="Test error message")

        error_tool = ErrorTool()
        registry.register(error_tool)

        langchain_tools = registry.to_langchain_tools()
        langchain_tool = langchain_tools[0]

        # Should raise ValueError when tool returns error
        with pytest.raises(ValueError, match="Test error message"):
            await langchain_tool.ainvoke({"param": "test"})

    def test_global_tool_registry_instance(self) -> None:
        """Test global tool_registry instance."""
        # Should be a ToolRegistry instance
        assert isinstance(tool_registry, ToolRegistry)

        # Register calculator tool (fixture clears registry, so we need to re-register)
        tool_registry.register(CalculatorTool())

        # Should have calculator tool registered by default
        tool_names = tool_registry.get_tool_names()
        assert "calculator" in tool_names

        # Should be able to get the calculator tool
        calculator = tool_registry.get_tool("calculator")
        assert isinstance(calculator, CalculatorTool)

    def test_global_registry_is_singleton(self) -> None:
        """Test that tool_registry is a singleton (same instance everywhere)."""
        from chat_shell_101.tools.registry import tool_registry as registry1
        from chat_shell_101.tools.registry import tool_registry as registry2

        # Both imports should reference the same instance
        assert registry1 is registry2

        # Modify one, check the other
        original_tools = registry1.get_all_tools().copy()

        # Create a new registry to compare
        new_registry = ToolRegistry()
        assert new_registry is not registry1

    @pytest.mark.asyncio
    async def test_langchain_tool_wrapper_closure_issue(
        self, registry: ToolRegistry
    ) -> None:
        """Test that LangChain tool wrapper doesn't have closure issues."""
        # Create multiple tools
        class Tool1Input(ToolInput):
            param: str = Field(..., description="Parameter for tool 1")

        class Tool1(BaseTool):
            name = "tool1"
            description = "First test tool"
            input_schema = Tool1Input

            async def execute(self, input_data: Tool1Input) -> ToolOutput:
                return ToolOutput(result=f"Tool1: {input_data.param}")

        class Tool2Input(ToolInput):
            value: str = Field(..., description="Parameter for tool 2")

        class Tool2(BaseTool):
            name = "tool2"
            description = "Second test tool"
            input_schema = Tool2Input

            async def execute(self, input_data: Tool2Input) -> ToolOutput:
                return ToolOutput(result=f"Tool2: {input_data.value}")

        tool1 = Tool1()
        tool2 = Tool2()

        registry.register(tool1)
        registry.register(tool2)

        langchain_tools = registry.to_langchain_tools()

        # Both tools should work correctly
        result1 = await langchain_tools[0].ainvoke({"param": "test1"})
        result2 = await langchain_tools[1].ainvoke({"value": "test2"})

        assert result1 == "Tool1: test1"
        assert result2 == "Tool2: test2"