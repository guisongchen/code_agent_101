"""
Tests for MessageConverter - Epic 2: Multi-Model LLM Integration.
"""

import pytest
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)

from chat_shell_101.models.converter import MessageConverter
from chat_shell_101.models.exceptions import MessageConversionError


pytestmark = [pytest.mark.unit, pytest.mark.epic_2]


class TestMessageConverterOpenAI:
    """Test cases for OpenAI format conversion."""

    def test_convert_system_message(self):
        """Test converting system message."""
        messages = [SystemMessage(content="You are helpful.")]
        result = MessageConverter.to_openai_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful."

    def test_convert_human_message(self):
        """Test converting human message."""
        messages = [HumanMessage(content="Hello")]
        result = MessageConverter.to_openai_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"

    def test_convert_ai_message(self):
        """Test converting AI message."""
        messages = [AIMessage(content="Hi there")]
        result = MessageConverter.to_openai_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Hi there"

    def test_convert_ai_message_with_tool_calls(self):
        """Test converting AI message with tool calls."""
        messages = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_123",
                        "name": "calculator",
                        "args": {"expression": "2+2"},
                    }
                ],
            )
        ]
        result = MessageConverter.to_openai_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert "tool_calls" in result[0]
        assert len(result[0]["tool_calls"]) == 1
        assert result[0]["tool_calls"][0]["id"] == "call_123"

    def test_convert_tool_message(self):
        """Test converting tool message."""
        messages = [ToolMessage(content="4", tool_call_id="call_123")]
        result = MessageConverter.to_openai_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "tool"
        assert result[0]["content"] == "4"
        assert result[0]["tool_call_id"] == "call_123"

    def test_convert_mixed_messages(self):
        """Test converting a mix of message types."""
        messages = [
            SystemMessage(content="System"),
            HumanMessage(content="User"),
            AIMessage(content="Assistant"),
        ]
        result = MessageConverter.to_openai_format(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"


class TestMessageConverterAnthropic:
    """Test cases for Anthropic format conversion."""

    def test_convert_basic_messages(self):
        """Test converting basic messages."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
        ]
        result = MessageConverter.to_anthropic_format(messages)

        assert "messages" in result
        assert "system" not in result

        msgs = result["messages"]
        assert len(msgs) == 2
        assert msgs[0]["role"] == "human"
        assert msgs[0]["content"] == "Hello"
        assert msgs[1]["role"] == "assistant"
        assert msgs[1]["content"] == "Hi there"

    def test_convert_with_system_message(self):
        """Test converting with system message extraction."""
        messages = [
            SystemMessage(content="You are helpful."),
            HumanMessage(content="Hello"),
        ]
        result = MessageConverter.to_anthropic_format(messages)

        assert result["system"] == "You are helpful."
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "human"

    def test_convert_with_provided_system_prompt(self):
        """Test with explicitly provided system prompt."""
        messages = [
            SystemMessage(content="Ignored"),
            HumanMessage(content="Hello"),
        ]
        result = MessageConverter.to_anthropic_format(
            messages, system_prompt="Custom system"
        )

        # Provided system prompt takes precedence
        assert result["system"] == "Custom system"

    def test_convert_ai_message_with_tool_calls(self):
        """Test converting AI message with tool calls to Anthropic format."""
        messages = [
            AIMessage(
                content="Let me calculate",
                tool_calls=[
                    {
                        "id": "calc_123",
                        "name": "calculator",
                        "args": {"expression": "2+2"},
                    }
                ],
            )
        ]
        result = MessageConverter.to_anthropic_format(messages)

        msg = result["messages"][0]
        assert msg["role"] == "assistant"
        assert isinstance(msg["content"], list)
        assert len(msg["content"]) == 2
        assert msg["content"][0]["type"] == "text"
        assert msg["content"][1]["type"] == "tool_use"
        assert msg["content"][1]["name"] == "calculator"

    def test_convert_tool_message(self):
        """Test converting tool message to Anthropic format."""
        messages = [ToolMessage(content="4", tool_call_id="calc_123")]
        result = MessageConverter.to_anthropic_format(messages)

        msg = result["messages"][0]
        assert msg["role"] == "user"
        assert isinstance(msg["content"], list)
        assert msg["content"][0]["type"] == "tool_result"
        assert msg["content"][0]["tool_use_id"] == "calc_123"


class TestMessageConverterGoogle:
    """Test cases for Google format conversion."""

    def test_convert_human_message(self):
        """Test converting human message."""
        messages = [HumanMessage(content="Hello")]
        result = MessageConverter.to_google_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["parts"][0]["text"] == "Hello"

    def test_convert_ai_message(self):
        """Test converting AI message."""
        messages = [AIMessage(content="Hi there")]
        result = MessageConverter.to_google_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "model"
        assert result[0]["parts"][0]["text"] == "Hi there"

    def test_convert_system_message(self):
        """Test converting system message (converted to user)."""
        messages = [SystemMessage(content="You are helpful.")]
        result = MessageConverter.to_google_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "System instruction" in result[0]["parts"][0]["text"]

    def test_convert_tool_message(self):
        """Test converting tool message."""
        messages = [ToolMessage(content="Result", tool_call_id="tool_1")]
        result = MessageConverter.to_google_format(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "Tool result" in result[0]["parts"][0]["text"]


class TestMessageConverterValidation:
    """Test cases for message validation."""

    def test_validate_empty_messages(self):
        """Test that empty messages raises error."""
        with pytest.raises(MessageConversionError):
            MessageConverter.validate_messages([])

    def test_validate_valid_messages(self):
        """Test validation of valid messages."""
        messages = [
            SystemMessage(content="System"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi"),
        ]
        # Should not raise
        MessageConverter.validate_messages(messages)

    def test_validate_non_message_objects(self):
        """Test validation rejects non-message objects."""
        with pytest.raises(MessageConversionError):
            MessageConverter.validate_messages(["not a message"])

        with pytest.raises(MessageConversionError):
            MessageConverter.validate_messages([{"role": "user", "content": "test"}])


class TestMergeSystemMessages:
    """Test cases for merging system messages."""

    def test_merge_single_system_message(self):
        """Test extracting single system message."""
        messages = [
            SystemMessage(content="You are helpful."),
            HumanMessage(content="Hello"),
        ]
        system, non_system = MessageConverter.merge_system_messages(messages)

        assert system == "You are helpful."
        assert len(non_system) == 1
        assert isinstance(non_system[0], HumanMessage)

    def test_merge_multiple_system_messages(self):
        """Test merging multiple system messages."""
        messages = [
            SystemMessage(content="First instruction."),
            SystemMessage(content="Second instruction."),
            HumanMessage(content="Hello"),
        ]
        system, non_system = MessageConverter.merge_system_messages(messages)

        assert "First instruction." in system
        assert "Second instruction." in system
        assert len(non_system) == 1

    def test_merge_no_system_messages(self):
        """Test with no system messages."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi"),
        ]
        system, non_system = MessageConverter.merge_system_messages(messages)

        assert system is None
        assert len(non_system) == 2

    def test_merge_with_default_system(self):
        """Test with default system prompt."""
        messages = [HumanMessage(content="Hello")]
        system, non_system = MessageConverter.merge_system_messages(
            messages, default_system="Default prompt"
        )

        assert system == "Default prompt"
        assert len(non_system) == 1
