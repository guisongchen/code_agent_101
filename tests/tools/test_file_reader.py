"""
Tests for FileReaderTool - Epic 3: Tools System.
"""

import json
import tempfile
from pathlib import Path

import pytest
from chat_shell.tools.file_reader import FileReaderTool, FileReaderInput


pytestmark = [pytest.mark.unit, pytest.mark.epic_3]


class TestFileReaderTool:
    """Test cases for FileReaderTool."""

    @pytest.fixture
    def tool(self):
        return FileReaderTool()

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_tool_attributes(self, tool):
        """Test tool has correct attributes."""
        assert tool.name == "file_reader"
        assert "Read and extract content" in tool.description

    def test_supported_extensions(self, tool):
        """Test supported file extensions."""
        assert '.txt' in tool.SUPPORTED_EXTENSIONS
        assert '.json' in tool.SUPPORTED_EXTENSIONS
        assert '.csv' in tool.SUPPORTED_EXTENSIONS
        assert '.pdf' in tool.SUPPORTED_EXTENSIONS
        assert '.docx' in tool.SUPPORTED_EXTENSIONS

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, tool):
        """Test reading nonexistent file returns error."""
        input_data = FileReaderInput(file_path="/nonexistent/file.txt")
        result = await tool.execute(input_data)

        assert result.error is not None or result.result == ""
        assert "not found" in result.error.lower() or "File not found" in result.error

    @pytest.mark.asyncio
    async def test_read_unsupported_file(self, tool, temp_dir):
        """Test reading unsupported file type returns error."""
        file_path = temp_dir / "test.xyz"
        file_path.write_text("content")

        input_data = FileReaderInput(file_path=str(file_path))
        result = await tool.execute(input_data)

        assert "unsupported" in result.error.lower()

    @pytest.mark.asyncio
    async def test_read_text_file(self, tool, temp_dir):
        """Test reading text file."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Hello, World!\nThis is a test.")

        input_data = FileReaderInput(file_path=str(file_path))
        result = await tool.execute(input_data)

        assert "Hello, World!" in result.result
        assert "error" not in result.error.lower() or result.error == ""

    @pytest.mark.asyncio
    async def test_read_json_file(self, tool, temp_dir):
        """Test reading JSON file."""
        file_path = temp_dir / "test.json"
        data = {"name": "test", "value": 42}
        file_path.write_text(json.dumps(data))

        input_data = FileReaderInput(file_path=str(file_path))
        result = await tool.execute(input_data)

        assert '"name": "test"' in result.result or '"name": "test"' in result.result.replace("'", '"')

    @pytest.mark.asyncio
    async def test_read_with_max_lines(self, tool, temp_dir):
        """Test reading with max_lines limit."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

        input_data = FileReaderInput(file_path=str(file_path), max_lines=2)
        result = await tool.execute(input_data)

        assert "Line 1" in result.result
        assert "Line 2" in result.result
        assert "truncated" in result.result.lower() or "Line 3" not in result.result

    @pytest.mark.asyncio
    async def test_read_markdown_file(self, tool, temp_dir):
        """Test reading markdown file."""
        file_path = temp_dir / "test.md"
        file_path.write_text("# Heading\n\nSome content here.")

        input_data = FileReaderInput(file_path=str(file_path))
        result = await tool.execute(input_data)

        assert "# Heading" in result.result
