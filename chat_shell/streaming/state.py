"""
Streaming state management for session tracking and recovery.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from .exceptions import StreamNotFoundError, StreamAlreadyExistsError, InvalidOffsetError


class StreamStatus(str, Enum):
    """Stream lifecycle statuses."""

    PENDING = "pending"  # Stream created but not started
    RUNNING = "running"  # Stream actively producing events
    PAUSED = "paused"  # Stream temporarily paused
    COMPLETED = "completed"  # Stream finished successfully
    CANCELLED = "cancelled"  # Stream was cancelled
    ERROR = "error"  # Stream ended with error


class ClientInfo(BaseModel):
    """Information about a connected client.

    Attributes:
        client_id: Unique client identifier
        connected_at: When the client connected
        last_offset: Last offset acknowledged by client
        is_active: Whether client is currently connected
        last_activity: Last activity timestamp for stale detection
    """

    client_id: str
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_offset: int = 0
    is_active: bool = True
    disconnected_at: Optional[datetime] = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    def is_stale(self, timeout_seconds: float = 60.0) -> bool:
        """Check if client has been inactive too long."""
        inactive = (datetime.utcnow() - self.last_activity).total_seconds()
        return inactive > timeout_seconds


class StreamSession(BaseModel):
    """A single streaming session with state tracking.

    Attributes:
        stream_id: Unique stream identifier
        session_id: Parent session identifier
        status: Current stream status
        current_offset: Next event offset to assign
        created_at: When the stream was created
        updated_at: Last update timestamp
        metadata: Additional stream metadata
        checkpoint_data: Data for recovery at current offset
        client_ids: Set of connected client IDs
    """

    stream_id: str
    session_id: str
    status: StreamStatus = StreamStatus.PENDING
    current_offset: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    checkpoint_data: Dict[str, Any] = Field(default_factory=dict)
    client_ids: Set[str] = Field(default_factory=set)
    error_info: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True

    def is_active(self) -> bool:
        """Check if stream is currently active (pending, running, or paused)."""
        return self.status in (StreamStatus.PENDING, StreamStatus.RUNNING, StreamStatus.PAUSED)

    def is_terminal(self) -> bool:
        """Check if stream has reached a terminal state."""
        return self.status in (StreamStatus.COMPLETED, StreamStatus.CANCELLED, StreamStatus.ERROR)

    def get_next_offset(self) -> int:
        """Get the next available offset and increment counter."""
        offset = self.current_offset
        self.current_offset += 1
        self.updated_at = datetime.utcnow()
        return offset

    def update_checkpoint(self, offset: int, data: Dict[str, Any]):
        """Update checkpoint data for recovery."""
        self.checkpoint_data = {
            "offset": offset,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.updated_at = datetime.utcnow()

    def mark_complete(self):
        """Mark the stream as completed."""
        self.status = StreamStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_cancelled(self, reason: Optional[str] = None):
        """Mark the stream as cancelled."""
        self.status = StreamStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if reason:
            self.metadata["cancellation_reason"] = reason

    def mark_error(self, error_code: str, message: str, details: Optional[Dict] = None):
        """Mark the stream as errored."""
        self.status = StreamStatus.ERROR
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_info = {
            "error_code": error_code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def add_client(self, client_id: str):
        """Add a client to this stream."""
        self.client_ids.add(client_id)
        self.updated_at = datetime.utcnow()

    def remove_client(self, client_id: str):
        """Remove a client from this stream."""
        self.client_ids.discard(client_id)
        self.updated_at = datetime.utcnow()


class StreamingState:
    """Central state management for all streaming sessions.

    Manages stream lifecycle, client connections, and provides
    recovery capabilities for disconnected clients.
    """

    def __init__(self):
        self._streams: Dict[str, StreamSession] = {}  # stream_id -> StreamSession
        self._clients: Dict[str, ClientInfo] = {}  # client_id -> ClientInfo
        self._session_streams: Dict[str, Set[str]] = {}  # session_id -> set of stream_ids
        self._lock = asyncio.Lock()

    async def create_stream(
        self,
        stream_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StreamSession:
        """Create a new stream session.

        Args:
            stream_id: Unique stream identifier
            session_id: Parent session identifier
            metadata: Optional stream metadata

        Raises:
            StreamAlreadyExistsError: If stream_id already exists
        """
        async with self._lock:
            if stream_id in self._streams:
                raise StreamAlreadyExistsError(
                    f"Stream {stream_id} already exists", stream_id
                )

            stream = StreamSession(
                stream_id=stream_id,
                session_id=session_id,
                metadata=metadata or {},
            )
            self._streams[stream_id] = stream

            # Track under session
            if session_id not in self._session_streams:
                self._session_streams[session_id] = set()
            self._session_streams[session_id].add(stream_id)

            return stream

    async def get_stream(self, stream_id: str) -> StreamSession:
        """Get a stream by ID.

        Raises:
            StreamNotFoundError: If stream not found
        """
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)
            return self._streams[stream_id]

    async def get_or_create_stream(
        self,
        stream_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StreamSession:
        """Get existing stream or create new one."""
        try:
            return await self.get_stream(stream_id)
        except StreamNotFoundError:
            return await self.create_stream(stream_id, session_id, metadata)

    async def update_stream_status(
        self,
        stream_id: str,
        status: StreamStatus,
    ) -> StreamSession:
        """Update stream status."""
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            stream = self._streams[stream_id]
            stream.status = status
            stream.updated_at = datetime.utcnow()
            return stream

    async def delete_stream(self, stream_id: str):
        """Delete a stream and clean up associated data."""
        async with self._lock:
            if stream_id not in self._streams:
                return

            stream = self._streams[stream_id]

            # Remove from session tracking
            session_id = stream.session_id
            if session_id in self._session_streams:
                self._session_streams[session_id].discard(stream_id)
                if not self._session_streams[session_id]:
                    del self._session_streams[session_id]

            # Remove stream
            del self._streams[stream_id]

    async def get_session_streams(self, session_id: str) -> List[StreamSession]:
        """Get all streams for a session."""
        async with self._lock:
            stream_ids = self._session_streams.get(session_id, set())
            return [self._streams[sid] for sid in stream_ids if sid in self._streams]

    async def register_client(
        self,
        client_id: str,
        stream_id: str,
        start_offset: int = 0,
    ) -> ClientInfo:
        """Register a new client connection to a stream.

        Args:
            client_id: Unique client identifier
            stream_id: Stream to connect to
            start_offset: Starting offset for this client (for recovery)

        Raises:
            StreamNotFoundError: If stream not found
        """
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            client = ClientInfo(
                client_id=client_id,
                last_offset=start_offset,
                is_active=True,
            )
            self._clients[client_id] = client
            self._streams[stream_id].add_client(client_id)
            return client

    async def disconnect_client(self, client_id: str, stream_id: Optional[str] = None):
        """Mark a client as disconnected."""
        async with self._lock:
            if client_id in self._clients:
                client = self._clients[client_id]
                client.is_active = False
                client.disconnected_at = datetime.utcnow()

            if stream_id and stream_id in self._streams:
                self._streams[stream_id].remove_client(client_id)

    async def update_client_offset(self, client_id: str, offset: int):
        """Update the last acknowledged offset for a client."""
        async with self._lock:
            if client_id in self._clients:
                self._clients[client_id].last_offset = offset

    async def get_client(self, client_id: str) -> Optional[ClientInfo]:
        """Get client information."""
        async with self._lock:
            return self._clients.get(client_id)

    async def get_recovery_offset(self, stream_id: str, client_id: str) -> int:
        """Get the offset to resume from for a client.

        Args:
            stream_id: Stream to recover
            client_id: Client requesting recovery

        Returns:
            Offset to resume from

        Raises:
            StreamNotFoundError: If stream not found
        """
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            # If client exists, use their last offset
            if client_id in self._clients:
                return self._clients[client_id].last_offset

            # Otherwise start from beginning
            return 0

    async def validate_offset(self, stream_id: str, offset: int) -> bool:
        """Validate if an offset is valid for a stream.

        Args:
            stream_id: Stream to validate against
            offset: Offset to validate

        Returns:
            True if offset is valid

        Raises:
            StreamNotFoundError: If stream not found
            InvalidOffsetError: If offset is invalid
        """
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            stream = self._streams[stream_id]

            if offset < 0:
                raise InvalidOffsetError(
                    f"Offset {offset} is negative", stream_id
                )

            if offset > stream.current_offset:
                raise InvalidOffsetError(
                    f"Offset {offset} exceeds stream position {stream.current_offset}",
                    stream_id,
                )

            return True

    async def get_active_streams(self) -> List[StreamSession]:
        """Get all currently active streams."""
        async with self._lock:
            return [s for s in self._streams.values() if s.is_active()]

    async def get_stream_count(self) -> int:
        """Get total number of streams."""
        async with self._lock:
            return len(self._streams)

    async def cleanup_old_streams(self, max_age_seconds: float) -> int:
        """Remove completed streams older than max_age_seconds.

        Returns:
            Number of streams removed
        """
        async with self._lock:
            now = datetime.utcnow()
            to_remove = []

            for stream_id, stream in self._streams.items():
                if stream.is_terminal() and stream.completed_at:
                    age = (now - stream.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(stream_id)

            # Remove streams directly without calling delete_stream to avoid lock reentrancy
            for stream_id in to_remove:
                if stream_id in self._streams:
                    stream = self._streams[stream_id]
                    # Remove from session tracking
                    session_id = stream.session_id
                    if session_id in self._session_streams:
                        self._session_streams[session_id].discard(stream_id)
                        if not self._session_streams[session_id]:
                            del self._session_streams[session_id]
                    # Remove stream
                    del self._streams[stream_id]

            return len(to_remove)

    async def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        async with self._lock:
            total = len(self._streams)
            active = sum(1 for s in self._streams.values() if s.is_active())
            completed = sum(1 for s in self._streams.values() if s.status == StreamStatus.COMPLETED)
            cancelled = sum(1 for s in self._streams.values() if s.status == StreamStatus.CANCELLED)
            error = sum(1 for s in self._streams.values() if s.status == StreamStatus.ERROR)

            return {
                "total_streams": total,
                "active_streams": active,
                "completed_streams": completed,
                "cancelled_streams": cancelled,
                "error_streams": error,
                "total_clients": len(self._clients),
                "active_clients": sum(1 for c in self._clients.values() if c.is_active),
            }
