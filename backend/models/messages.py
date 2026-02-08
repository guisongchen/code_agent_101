"""SQLAlchemy model for chat message history.

Epic 15: Message History Management
"""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.database.base import Base, TimestampMixin


class MessageRole(str, enum.Enum):
    """Enumeration of message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(str, enum.Enum):
    """Enumeration of message types."""

    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
    ERROR = "error"


class Message(Base, TimestampMixin):
    """Model for chat message history.

    Messages represent individual chat interactions within a task,
    storing both user inputs and AI responses with metadata.
    """

    __tablename__ = "messages"

    # Primary key using UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Reference to the task this message belongs to
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message role (user, assistant, system, tool)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role_enum"),
        nullable=False,
        index=True,
    )

    # Message type (text, tool_call, tool_result, thinking, error)
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type_enum"),
        nullable=False,
        default=MessageType.TEXT,
        index=True,
    )

    # Message content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Thread ID for session persistence
    thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="default",
        index=True,
    )

    # Sequence number for ordering within a thread
    sequence: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        index=True,
    )

    # Token usage metadata
    tokens_used: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    prompt_tokens: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    completion_tokens: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    # Model used for generation (for assistant messages)
    model: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Tool-related fields (for tool_call and tool_result types)
    tool_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    tool_call_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Additional message metadata as JSON (using 'meta' to avoid SQLAlchemy reserved name)
    meta: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Timestamp for when the message was generated
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship(  # type: ignore # noqa: F821
        "Task",
        back_populates="messages",
        foreign_keys=[task_id],
    )

    # Table constraints
    __table_args__ = (
        Index("ix_messages_task_thread", "task_id", "thread_id"),
        Index("ix_messages_task_sequence", "task_id", "thread_id", "sequence"),
        Index("ix_messages_role_type", "role", "message_type"),
        Index("ix_messages_created_at", "created_at"),
    )

    @validates("content")
    def validate_content(self, key: str, content: str) -> str:
        """Validate message content."""
        if content is None:
            raise ValueError("Content cannot be None")
        return content

    @validates("sequence")
    def validate_sequence(self, key: str, sequence: int) -> int:
        """Validate sequence number."""
        if sequence < 0:
            raise ValueError("Sequence must be non-negative")
        return sequence

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, task_id={self.task_id}, role={self.role.value}, sequence={self.sequence})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary representation."""
        return {
            "id": str(self.id),
            "taskId": str(self.task_id),
            "role": self.role.value,
            "messageType": self.message_type.value,
            "content": self.content,
            "threadId": self.thread_id,
            "sequence": self.sequence,
            "tokensUsed": self.tokens_used,
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "model": self.model,
            "toolName": self.tool_name,
            "toolCallId": self.tool_call_id,
            "meta": self.meta,
            "generatedAt": self.generated_at.isoformat() if self.generated_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
