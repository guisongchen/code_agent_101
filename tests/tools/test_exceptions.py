"""
Tests for tool exceptions - Epic 3: Tools System.
"""

import pytest
from chat_shell_101.tools.exceptions import (
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
    ToolExecutionError,
    ToolRegistrationError,
    MCPToolError,
    MCPConnectionError,
    SkillError,
    SkillLoadError,
    SkillNotFoundError,
)


pytestmark = [pytest.mark.unit, pytest.mark.epic_3]


class TestToolErrors:
    """Test cases for tool exceptions."""

    def test_tool_error_basic(self):
        """Test basic tool error."""
        error = ToolError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.tool_name is None

    def test_tool_error_with_name(self):
        """Test tool error with tool name."""
        error = ToolError("Execution failed", tool_name="calculator")
        assert "calculator" in str(error)
        assert "Execution failed" in str(error)
        assert error.tool_name == "calculator"

    def test_tool_not_found_error(self):
        """Test tool not found error."""
        error = ToolNotFoundError("unknown_tool")
        assert "unknown_tool" in str(error)
        assert error.tool_name == "unknown_tool"

    def test_tool_validation_error(self):
        """Test tool validation error."""
        error = ToolValidationError("Invalid input", tool_name="calculator", field="expression")
        assert error.tool_name == "calculator"
        assert error.field == "expression"

    def test_tool_execution_error(self):
        """Test tool execution error."""
        cause = ValueError("Division by zero")
        error = ToolExecutionError("Calculation failed", tool_name="calculator", cause=cause)
        assert error.tool_name == "calculator"
        assert error.cause is cause

    def test_tool_registration_error(self):
        """Test tool registration error."""
        error = ToolRegistrationError("Invalid tool class", tool_name="bad_tool")
        assert error.tool_name == "bad_tool"


class TestMCPErrors:
    """Test cases for MCP exceptions."""

    def test_mcp_tool_error(self):
        """Test MCP tool error."""
        error = MCPToolError("MCP execution failed")
        assert str(error) == "MCP execution failed"

    def test_mcp_connection_error(self):
        """Test MCP connection error."""
        error = MCPConnectionError("Connection refused", server_url="http://localhost:8080")
        assert "Connection refused" in str(error)
        assert error.server_url == "http://localhost:8080"


class TestSkillErrors:
    """Test cases for skill exceptions."""

    def test_skill_error_basic(self):
        """Test basic skill error."""
        error = SkillError("Skill failed")
        assert str(error) == "Skill failed"

    def test_skill_error_with_name(self):
        """Test skill error with name."""
        error = SkillError("Load failed", tool_name="data_analysis")
        assert "data_analysis" in str(error)

    def test_skill_load_error(self):
        """Test skill load error."""
        error = SkillLoadError("Module not found", skill_name="missing_skill")
        assert "missing_skill" in str(error)

    def test_skill_not_found_error(self):
        """Test skill not found error."""
        error = SkillNotFoundError("unknown_skill")
        assert "unknown_skill" in str(error)
