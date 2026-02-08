"""Pydantic schemas for WebSocket events.

Defines request and response models for WebSocket communication.

Epic 14: WebSocket Chat Endpoint
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Client -> Server Events
# =============================================================================


class ChatSendEvent(BaseModel):
    """Client event to send a chat message."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:send", description="Event type")
    message: str = Field(..., description="Message content to send")
    thread_id: Optional[str] = Field(
        default=None,
        alias="threadId",
        description="Thread ID for session persistence",
    )
    show_thinking: bool = Field(
        default=True,
        alias="showThinking",
        description="Whether to show thinking/tool call events",
    )


class ChatCancelEvent(BaseModel):
    """Client event to cancel ongoing generation."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:cancel", description="Event type")


class TaskJoinEvent(BaseModel):
    """Client event to join a task room."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="task:join", description="Event type")


class TaskLeaveEvent(BaseModel):
    """Client event to leave a task room."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="task:leave", description="Event type")


class PingEvent(BaseModel):
    """Client event for keep-alive ping."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="ping", description="Event type")


# =============================================================================
# Server -> Client Events
# =============================================================================


class ChatStartEvent(BaseModel):
    """Server event indicating AI started generating."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:start", description="Event type")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class ChatChunkEvent(BaseModel):
    """Server event with streaming content chunk."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:chunk", description="Event type")
    data: Dict[str, str] = Field(
        default_factory=dict,
        description="Event data containing 'text' field",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class ChatDoneEvent(BaseModel):
    """Server event indicating AI response completed."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:done", description="Event type")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class ChatErrorEvent(BaseModel):
    """Server event indicating an error occurred."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:error", description="Event type")
    data: Dict[str, str] = Field(
        default_factory=dict,
        description="Event data containing 'message' and 'error_code'",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class ChatCancelledEvent(BaseModel):
    """Server event indicating stream was cancelled."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:cancelled", description="Event type")
    data: Dict[str, str] = Field(
        default_factory=dict,
        description="Event data containing 'reason'",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class ChatToolStartEvent(BaseModel):
    """Server event indicating tool execution started."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:tool_start", description="Event type")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event data containing 'tool' and 'input'",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class ChatToolResultEvent(BaseModel):
    """Server event with tool execution result."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:tool_result", description="Event type")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event data containing 'tool' and 'result'",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class ChatThinkingEvent(BaseModel):
    """Server event with agent thinking/thought process."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="chat:thinking", description="Event type")
    data: Dict[str, str] = Field(
        default_factory=dict,
        description="Event data containing 'text'",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp",
    )


class TaskStatusEvent(BaseModel):
    """Server event with task status update."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="task:status", description="Event type")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event data containing 'status', 'task_id', etc.",
    )


class PongEvent(BaseModel):
    """Server event for keep-alive pong response."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="pong", description="Event type")


class HistoryRequestEvent(BaseModel):
    """Client event to request message history."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="history:request", description="Event type")
    thread_id: Optional[str] = Field(
        default=None,
        alias="threadId",
        description="Thread ID to get history for",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of messages",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of messages to skip",
    )


class HistorySyncEvent(BaseModel):
    """Server event with message history."""

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(default="history:sync", description="Event type")
    task_id: str = Field(
        ...,
        alias="taskId",
        description="Task ID",
    )
    thread_id: str = Field(
        default="default",
        alias="threadId",
        description="Thread ID",
    )
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of messages",
    )
    total: int = Field(
        ...,
        description="Total number of messages",
    )
    has_more: bool = Field(
        ...,
        alias="hasMore",
        description="Whether there are more messages",
    )


# =============================================================================
# WebSocket Connection Info
# =============================================================================


class WebSocketConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""

    model_config = ConfigDict(populate_by_name=True)

    task_id: str = Field(
        ...,
        alias="taskId",
        description="Task ID for the connection",
    )
    client_count: int = Field(
        default=1,
        alias="clientCount",
        description="Number of connected clients",
    )
    user_id: Optional[int] = Field(
        default=None,
        alias="userId",
        description="User ID for the connection",
    )
    username: Optional[str] = Field(
        default=None,
        description="Username for the connection",
    )
    connected_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        alias="connectedAt",
        description="Connection timestamp",
    )


class RoomInfo(BaseModel):
    """Information about a task room."""

    model_config = ConfigDict(populate_by_name=True)

    task_id: str = Field(
        ...,
        alias="taskId",
        description="Task ID for the room",
    )
    client_count: int = Field(
        ...,
        alias="clientCount",
        description="Number of connected clients",
    )
    created_at: float = Field(
        ...,
        alias="createdAt",
        description="Room creation timestamp (Unix time)",
    )
