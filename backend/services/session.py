"""Session service for chat session management.

Provides CRUD operations for chat sessions with lifecycle management,
timeout handling, and recovery support.

Epic 16: Chat Session State Management
"""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.session import ChatSession, SessionStatus
from backend.schemas.session import (
    SessionCreateRequest,
    SessionListRequest,
    SessionListResponse,
    SessionMetrics,
    SessionRecoveryRequest,
    SessionRecoveryResponse,
    SessionResponse,
    SessionUpdateRequest,
)


class SessionService:
    """Service for chat session management.

    Handles session lifecycle, timeout handling, recovery,
    and concurrent session limits per user.
    """

    # Maximum concurrent sessions per user
    MAX_SESSIONS_PER_USER = 5

    # Default session expiration in hours
    DEFAULT_EXPIRY_HOURS = 2

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session for database operations.
        """
        self.session = session

    def _generate_session_id(self) -> str:
        """Generate a unique session ID.

        Returns:
            Unique session identifier.
        """
        return f"sess_{secrets.token_urlsafe(32)}"

    def _generate_recovery_token(self) -> str:
        """Generate a unique recovery token.

        Returns:
            Unique recovery token.
        """
        return f"rec_{secrets.token_urlsafe(32)}"

    async def create(self, request: SessionCreateRequest) -> SessionResponse:
        """Create a new session.

        Args:
            request: Session creation request.

        Returns:
            Created SessionResponse.

        Raises:
            ValueError: If user has too many concurrent sessions.
        """
        # Check concurrent session limit
        active_count = await self._count_user_active_sessions(request.user_id)
        if active_count >= self.MAX_SESSIONS_PER_USER:
            raise ValueError(
                f"Maximum concurrent sessions ({self.MAX_SESSIONS_PER_USER}) reached"
            )

        # Generate session ID if not provided
        session_id = request.session_id or self._generate_session_id()

        # Calculate expiration
        expires_in = request.expires_in_hours or self.DEFAULT_EXPIRY_HOURS
        expires_at = datetime.utcnow() + timedelta(hours=expires_in)

        # Create session
        chat_session = ChatSession(
            session_id=session_id,
            user_id=request.user_id,
            task_id=request.task_id,
            thread_id=request.thread_id or "default",
            status=SessionStatus.ACTIVE,
            meta=request.meta or {},
            connection_count=1,
            last_activity_at=datetime.utcnow(),
            expires_at=expires_at,
            recovery_token=self._generate_recovery_token(),
        )

        self.session.add(chat_session)
        await self.session.flush()
        await self.session.refresh(chat_session)

        return SessionResponse.from_db_model(chat_session)

    async def get(self, session_id: str) -> Optional[SessionResponse]:
        """Get a session by session ID.

        Args:
            session_id: Session identifier.

        Returns:
            SessionResponse if found, None otherwise.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        return SessionResponse.from_db_model(session) if session else None

    async def get_by_id(self, session_id: UUID) -> Optional[SessionResponse]:
        """Get a session by internal ID.

        Args:
            session_id: Internal UUID.

        Returns:
            SessionResponse if found, None otherwise.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        return SessionResponse.from_db_model(session) if session else None

    async def get_by_recovery_token(self, token: str) -> Optional[SessionResponse]:
        """Get a session by recovery token.

        Args:
            token: Recovery token.

        Returns:
            SessionResponse if found, None otherwise.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.recovery_token == token)
        )
        session = result.scalar_one_or_none()

        return SessionResponse.from_db_model(session) if session else None

    async def list_sessions(
        self,
        request: Optional[SessionListRequest] = None,
    ) -> SessionListResponse:
        """List sessions with filtering.

        Args:
            request: List request with filters.

        Returns:
            SessionListResponse with sessions and pagination.
        """
        if request is None:
            request = SessionListRequest()

        # Build query conditions
        conditions = []

        if request.user_id is not None:
            conditions.append(ChatSession.user_id == request.user_id)

        if request.task_id is not None:
            conditions.append(ChatSession.task_id == request.task_id)

        if request.status is not None:
            conditions.append(ChatSession.status == request.status)

        if request.active_only:
            conditions.append(ChatSession.status == SessionStatus.ACTIVE)
            conditions.append(ChatSession.expires_at > datetime.utcnow())

        # Get total count
        count_query = select(func.count()).where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get sessions with pagination
        query = (
            select(ChatSession)
            .where(and_(*conditions))
            .order_by(desc(ChatSession.last_activity_at))
            .offset(request.offset)
            .limit(request.limit)
        )

        result = await self.session.execute(query)
        sessions = result.scalars().all()

        # Calculate has_more
        has_more = (request.offset + len(sessions)) < total

        return SessionListResponse(
            sessions=[SessionResponse.from_db_model(s) for s in sessions],
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
        )

    async def recover_session(
        self,
        request: SessionRecoveryRequest,
    ) -> SessionRecoveryResponse:
        """Recover a previous session.

        Args:
            request: Recovery request with token.

        Returns:
            SessionRecoveryResponse with result.
        """
        # Find the session to recover
        old_session_result = await self.session.execute(
            select(ChatSession).where(ChatSession.recovery_token == request.recovery_token)
        )
        old_session = old_session_result.scalar_one_or_none()

        if not old_session:
            return SessionRecoveryResponse(
                success=False,
                message="Invalid or expired recovery token",
            )

        # Check if session can be recovered
        if old_session.status == SessionStatus.CLOSED:
            return SessionRecoveryResponse(
                success=False,
                message="Session has been closed and cannot be recovered",
            )

        # Mark old session as recovered
        old_session.status = SessionStatus.RECOVERED
        old_session.connection_count = 0

        # Create new session based on old one
        new_session_id = request.session_id or self._generate_session_id()
        expires_at = datetime.utcnow() + timedelta(hours=self.DEFAULT_EXPIRY_HOURS)

        # Merge metadata
        merged_meta = {**old_session.meta, **(request.meta or {})}
        merged_meta["recovered_from"] = old_session.session_id
        merged_meta["recovery_time"] = datetime.utcnow().isoformat()

        new_session = ChatSession(
            session_id=new_session_id,
            user_id=old_session.user_id,
            task_id=old_session.task_id,
            thread_id=old_session.thread_id,
            status=SessionStatus.ACTIVE,
            meta=merged_meta,
            connection_count=1,
            last_activity_at=datetime.utcnow(),
            expires_at=expires_at,
            recovery_token=self._generate_recovery_token(),
            recovered_from_id=old_session.id,
        )

        self.session.add(new_session)
        await self.session.flush()
        await self.session.refresh(new_session)

        return SessionRecoveryResponse(
            success=True,
            session=SessionResponse.from_db_model(new_session),
            message="Session recovered successfully",
        )

    async def update_activity(self, session_id: str) -> Optional[SessionResponse]:
        """Update session activity timestamp.

        Args:
            session_id: Session identifier.

        Returns:
            Updated SessionResponse or None if not found.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.update_activity()
        await self.session.flush()
        await self.session.refresh(session)

        return SessionResponse.from_db_model(session)

    async def update_session(
        self,
        session_id: str,
        request: SessionUpdateRequest,
    ) -> Optional[SessionResponse]:
        """Update a session.

        Args:
            session_id: Session identifier.
            request: Update request.

        Returns:
            Updated SessionResponse or None if not found.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Update metadata if provided
        if request.meta is not None:
            session.meta = {**session.meta, **request.meta}

        # Extend expiration if requested
        if request.extend_expiry:
            hours = request.expires_in_hours or self.DEFAULT_EXPIRY_HOURS
            session.expires_at = datetime.utcnow() + timedelta(hours=hours)

        session.update_activity()
        await self.session.flush()
        await self.session.refresh(session)

        return SessionResponse.from_db_model(session)

    async def increment_connections(self, session_id: str) -> Optional[SessionResponse]:
        """Increment connection count for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Updated SessionResponse or None if not found.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.connection_count += 1
        session.update_activity()
        await self.session.flush()
        await self.session.refresh(session)

        return SessionResponse.from_db_model(session)

    async def decrement_connections(self, session_id: str) -> Optional[SessionResponse]:
        """Decrement connection count for a session.

        If connection count reaches 0, the session is marked as closed.

        Args:
            session_id: Session identifier.

        Returns:
            Updated SessionResponse or None if not found.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.connection_count = max(0, session.connection_count - 1)
        session.update_activity()

        # Close session if no connections
        if session.connection_count == 0:
            session.close()

        await self.session.flush()
        await self.session.refresh(session)

        return SessionResponse.from_db_model(session)

    async def close_session(self, session_id: str) -> Optional[SessionResponse]:
        """Close a session.

        Args:
            session_id: Session identifier.

        Returns:
            Closed SessionResponse or None if not found.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.close()
        session.connection_count = 0
        await self.session.flush()
        await self.session.refresh(session)

        return SessionResponse.from_db_model(session)

    async def expire_session(self, session_id: str) -> Optional[SessionResponse]:
        """Mark a session as expired.

        Args:
            session_id: Session identifier.

        Returns:
            Expired SessionResponse or None if not found.
        """
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.expire()
        await self.session.flush()
        await self.session.refresh(session)

        return SessionResponse.from_db_model(session)

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions by marking them as expired.

        Returns:
            Number of sessions marked as expired.
        """
        result = await self.session.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.status == SessionStatus.ACTIVE,
                    ChatSession.expires_at <= datetime.utcnow(),
                )
            )
        )
        expired_sessions = result.scalars().all()

        for session in expired_sessions:
            session.expire()

        return len(expired_sessions)

    async def get_metrics(self) -> SessionMetrics:
        """Get session metrics for monitoring.

        Returns:
            SessionMetrics with aggregated statistics.
        """
        # Total sessions
        total_result = await self.session.execute(select(func.count()).select_from(ChatSession))
        total = total_result.scalar() or 0

        # Active sessions
        active_result = await self.session.execute(
            select(func.count()).where(
                and_(
                    ChatSession.status == SessionStatus.ACTIVE,
                    ChatSession.expires_at > datetime.utcnow(),
                )
            )
        )
        active = active_result.scalar() or 0

        # Expired sessions
        expired_result = await self.session.execute(
            select(func.count()).where(ChatSession.status == SessionStatus.EXPIRED)
        )
        expired = expired_result.scalar() or 0

        # Closed sessions
        closed_result = await self.session.execute(
            select(func.count()).where(ChatSession.status == SessionStatus.CLOSED)
        )
        closed = closed_result.scalar() or 0

        # Recovered sessions
        recovered_result = await self.session.execute(
            select(func.count()).where(ChatSession.status == SessionStatus.RECOVERED)
        )
        recovered = recovered_result.scalar() or 0

        # Total connections
        connections_result = await self.session.execute(
            select(func.sum(ChatSession.connection_count)).where(
                ChatSession.status == SessionStatus.ACTIVE
            )
        )
        total_connections = connections_result.scalar() or 0

        # Average connections per active session
        avg_connections = total_connections / active if active > 0 else 0.0

        return SessionMetrics(
            total_sessions=total,
            active_sessions=active,
            expired_sessions=expired,
            closed_sessions=closed,
            recovered_sessions=recovered,
            total_connections=total_connections,
            avg_connections_per_session=round(avg_connections, 2),
        )

    async def _count_user_active_sessions(self, user_id: int) -> int:
        """Count active sessions for a user.

        Args:
            user_id: User ID.

        Returns:
            Number of active sessions.
        """
        result = await self.session.execute(
            select(func.count()).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.status == SessionStatus.ACTIVE,
                    ChatSession.expires_at > datetime.utcnow(),
                )
            )
        )
        return result.scalar() or 0
