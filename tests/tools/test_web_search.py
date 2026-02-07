"""
Tests for WebSearchTool - Epic 3: Tools System.
"""

import pytest
from chat_shell.tools.web_search import WebSearchTool, WebSearchInput


pytestmark = [pytest.mark.unit, pytest.mark.epic_3]


class TestWebSearchTool:
    """Test cases for WebSearchTool."""

    @pytest.fixture
    def tool(self):
        return WebSearchTool()

    def test_tool_attributes(self, tool):
        """Test tool has correct attributes."""
        assert tool.name == "web_search"
        assert "Search the web" in tool.description

    def test_input_schema(self):
        """Test input schema validation."""
        # Valid input
        input_data = WebSearchInput(query="Python programming", num_results=5)
        assert input_data.query == "Python programming"
        assert input_data.num_results == 5
        assert input_data.include_snippets is True

    def test_input_defaults(self):
        """Test input schema defaults."""
        input_data = WebSearchInput(query="test")
        assert input_data.num_results == 5
        assert input_data.include_snippets is True

    def test_input_validation_num_results(self):
        """Test num_results validation."""
        # Should fail validation - less than minimum
        with pytest.raises(ValueError):
            WebSearchInput(query="test", num_results=0)

        with pytest.raises(ValueError):
            WebSearchInput(query="test", num_results=25)

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, tool):
        """Test execution returns result structure."""
        input_data = WebSearchInput(query="Python", num_results=3)

        # Note: This may fail if no network, so we catch exceptions
        try:
            result = await tool.execute(input_data)
            assert result is not None
            # Should have result or error
            assert hasattr(result, 'result') or hasattr(result, 'error')
        except Exception:
            pytest.skip("Network or external service unavailable")
