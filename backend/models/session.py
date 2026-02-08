"""SQLAlchemy model for chat session management.

Epic 16: Chat Session State Management
"""

import enum
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.database.base import Base, TimestampMixin


class SessionStatus(str, enum.Enum):
    """Enumeration of session statuses."""

    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"
    RECOVERED = "recovered"


class ChatSession(Base, TimestampMixin):
    """Model for chat session state management.

    Sessions represent active chat connections with a user, tracking
    connection state, metadata, and expiration for recovery purposes.
    """

    __tablename__ = "chat_sessions"

    # Primary key using UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Session identifier (unique per session)
    session_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # Reference to the user who owns this session
    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )

    # Reference to the task this session is for
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Thread ID for this session
    thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="default",
    )

    # Session status
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status_enum"),
        nullable=False,
        default=SessionStatus.ACTIVE,
        index=True,
    )

    # Session metadata (client info, user agent, etc.)
    meta: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Last activity timestamp for timeout handling
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Expiration timestamp (2 hours default)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(hours=2),
    )

    # Connection count (for concurrent session tracking)
    connection_count: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )

    # Recovery token for session resumption
    recovery_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    # Recovered from session ID (for tracking recovery chain)
    recovered_from_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    task: Mapped[Optional["Task"]] = relationship(  # type: ignore # noqa: F821
        "Task",
        back_populates="sessions",
        foreign_keys=[task_id],
    )

    # Table constraints
    __table_args__ = (
        Index("ix_sessions_user_status", "user_id", "status"),
        Index("ix_sessions_task_thread", "task_id", "thread_id"),
        Index("ix_sessions_expires_at", "expires_at"),
        Index("ix_sessions_last_activity", "last_activity_at"),
    )

    @validates("session_id")
    def validate_session_id(self, key: str, session_id: str) -> str:
        """Validate session ID format."""
        if not session_id:
            raise ValueError("Session ID cannot be empty")
        if len(session_id) > 255:
            raise ValueError("Session ID cannot exceed 255 characters")
        return session_id

    @validates("connection_count")
    def validate_connection_count(self, key: str, count: int) -> int:
        """Validate connection count."""
        if count < 0:
            raise ValueError("Connection count cannot be negative")
        return count

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        """Check if the session is active and not expired."""
        return self.status == SessionStatus.ACTIVE and not self.is_expired()

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity_at = datetime.utcnow()

    def expire(self) -> None:
        """Mark the session as expired."""
        self.status = SessionStatus.EXPIRED

    def close(self) -> None:
        """Mark the session as closed."""
        self.status = SessionStatus.CLOSED

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, session_id={self.session_id}, user_id={self.user_id}, status={self.status.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary representation."""
        return {
            "id": str(self.id),
            "sessionId": self.session_id,
            "userId": self.user_id,
            "taskId": str(self.task_id) if self.task_id else None,
            "threadId": self.thread_id,
            "status": self.status.value,
            "meta": self.meta,
            "connectionCount": self.connection_count,
            "lastActivityAt": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
