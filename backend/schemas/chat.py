"""Pydantic schemas for Chat API.

Defines request and response models for chat execution endpoints.

Epic 13: Chat Shell Integration
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatMessage(BaseModel):
    """A single chat message.

    Represents one message in a conversation with role and content.
    """

    model_config = ConfigDict(populate_by_name=True)

    role: str = Field(
        ...,
        description="Message role (system, user, assistant, tool)",
        examples=["user", "assistant", "system"],
    )
    content: str = Field(
        ...,
        description="Message content/text",
        examples=["Hello!", "How can I help you?"],
    )
    name: Optional[str] = Field(
        default=None,
        description="Optional name for the message sender (for tool messages)",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values."""
        allowed_roles = {"system", "user", "assistant", "tool"}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}, got {v}")
        return v


class ChatRequest(BaseModel):
    """Request schema for chat execution.

    Used in POST /api/v1/chat/{bot_name} endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    messages: List[ChatMessage] = Field(
        ...,
        min_length=1,
        description="List of chat messages (must include at least one message)",
    )
    thread_id: Optional[str] = Field(
        default=None,
        alias="threadId",
        description="Optional thread ID for session persistence",
    )
    stream: bool = Field(
        default=True,
        description="Whether to stream the response (default: true)",
    )
    show_thinking: bool = Field(
        default=True,
        alias="showThinking",
        description="Whether to include thinking/tool call events in stream",
    )

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: List[ChatMessage]) -> List[ChatMessage]:
        """Validate messages list is not empty."""
        if not v:
            raise ValueError("At least one message is required")
        return v


class ChatEvent(BaseModel):
    """A single chat event from streaming response.

    Represents one event in a chat stream (content, tool call, etc.).
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        ...,
        description="Event type (content, tool_call, tool_result, thinking, error, done)",
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data payload",
    )


class ChatResponse(BaseModel):
    """Response schema for non-streaming chat execution.

    Contains the complete chat response with content and metadata.
    """

    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(
        ...,
        description="Complete response content from the AI",
    )
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        alias="toolCalls",
        description="List of tool calls made during execution",
    )
    thinking: Optional[str] = Field(
        default=None,
        description="Agent's thinking process if show_thinking was enabled",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed",
    )
    bot_name: str = Field(
        ...,
        alias="botName",
        description="Name of the Bot used for this chat",
    )
    namespace: str = Field(
        default="default",
        description="Namespace of the Bot",
    )
    thread_id: Optional[str] = Field(
        default=None,
        alias="threadId",
        description="Thread ID for session persistence",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model used for this response",
    )
    usage: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token usage statistics if available",
    )


class ChatValidationResponse(BaseModel):
    """Response schema for bot configuration validation.

    Contains validation results for a Bot's chat configuration.
    """

    model_config = ConfigDict(populate_by_name=True)

    valid: bool = Field(
        ...,
        description="Whether the configuration is valid",
    )
    bot_name: str = Field(
        ...,
        alias="botName",
        description="Name of the validated Bot",
    )
    namespace: str = Field(
        default="default",
        description="Namespace of the Bot",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of validation warnings",
    )
    ghost: Optional[str] = Field(
        default=None,
        description="Name of the Ghost resource used",
    )
    model: Optional[str] = Field(
        default=None,
        description="Name of the Model resource used",
    )
    shell: Optional[str] = Field(
        default=None,
        description="Name of the Shell resource used",
    )


class ChatSessionInfo(BaseModel):
    """Information about a chat session.

    Used for listing active chat sessions.
    """

    model_config = ConfigDict(populate_by_name=True)

    thread_id: str = Field(
        ...,
        alias="threadId",
        description="Unique thread identifier",
    )
    bot_name: str = Field(
        ...,
        alias="botName",
        description="Bot used in this session",
    )
    namespace: str = Field(
        default="default",
        description="Namespace of the Bot",
    )
    message_count: int = Field(
        default=0,
        alias="messageCount",
        description="Number of messages in the session",
    )
    created_at: Optional[str] = Field(
        default=None,
        alias="createdAt",
        description="Session creation timestamp",
    )
    last_activity: Optional[str] = Field(
        default=None,
        alias="lastActivity",
        description="Last activity timestamp",
    )
