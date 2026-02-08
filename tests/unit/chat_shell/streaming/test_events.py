"""
Tests for streaming events module.
"""

import json
import pytest
from datetime import datetime

from chat_shell.streaming.events import (
    BaseStreamEvent,
    ChunkEvent,
    ToolStartEvent,
    ToolResultEvent,
    ThinkingEvent,
    StreamOffsetEvent,
    ErrorEvent,
    CompleteEvent,
    CancelledEvent,
    EventType,
)


class TestChunkEvent:
    """Tests for ChunkEvent."""

    def test_create_chunk_event(self):
        """Test creating a chunk event."""
        event = ChunkEvent(
            offset=0,
            session_id="test-session",
            text="Hello",
            is_delta=True,
            token_count=1,
        )

        assert event.event_type == EventType.CHUNK
        assert event.offset == 0
        assert event.session_id == "test-session"
        assert event.text == "Hello"
        assert event.is_delta is True
        assert event.token_count == 1

    def test_chunk_event_to_sse_payload(self):
        """Test converting chunk event to SSE payload."""
        event = ChunkEvent(
            offset=5,
            session_id="test-session",
            text="World",
            is_delta=True,
        )

        payload = event.to_sse_payload()

        assert payload["type"] == "chunk"
        assert payload["offset"] == 5
        assert payload["session_id"] == "test-session"
        assert payload["data"]["text"] == "World"
        assert payload["data"]["is_delta"] is True

    def test_chunk_event_to_sse_line(self):
        """Test converting chunk event to SSE line format."""
        event = ChunkEvent(
            offset=0,
            session_id="test-session",
            text="Hello",
            is_delta=True,
        )

        line = event.to_sse_line()

        assert line.startswith("event: chunk")
        assert "data:" in line


class TestToolStartEvent:
    """Tests for ToolStartEvent."""

    def test_create_tool_start_event(self):
        """Test creating a tool start event."""
        event = ToolStartEvent(
            offset=10,
            session_id="test-session",
            tool_name="calculator",
            tool_input={"expression": "1 + 1"},
            tool_call_id="call-123",
        )

        assert event.event_type == EventType.TOOL_START
        assert event.offset == 10
        assert event.tool_name == "calculator"
        assert event.tool_input == {"expression": "1 + 1"}
        assert event.tool_call_id == "call-123"

    def test_tool_start_sse_payload(self):
        """Test tool start event SSE payload."""
        event = ToolStartEvent(
            offset=10,
            session_id="test-session",
            tool_name="calculator",
            tool_input={"expression": "1 + 1"},
            tool_call_id="call-123",
        )

        payload = event.to_sse_payload()

        assert payload["type"] == "tool_start"
        assert payload["data"]["tool_name"] == "calculator"
        assert payload["data"]["tool_input"]["expression"] == "1 + 1"
        assert payload["data"]["tool_call_id"] == "call-123"


class TestToolResultEvent:
    """Tests for ToolResultEvent."""

    def test_create_tool_result_event(self):
        """Test creating a tool result event."""
        event = ToolResultEvent(
            offset=15,
            session_id="test-session",
            tool_name="calculator",
            tool_call_id="call-123",
            result=2,
            execution_time_ms=50.0,
        )

        assert event.event_type == EventType.TOOL_RESULT
        assert event.result == 2
        assert event.execution_time_ms == 50.0
        assert event.error is None

    def test_tool_result_with_error(self):
        """Test tool result event with error."""
        event = ToolResultEvent(
            offset=15,
            session_id="test-session",
            tool_name="calculator",
            tool_call_id="call-123",
            error="Division by zero",
        )

        assert event.error == "Division by zero"
        assert event.result is None


class TestThinkingEvent:
    """Tests for ThinkingEvent."""

    def test_create_thinking_event(self):
        """Test creating a thinking event."""
        event = ThinkingEvent(
            offset=20,
            session_id="test-session",
            text="I need to calculate this...",
            step="analysis",
        )

        assert event.event_type == EventType.THINKING
        assert event.text == "I need to calculate this..."
        assert event.step == "analysis"


