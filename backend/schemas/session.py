"""Pydantic schemas for Chat Session resources.

Session resources represent active chat sessions for session management.

Epic 16: Chat Session State Management
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.session import SessionStatus


class SessionCreateRequest(BaseModel):
    """Request schema for creating a Chat Session.

    Used when a new WebSocket connection is established.
    """

    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(
        ...,
        alias="userId",
        description="User ID who owns this session",
    )
    task_id: Optional[UUID] = Field(
        default=None,
        alias="taskId",
        description="Optional task ID this session is for",
    )
    thread_id: str = Field(
        default="default",
        alias="threadId",
        description="Thread ID for this session",
    )
    session_id: Optional[str] = Field(
        default=None,
        alias="sessionId",
        description="Optional custom session ID (auto-generated if not provided)",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Session metadata (client info, user agent, etc.)",
    )
    expires_in_hours: int = Field(
        default=2,
        alias="expiresInHours",
        ge=1,
        le=24,
        description="Session expiration time in hours (default: 2, max: 24)",
    )


class SessionResponse(BaseModel):
    """Response schema for Chat Session resources.

    Returned by API endpoints with full session details.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: UUID = Field(
        ...,
        description="Unique identifier for the session",
    )
    session_id: str = Field(
        ...,
        alias="sessionId",
        description="Session identifier",
    )
    user_id: int = Field(
        ...,
        alias="userId",
        description="User ID who owns this session",
    )
    task_id: Optional[UUID] = Field(
        default=None,
        alias="taskId",
        description="Task ID this session is for",
    )
    thread_id: str = Field(
        ...,
        alias="threadId",
        description="Thread ID",
    )
    status: SessionStatus = Field(
        ...,
        description="Session status",
    )
    connection_count: int = Field(
        ...,
        alias="connectionCount",
        description="Number of active connections",
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session metadata",
    )
    last_activity_at: datetime = Field(
        ...,
        alias="lastActivityAt",
        description="Last activity timestamp",
    )
    expires_at: datetime = Field(
        ...,
        alias="expiresAt",
        description="Expiration timestamp",
    )
    recovery_token: Optional[str] = Field(
        default=None,
        alias="recoveryToken",
        description="Token for session recovery",
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="When session was created",
    )
    updated_at: datetime = Field(
        ...,
        alias="updatedAt",
        description="When session was last updated",
    )

    @classmethod
    def from_db_model(cls, db_model: Any) -> "SessionResponse":
        """Create SessionResponse from database ChatSession model.

        Args:
            db_model: ChatSession model instance from database.

        Returns:
            SessionResponse instance populated from database model.
        """
        return cls(
            id=db_model.id,
            session_id=db_model.session_id,
            user_id=db_model.user_id,
            task_id=db_model.task_id,
            thread_id=db_model.thread_id,
            status=db_model.status,
            connection_count=db_model.connection_count,
            meta=db_model.meta,
            last_activity_at=db_model.last_activity_at,
            expires_at=db_model.expires_at,
            recovery_token=db_model.recovery_token,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )


class SessionRecoveryRequest(BaseModel):
    """Request schema for session recovery.

    Used when a client wants to recover a previous session.
    """

    model_config = ConfigDict(populate_by_name=True)

    recovery_token: str = Field(
        ...,
        alias="recoveryToken",
        description="Recovery token from the previous session",
    )
    session_id: Optional[str] = Field(
        default=None,
        alias="sessionId",
        description="Optional new session ID for the recovered session",
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated metadata for the recovered session",
    )


class SessionRecoveryResponse(BaseModel):
    """Response schema for session recovery.

    Returned after a successful session recovery.
    """

    model_config = ConfigDict(populate_by_name=True)

    success: bool = Field(
        ...,
        description="Whether recovery was successful",
    )
    session: Optional[SessionResponse] = Field(
        default=None,
        description="The recovered session",
    )
    message: str = Field(
        default="",
        description="Status message",
    )


class SessionListRequest(BaseModel):
    """Request schema for listing sessions.

    Used for filtering and pagination.
    """

    model_config = ConfigDict(populate_by_name=True)

    user_id: Optional[int] = Field(
        default=None,
        alias="userId",
        description="Filter by user ID",
    )
    task_id: Optional[UUID] = Field(
        default=None,
        alias="taskId",
        description="Filter by task ID",
    )
    status: Optional[SessionStatus] = Field(
        default=None,
        description="Filter by session status",
    )
    active_only: bool = Field(
        default=False,
        alias="activeOnly",
        description="Only return active (non-expired) sessions",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of sessions to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of sessions to skip",
    )


class SessionListResponse(BaseModel):
    """Response schema for session list.

    Includes sessions and pagination info.
    """

    model_config = ConfigDict(populate_by_name=True)

    sessions: List[SessionResponse] = Field(
        default_factory=list,
        description="List of sessions",
    )
    total: int = Field(
        ...,
        description="Total number of sessions matching the query",
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
        description="Whether there are more sessions available",
    )


class SessionMetrics(BaseModel):
    """Session metrics for monitoring.

    Provides aggregated session statistics.
    """

    model_config = ConfigDict(populate_by_name=True)

    total_sessions: int = Field(
        ...,
        alias="totalSessions",
        description="Total number of sessions",
    )
    active_sessions: int = Field(
        ...,
        alias="activeSessions",
        description="Number of active sessions",
    )
    expired_sessions: int = Field(
        ...,
        alias="expiredSessions",
        description="Number of expired sessions",
    )
    closed_sessions: int = Field(
        ...,
        alias="closedSessions",
        description="Number of closed sessions",
    )
    recovered_sessions: int = Field(
        ...,
        alias="recoveredSessions",
        description="Number of recovered sessions",
    )
    total_connections: int = Field(
        ...,
        alias="totalConnections",
        description="Total number of active connections",
    )
    avg_connections_per_session: float = Field(
        ...,
        alias="avgConnectionsPerSession",
        description="Average connections per active session",
    )


class SessionUpdateRequest(BaseModel):
    """Request schema for updating a session.

    Used for heartbeat updates and metadata changes.
    """

    model_config = ConfigDict(populate_by_name=True)

    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated metadata (merged with existing)",
    )
    extend_expiry: bool = Field(
        default=False,
        alias="extendExpiry",
        description="Whether to extend the expiration time",
    )
    expires_in_hours: Optional[int] = Field(
        default=None,
        alias="expiresInHours",
        ge=1,
        le=24,
        description="New expiration time in hours (if extending)",
    )


class WebSocketSessionEvent(BaseModel):
    """WebSocket event for session state changes.

    Sent to clients when session state changes.
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        default="session:state",
        description="Event type",
    )
    session_id: str = Field(
        ...,
        alias="sessionId",
        description="Session ID",
    )
    status: SessionStatus = Field(
        ...,
        description="Current session status",
    )
    connection_count: int = Field(
        ...,
        alias="connectionCount",
        description="Current connection count",
    )
    expires_at: datetime = Field(
        ...,
        alias="expiresAt",
        description="Current expiration time",
    )


class WebSocketSessionRecoveryEvent(BaseModel):
    """WebSocket event for session recovery result.

    Sent to clients after a recovery attempt.
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        default="session:recovered",
        description="Event type",
    )
    success: bool = Field(
        ...,
        description="Whether recovery was successful",
    )
    session_id: Optional[str] = Field(
        default=None,
        alias="sessionId",
        description="New session ID (if recovered)",
    )
    previous_session_id: Optional[str] = Field(
        default=None,
        alias="previousSessionId",
        description="Previous session ID",
    )
    message: str = Field(
        default="",
        description="Status message",
    )
