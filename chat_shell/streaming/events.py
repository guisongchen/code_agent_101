"""
Streaming event type definitions with offset/sequence tracking.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for streaming responses."""

    CHUNK = "chunk"  # Token-level content chunk
    TOOL_START = "tool_start"  # Tool execution start
    TOOL_RESULT = "tool_result"  # Tool execution completion
    THINKING = "thinking"  # Model thinking process
    OFFSET = "offset"  # Recovery checkpoint event
    ERROR = "error"  # Structured error information
    COMPLETE = "complete"  # Stream completion
    CANCELLED = "cancelled"  # Stream cancellation


class BaseStreamEvent(BaseModel, ABC):
    """Abstract base for all stream events.

    Attributes:
        event_type: The type of event
        offset: Sequential offset for ordering and recovery
        timestamp: Event creation time
        session_id: Associated session identifier
        sequence: Global sequence number across all events
    """

    event_type: EventType
    offset: int = Field(..., description="Sequential offset for ordering and recovery")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = Field(None, description="Associated session identifier")
    sequence: Optional[int] = Field(None, description="Global sequence number")

    class Config:
        frozen = True  # Immutable events

    @abstractmethod
    def to_sse_payload(self) -> Dict[str, Any]:
        """Convert event to SSE payload format."""
        pass

    def to_sse_line(self) -> str:
        """Convert event to SSE formatted line."""
        import json

        payload = self.to_sse_payload()
        event_type_value = self.event_type.value if isinstance(self.event_type, Enum) else self.event_type
        return f"event: {event_type_value}\ndata: {json.dumps(payload)}\n\n"


class ChunkEvent(BaseStreamEvent):
    """Token-level streaming event with text chunks.

    Attributes:
        text: The text chunk content
        is_delta: Whether this is a delta or absolute content
        token_count: Number of tokens in this chunk (if known)
    """

    event_type: EventType = Field(EventType.CHUNK, frozen=True)
    text: str = Field(..., description="Text chunk content")
    is_delta: bool = Field(True, description="Whether this is a delta update")
    token_count: Optional[int] = Field(None, description="Number of tokens in chunk")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "text": self.text,
                "is_delta": self.is_delta,
                "token_count": self.token_count,
            },
        }


class ToolStartEvent(BaseStreamEvent):
    """Tool execution start event.

    Attributes:
        tool_name: Name of the tool being called
        tool_input: Input arguments for the tool
        tool_call_id: Unique identifier for this tool call
    """

    event_type: EventType = Field(EventType.TOOL_START, frozen=True)
    tool_name: str = Field(..., description="Name of the tool being called")
    tool_input: Dict[str, Any] = Field(default_factory=dict, description="Tool input arguments")
    tool_call_id: str = Field(..., description="Unique tool call identifier")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "tool_name": self.tool_name,
                "tool_input": self.tool_input,
                "tool_call_id": self.tool_call_id,
            },
        }


class ToolResultEvent(BaseStreamEvent):
    """Tool execution completion event.

    Attributes:
        tool_name: Name of the tool that was executed
        tool_call_id: Unique identifier for this tool call
        result: The tool execution result
        execution_time_ms: Time taken to execute the tool (if known)
        error: Error message if tool execution failed
    """

    event_type: EventType = Field(EventType.TOOL_RESULT, frozen=True)
    tool_name: str = Field(..., description="Name of the tool that was executed")
    tool_call_id: str = Field(..., description="Unique tool call identifier")
    result: Any = Field(None, description="Tool execution result")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if execution failed")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "tool_name": self.tool_name,
                "tool_call_id": self.tool_call_id,
                "result": self.result,
                "execution_time_ms": self.execution_time_ms,
                "error": self.error,
            },
        }


class ThinkingEvent(BaseStreamEvent):
    """Model thinking process event.

    Attributes:
        text: The thinking/reasoning content
        step: Optional step identifier for multi-step thinking
    """

    event_type: EventType = Field(EventType.THINKING, frozen=True)
    text: str = Field(..., description="Thinking/reasoning content")
    step: Optional[str] = Field(None, description="Step identifier for multi-step thinking")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "text": self.text,
                "step": self.step,
            },
        }


class StreamOffsetEvent(BaseStreamEvent):
    """Recovery checkpoint event for stream resumption.

    Attributes:
        checkpoint_data: Opaque data needed to resume from this offset
        is_recoverable: Whether this checkpoint supports recovery
    """

    event_type: EventType = Field(EventType.OFFSET, frozen=True)
    checkpoint_data: Dict[str, Any] = Field(
        default_factory=dict, description="Opaque data for stream resumption"
    )
    is_recoverable: bool = Field(True, description="Whether this checkpoint supports recovery")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "checkpoint_data": self.checkpoint_data,
                "is_recoverable": self.is_recoverable,
            },
        }


class ErrorEvent(BaseStreamEvent):
    """Structured error information event.

    Attributes:
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Additional error details
        is_recoverable: Whether the stream can continue after this error
    """

    event_type: EventType = Field(EventType.ERROR, frozen=True)
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    is_recoverable: bool = Field(False, description="Whether stream can continue")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "error_code": self.error_code,
                "message": self.message,
                "details": self.details,
                "is_recoverable": self.is_recoverable,
            },
        }


class CompleteEvent(BaseStreamEvent):
    """Stream completion event.

    Attributes:
        final_offset: The final offset of the completed stream
        total_tokens: Total token count if available
        finish_reason: Reason for completion (e.g., 'stop', 'length')
    """

    event_type: EventType = Field(EventType.COMPLETE, frozen=True)
    final_offset: int = Field(..., description="Final offset of the completed stream")
    total_tokens: Optional[int] = Field(None, description="Total token count")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "final_offset": self.final_offset,
                "total_tokens": self.total_tokens,
                "finish_reason": self.finish_reason,
            },
        }


class CancelledEvent(BaseStreamEvent):
    """Stream cancellation event.

    Attributes:
        reason: Reason for cancellation
        cancelled_at_offset: Offset at which cancellation occurred
    """

    event_type: EventType = Field(EventType.CANCELLED, frozen=True)
    reason: Optional[str] = Field(None, description="Reason for cancellation")
    cancelled_at_offset: int = Field(..., description="Offset at cancellation")

    def to_sse_payload(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "offset": self.offset,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "sequence": self.sequence,
            "data": {
                "reason": self.reason,
                "cancelled_at_offset": self.cancelled_at_offset,
            },
        }


# Union type for all events
StreamEvent = ChunkEvent | ToolStartEvent | ToolResultEvent | ThinkingEvent | StreamOffsetEvent | ErrorEvent | CompleteEvent | CancelledEvent