class TestStreamOffsetEvent:
    """Tests for StreamOffsetEvent."""

    def test_create_offset_event(self):
        """Test creating an offset checkpoint event."""
        event = StreamOffsetEvent(
            offset=100,
            session_id="test-session",
            checkpoint_data={"last_event_offset": 99},
            is_recoverable=True,
        )

        assert event.event_type == EventType.OFFSET
        assert event.checkpoint_data["last_event_offset"] == 99
        assert event.is_recoverable is True


class TestErrorEvent:
    """Tests for ErrorEvent."""

    def test_create_error_event(self):
        """Test creating an error event."""
        event = ErrorEvent(
            offset=50,
            session_id="test-session",
            error_code="TOOL_ERROR",
            message="Tool execution failed",
            details={"tool_name": "calculator"},
            is_recoverable=False,
        )

        assert event.event_type == EventType.ERROR
        assert event.error_code == "TOOL_ERROR"
        assert event.message == "Tool execution failed"
        assert event.details["tool_name"] == "calculator"
        assert event.is_recoverable is False

    def test_error_event_sse_payload(self):
        """Test error event SSE payload structure."""
        event = ErrorEvent(
            offset=50,
            session_id="test-session",
            error_code="STREAM_ERROR",
            message="Something went wrong",
        )

        payload = event.to_sse_payload()

        assert payload["data"]["error_code"] == "STREAM_ERROR"
        assert payload["data"]["message"] == "Something went wrong"
        assert payload["data"]["is_recoverable"] is False  # Default


class TestCompleteEvent:
    """Tests for CompleteEvent."""

    def test_create_complete_event(self):
        """Test creating a complete event."""
        event = CompleteEvent(
            offset=200,
            session_id="test-session",
            final_offset=199,
            total_tokens=150,
            finish_reason="stop",
        )

        assert event.event_type == EventType.COMPLETE
        assert event.final_offset == 199
        assert event.total_tokens == 150
        assert event.finish_reason == "stop"


class TestCancelledEvent:
    """Tests for CancelledEvent."""

    def test_create_cancelled_event(self):
        """Test creating a cancelled event."""
        event = CancelledEvent(
            offset=75,
            session_id="test-session",
            reason="User requested cancellation",
            cancelled_at_offset=74,
        )

        assert event.event_type == EventType.CANCELLED
        assert event.reason == "User requested cancellation"
        assert event.cancelled_at_offset == 74


class TestEventImmutability:
    """Tests for event immutability."""

    def test_events_are_frozen(self):
        """Test that events are immutable."""
        event = ChunkEvent(
            offset=0,
            session_id="test",
            text="Hello",
        )

        with pytest.raises(Exception):  # pydantic.ValidationError or TypeError
            event.text = "World"


class TestEventSerialization:
    """Tests for event serialization."""

    def test_event_timestamp_in_payload(self):
        """Test that timestamp is included in payload."""
        event = ChunkEvent(
            offset=0,
            session_id="test",
            text="Hello",
        )

        payload = event.to_sse_payload()

        assert "timestamp" in payload
        # Should be ISO format string
        assert isinstance(payload["timestamp"], str)

    def test_event_sequence_in_payload(self):
        """Test that sequence number is included in payload."""
        event = ChunkEvent(
            offset=0,
            session_id="test",
            text="Hello",
            sequence=42,
        )

        payload = event.to_sse_payload()

        assert payload["sequence"] == 42

    def test_sse_line_valid_json(self):
        """Test that SSE line contains valid JSON data."""
        event = ChunkEvent(
            offset=0,
            session_id="test",
            text="Hello",
        )

        line = event.to_sse_line()

        # Extract data part
        lines = line.strip().split("\n")
        data_lines = [l for l in lines if l.startswith("data: ")]

        assert len(data_lines) > 0

        # Combine data lines and parse
        data_str = "\n".join(l[6:] for l in data_lines)
        data = json.loads(data_str)

        assert data["type"] == "chunk"
        assert data["data"]["text"] == "Hello"


pytestmark = [pytest.mark.unit, pytest.mark.chat_shell]
