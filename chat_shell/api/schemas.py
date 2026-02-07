"""
API schemas for HTTP mode.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A chat message."""

    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request to start a chat session."""

    messages: List[ChatMessage] = Field(..., description="Initial messages")
    session_id: Optional[str] = Field(None, description="Optional session ID")
    model: Optional[str] = Field(None, description="Model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(4096, ge=1)
    tools: Optional[List[str]] = Field(None, description="Tools to enable")
    stream: bool = Field(True, description="Enable streaming response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    offset: Optional[int] = Field(None, description="Offset to resume from for stream recovery")


class ChatResponse(BaseModel):
    """Response from chat session creation."""

    subtask_id: str = Field(..., description="Unique task ID for this session")
    session_id: str = Field(..., description="Session identifier")
    status: Literal["created", "running", "completed", "error"] = "created"
    created_at: datetime = Field(default_factory=datetime.now)


class ChatEvent(BaseModel):
    """A streaming event from the chat session."""

    event_type: Literal[
        "content",  # Token-level content
        "tool_call",  # Tool execution start
        "tool_result",  # Tool execution result
        "thinking",  # Thinking process
        "error",  # Error event
        "complete",  # Session complete
        "cancelled",  # Session cancelled
        "offset",  # Recovery checkpoint
    ]
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    offset: Optional[int] = Field(None, description="Event offset for ordering and recovery")
    sequence: Optional[int] = Field(None, description="Global sequence number")


class SessionStatus(BaseModel):
    """Status of a chat session."""

    subtask_id: str
    session_id: str
    status: Literal["pending", "running", "completed", "error", "cancelled"]
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class SessionHistory(BaseModel):
    """History of a session."""

    session_id: str
    messages: List[ChatMessage]
    total_messages: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    active_sessions: int
    models_available: List[str]


class ErrorResponse(BaseModel):
    """Error response."""

    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class StreamRecoveryRequest(BaseModel):
    """Request to recover a stream from a specific offset."""

    stream_id: str = Field(..., description="Stream to recover")
    offset: int = Field(..., description="Offset to resume from")
    client_id: Optional[str] = Field(None, description="Client ID for tracking")


class StreamRecoveryResponse(BaseModel):
    """Response for stream recovery request."""

    stream_id: str
    can_recover: bool
    from_offset: int
    available_offsets: Dict[str, Any]
    message: Optional[str] = None


class StreamStatusExtended(BaseModel):
    """Extended stream status with buffer and recovery info."""

    stream_id: str
    session_id: str
    status: Literal["pending", "running", "completed", "error", "cancelled"]
    current_offset: int
    created_at: str
    updated_at: str
    buffer: Dict[str, Any]
    client_count: int
