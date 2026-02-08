"""In-memory session manager for chat session state management.

Provides session tracking with optional Redis support for distributed deployments.

Epic 16: Chat Session State Management
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID


@dataclass
class SessionState:
    """In-memory representation of a session state."""

    session_id: str
    user_id: int
    task_id: Optional[UUID]
    thread_id: str
    connection_count: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=2))
    meta: Dict[str, Any] = field(default_factory=dict)
    websocket_ids: Set[str] = field(default_factory=set)

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def add_websocket(self, websocket_id: str) -> None:
        """Add a WebSocket connection to this session."""
        self.websocket_ids.add(websocket_id)
        self.connection_count = len(self.websocket_ids)
        self.update_activity()

    def remove_websocket(self, websocket_id: str) -> None:
        """Remove a WebSocket connection from this session."""
        self.websocket_ids.discard(websocket_id)
        self.connection_count = len(self.websocket_ids)
        self.update_activity()


class SessionManager:
    """Manages in-memory session state for WebSocket connections.

    Tracks active sessions, connection counts, and provides session
    recovery support. Can be extended with Redis for distributed deployments.
    """

    def __init__(self):
        """Initialize the session manager."""
        # session_id -> SessionState
        self._sessions: Dict[str, SessionState] = {}
        # user_id -> set of session_ids
        self._user_sessions: Dict[int, Set[str]] = {}
        # task_id -> set of session_ids
        self._task_sessions: Dict[UUID, Set[str]] = {}
        # websocket_id -> session_id
        self._websocket_sessions: Dict[str, str] = {}

        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the session manager and background tasks."""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def stop(self) -> None:
        """Stop the session manager and cleanup."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def create_session(
        self,
        session_id: str,
        user_id: int,
        task_id: Optional[UUID] = None,
        thread_id: str = "default",
        expires_in_hours: int = 2,
        meta: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        """Create a new session.

        Args:
            session_id: Unique session identifier.
            user_id: User ID who owns this session.
            task_id: Optional task ID.
            thread_id: Thread ID.
            expires_in_hours: Session expiration time.
            meta: Optional metadata.

        Returns:
            Created SessionState.
        """
        async with self._lock:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

            session = SessionState(
                session_id=session_id,
                user_id=user_id,
                task_id=task_id,
                thread_id=thread_id,
                expires_at=expires_at,
                meta=meta or {},
            )

            self._sessions[session_id] = session

            # Index by user
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)

            # Index by task
            if task_id:
                if task_id not in self._task_sessions:
                    self._task_sessions[task_id] = set()
                self._task_sessions[task_id].add(session_id)

            return session

    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            SessionState if found and not expired, None otherwise.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and not session.is_expired():
                return session
            return None

    async def associate_websocket(
        self,
        session_id: str,
        websocket_id: str,
    ) -> Optional[SessionState]:
        """Associate a WebSocket connection with a session.

        Args:
            session_id: Session identifier.
            websocket_id: WebSocket connection identifier.

        Returns:
            Updated SessionState or None if session not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None

            session.add_websocket(websocket_id)
            self._websocket_sessions[websocket_id] = session_id

            return session

    async def disassociate_websocket(self, websocket_id: str) -> Optional[SessionState]:
        """Disassociate a WebSocket connection from its session.

        Args:
            websocket_id: WebSocket connection identifier.

        Returns:
            Updated SessionState or None if not found.
        """
        async with self._lock:
            session_id = self._websocket_sessions.get(websocket_id)
            if not session_id:
                return None

            session = self._sessions.get(session_id)
            if session:
                session.remove_websocket(websocket_id)

            del self._websocket_sessions[websocket_id]

            return session

    async def update_activity(self, session_id: str) -> Optional[SessionState]:
        """Update session activity timestamp.

        Args:
            session_id: Session identifier.

        Returns:
            Updated SessionState or None if not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.update_activity()
            return session

    async def close_session(self, session_id: str) -> bool:
        """Close a session and remove it from tracking.

        Args:
            session_id: Session identifier.

        Returns:
            True if session was found and closed, False otherwise.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            # Remove from user index
            if session.user_id in self._user_sessions:
                self._user_sessions[session.user_id].discard(session_id)
                if not self._user_sessions[session.user_id]:
                    del self._user_sessions[session.user_id]

            # Remove from task index
            if session.task_id and session.task_id in self._task_sessions:
                self._task_sessions[session.task_id].discard(session_id)
                if not self._task_sessions[session.task_id]:
                    del self._task_sessions[session.task_id]

            # Remove websocket associations
            for ws_id in list(session.websocket_ids):
                if ws_id in self._websocket_sessions:
                    del self._websocket_sessions[ws_id]

            # Remove session
            del self._sessions[session_id]

            return True

    async def get_user_sessions(self, user_id: int) -> List[SessionState]:
        """Get all active sessions for a user.

        Args:
            user_id: User ID.

        Returns:
            List of active SessionState objects.
        """
        async with self._lock:
            session_ids = self._user_sessions.get(user_id, set())
            sessions = []
            for sid in list(session_ids):
                session = self._sessions.get(sid)
                if session and not session.is_expired():
                    sessions.append(session)
            return sessions

    async def get_task_sessions(self, task_id: UUID) -> List[SessionState]:
        """Get all active sessions for a task.

        Args:
            task_id: Task ID.

        Returns:
            List of active SessionState objects.
        """
        async with self._lock:
            session_ids = self._task_sessions.get(task_id, set())
            sessions = []
            for sid in list(session_ids):
                session = self._sessions.get(sid)
                if session and not session.is_expired():
                    sessions.append(session)
            return sessions

    async def get_session_count(self) -> int:
        """Get total number of tracked sessions.

        Returns:
            Number of sessions.
        """
        async with self._lock:
            return len(self._sessions)

    async def get_connection_count(self) -> int:
        """Get total number of WebSocket connections.

        Returns:
            Number of connections.
        """
        async with self._lock:
            return len(self._websocket_sessions)

    async def _cleanup_expired_sessions(self) -> None:
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                async with self._lock:
                    expired_ids = [
                        sid for sid, session in self._sessions.items()
                        if session.is_expired()
                    ]

                    for sid in expired_ids:
                        session = self._sessions.get(sid)
                        if session:
                            # Remove from user index
                            if session.user_id in self._user_sessions:
                                self._user_sessions[session.user_id].discard(sid)

                            # Remove from task index
                            if session.task_id and session.task_id in self._task_sessions:
                                self._task_sessions[session.task_id].discard(sid)

                            # Remove websocket associations
                            for ws_id in list(session.websocket_ids):
                                if ws_id in self._websocket_sessions:
                                    del self._websocket_sessions[ws_id]

                            # Remove session
                            del self._sessions[sid]

            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue running
                pass


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance.

    Returns:
        The global SessionManager instance.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
