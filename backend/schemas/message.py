"""Pydantic schemas for Message resources.

Message resources represent chat message history for tasks.

Epic 15: Message History Management
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.messages import MessageRole, MessageType


class MessageCreateRequest(BaseModel):
    """Request schema for creating a Message.

    Used internally by the message service and WebSocket handler.
    """

    model_config = ConfigDict(populate_by_name=True)

    task_id: UUID = Field(
        ...,
        alias="taskId",
        description="Task ID this message belongs to",
    )
    role: MessageRole = Field(
        ...,
        description="Message role (user, assistant, system, tool)",
    )
    content: str = Field(
        ...,
        min_length=0,
        description="Message content",
    )
    message_type: MessageType = Field(
        default=MessageType.TEXT,
        alias="messageType",
        description="Message type",
    )
    thread_id: Optional[str] = Field(
        default="default",
        alias="threadId",
        description="Thread ID for session persistence",
    )
    sequence: Optional[int] = Field(
        default=None,
        description="Sequence number for ordering (auto-assigned if not provided)",
    )
    tokens_used: Optional[int] = Field(
        default=None,
        alias="tokensUsed",
        description="Total tokens used",
    )
    prompt_tokens: Optional[int] = Field(
        default=None,
        alias="promptTokens",
        description="Prompt tokens used",
    )
    completion_tokens: Optional[int] = Field(
        default=None,
        alias="completionTokens",
        description="Completion tokens used",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model used for generation",
    )
    tool_name: Optional[str] = Field(
        default=None,
        alias="toolName",
        description="Tool name for tool messages",
    )
    tool_call_id: Optional[str] = Field(
        default=None,
        alias="toolCallId",
        description="Tool call ID for tool messages",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata",
    )


class MessageResponse(BaseModel):
    """Response schema for Message resources.

    Returned by API endpoints with full message details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the message",
    )
    task_id: UUID = Field(
        ...,
        alias="taskId",
        description="Task ID this message belongs to",
    )
    role: MessageRole = Field(
        ...,
        description="Message role",
    )
    message_type: MessageType = Field(
        ...,
        alias="messageType",
        description="Message type",
    )
    content: str = Field(
        ...,
        description="Message content",
    )
    thread_id: str = Field(
        ...,
        alias="threadId",
        description="Thread ID",
    )
    sequence: int = Field(
        ...,
        description="Sequence number for ordering",
    )
    tokens_used: Optional[int] = Field(
        default=None,
        alias="tokensUsed",
        description="Total tokens used",
    )
    prompt_tokens: Optional[int] = Field(
        default=None,
        alias="promptTokens",
        description="Prompt tokens used",
    )
    completion_tokens: Optional[int] = Field(
        default=None,
        alias="completionTokens",
        description="Completion tokens used",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model used for generation",
    )
    tool_name: Optional[str] = Field(
        default=None,
        alias="toolName",
        description="Tool name",
    )
    tool_call_id: Optional[str] = Field(
        default=None,
        alias="toolCallId",
        description="Tool call ID",
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    generated_at: Optional[datetime] = Field(
        default=None,
        alias="generatedAt",
        description="When the message was generated",
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="When message was created",
    )
    updated_at: datetime = Field(
        ...,
        alias="updatedAt",
        description="When message was last updated",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "MessageResponse":
        """Create MessageResponse from database Message model.

        Args:
            db_model: Message model instance from database.

        Returns:
            MessageResponse instance populated from database model.
        """
        return cls(
            id=db_model.id,
            task_id=db_model.task_id,
            role=db_model.role,
            message_type=db_model.message_type,
            content=db_model.content,
            thread_id=db_model.thread_id,
            sequence=db_model.sequence,
            tokens_used=db_model.tokens_used,
            prompt_tokens=db_model.prompt_tokens,
            completion_tokens=db_model.completion_tokens,
            model=db_model.model,
            tool_name=db_model.tool_name,
            tool_call_id=db_model.tool_call_id,
            meta=db_model.meta,
            generated_at=db_model.generated_at,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )


class MessageHistoryRequest(BaseModel):
    """Request schema for retrieving message history.

    Used for pagination and filtering.
    """

    model_config = ConfigDict(populate_by_name=True)

    thread_id: Optional[str] = Field(
        default=None,
        alias="threadId",
        description="Filter by thread ID (default: all threads)",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of messages to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of messages to skip",
    )
    before_sequence: Optional[int] = Field(
        default=None,
        alias="beforeSequence",
        description="Get messages before this sequence number",
    )
    after_sequence: Optional[int] = Field(
        default=None,
        alias="afterSequence",
        description="Get messages after this sequence number",
    )


class MessageHistoryResponse(BaseModel):
    """Response schema for message history.

    Includes messages and pagination info.
    """

    model_config = ConfigDict(populate_by_name=True)

    task_id: UUID = Field(
        ...,
        alias="taskId",
        description="Task ID",
    )
    thread_id: Optional[str] = Field(
        default=None,
        alias="threadId",
        description="Thread ID (if filtered)",
    )
    messages: List[MessageResponse] = Field(
        default_factory=list,
        description="List of messages",
    )
    total: int = Field(
        ...,
        description="Total number of messages matching the query",
    )
    limit: int = Field(
        ...,
        description="Limit used for the query",
    )
    offset: int = Field(
        ...,
        description="Offset used for the query",
    )
    has_more: bool = Field(
        ...,
        alias="hasMore",
        description="Whether there are more messages available",
    )


class MessageHistorySyncEvent(BaseModel):
    """WebSocket event for history synchronization.

    Sent to clients when they request message history.
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        default="history:sync",
        description="Event type",
    )
    task_id: UUID = Field(
        ...,
        alias="taskId",
        description="Task ID",
    )
    thread_id: str = Field(
        default="default",
        alias="threadId",
        description="Thread ID",
    )
    messages: List[MessageResponse] = Field(
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


class MessageHistoryRequestEvent(BaseModel):
    """WebSocket event for requesting message history.

    Sent by clients to request message history.
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        default="history:request",
        description="Event type",
    )
    thread_id: Optional[str] = Field(
        default=None,
        alias="threadId",
        description="Thread ID (default: default)",
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
