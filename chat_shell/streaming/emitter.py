"""
SSE (Server-Sent Events) emitter for streaming responses.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set

from .events import BaseStreamEvent, EventType
from .exceptions import ClientDisconnectedError, StreamingError


class ConnectionState(Enum):
    """Connection lifecycle states."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ClientConnection:
    """Represents a client SSE connection.

    Attributes:
        client_id: Unique client identifier
        stream_id: Stream this client is connected to
        queue: Async queue for events
        state: Current connection state
        connected_at: Connection start time
        last_activity: Last activity timestamp
        heartbeat_interval: Seconds between heartbeats
        metadata: Additional connection metadata
    """

    client_id: str
    stream_id: str
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=1000))
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    heartbeat_interval: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    _disconnect_event: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self):
        self.state = ConnectionState.CONNECTED
        self._disconnect_event.clear()

    @property
    def is_active(self) -> bool:
        """Check if client connection is active."""
        return self.state == ConnectionState.CONNECTED

    def mark_active(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def is_stale(self, timeout_seconds: float = 60.0) -> bool:
        """Check if connection has been inactive too long."""
        inactive = (datetime.utcnow() - self.last_activity).total_seconds()
        return inactive > timeout_seconds

    def disconnect(self):
        """Mark connection for disconnection."""
        self.state = ConnectionState.DISCONNECTING
        self._disconnect_event.set()

    async def wait_for_disconnect(self, timeout: Optional[float] = None) -> bool:
        """Wait for disconnection signal."""
        try:
            await asyncio.wait_for(self._disconnect_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False


@dataclass
class SSEMessage:
    """An SSE message ready for emission.

    Attributes:
        event: Event type/name
        data: Message payload
        id: Optional event ID
        retry: Optional retry timing hint
        comment: Optional comment (ignored by client but useful for debugging)
    """

    event: str
    data: str
    id: Optional[str] = None
    retry: Optional[int] = None
    comment: Optional[str] = None

    def to_sse_format(self) -> str:
        """Convert to SSE wire format."""
        lines = []

        if self.comment:
            lines.append(f": {self.comment}")

        if self.id:
            lines.append(f"id: {self.id}")

        if self.retry:
            lines.append(f"retry: {self.retry}")

        lines.append(f"event: {self.event}")

        # Handle multi-line data
        for line in self.data.split("\n"):
            lines.append(f"data: {line}")

        lines.append("")  # Empty line to terminate
        lines.append("")  # Second newline for SSE termination

        return "\n".join(lines)


class SSEEmitter:
    """Dedicated SSE event emission manager.

    Handles event queuing per client, connection management,
    heartbeat/keepalive mechanisms, and batch event emission.
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        max_queue_size: int = 1000,
        enable_heartbeats: bool = True,
    ):
        self.heartbeat_interval = heartbeat_interval
        self.max_queue_size = max_queue_size
        self.enable_heartbeats = enable_heartbeats

        self._clients: Dict[str, ClientConnection] = {}
        self._stream_clients: Dict[str, Set[str]] = {}  # stream_id -> set of client_ids
        self._lock = asyncio.Lock()
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self._global_sequence = 0

    def _get_next_sequence(self) -> int:
        """Get next global sequence number."""
        self._global_sequence += 1
        return self._global_sequence

    async def register_client(
        self,
        stream_id: str,
        client_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClientConnection:
        """Register a new client connection.

        Args:
            stream_id: Stream to connect to
            client_id: Optional client ID (generated if not provided)
            metadata: Optional connection metadata

        Returns:
            New ClientConnection instance
        """
        async with self._lock:
            client_id = client_id or str(uuid.uuid4())

            client = ClientConnection(
                client_id=client_id,
                stream_id=stream_id,
                heartbeat_interval=self.heartbeat_interval,
                metadata=metadata or {},
            )

            self._clients[client_id] = client

            # Track under stream
            if stream_id not in self._stream_clients:
                self._stream_clients[stream_id] = set()
            self._stream_clients[stream_id].add(client_id)

            # Start heartbeat if enabled
            if self.enable_heartbeats:
                self._heartbeat_tasks[client_id] = asyncio.create_task(
                    self._heartbeat_loop(client_id)
                )

            return client

    async def unregister_client(self, client_id: str):
        """Unregister and cleanup a client connection."""
        async with self._lock:
            await self._cleanup_client(client_id)

    async def _cleanup_client(self, client_id: str):
        """Internal cleanup for a client (must hold lock)."""
        if client_id not in self._clients:
            return

        client = self._clients[client_id]
        client.disconnect()

        # Cancel heartbeat
        if client_id in self._heartbeat_tasks:
            self._heartbeat_tasks[client_id].cancel()
            try:
                await self._heartbeat_tasks[client_id]
            except asyncio.CancelledError:
                pass
            del self._heartbeat_tasks[client_id]

        # Remove from stream tracking
        stream_id = client.stream_id
        if stream_id in self._stream_clients:
            self._stream_clients[stream_id].discard(client_id)
            if not self._stream_clients[stream_id]:
                del self._stream_clients[stream_id]

        # Remove client
        del self._clients[client_id]

    async def _heartbeat_loop(self, client_id: str):
        """Send periodic heartbeat comments to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)

                if client_id not in self._clients:
                    break

                client = self._clients[client_id]
                if client.state != ConnectionState.CONNECTED:
                    break

                # Send heartbeat comment
                heartbeat = SSEMessage(
                    event="heartbeat",
                    data="",
                    comment=f"heartbeat {datetime.utcnow().isoformat()}",
                )

                try:
                    client.queue.put_nowait(heartbeat)
                    client.mark_active()
                except asyncio.QueueFull:
                    # Client not consuming, mark for disconnect
                    client.disconnect()
                    break

        except asyncio.CancelledError:
            pass
        except Exception:
            # Log but don't crash
            pass

    async def emit(
        self,
        client_id: str,
        event: BaseStreamEvent,
        timeout: Optional[float] = None,
    ) -> bool:
        """Emit a single event to a specific client.

        Args:
            client_id: Target client
            event: Event to emit
            timeout: Max time to wait for queue space

        Returns:
            True if event was queued, False otherwise

        Raises:
            ClientDisconnectedError: If client is not connected
        """
        async with self._lock:
            if client_id not in self._clients:
                raise ClientDisconnectedError(f"Client {client_id} not connected")

            client = self._clients[client_id]
            if client.state != ConnectionState.CONNECTED:
                raise ClientDisconnectedError(f"Client {client_id} is {client.state.value}")

            # Get sequence number (events are immutable, so we pass it to SSE conversion)
            sequence = self._get_next_sequence()

            # Convert to SSE message with sequence
            sse_msg = self._event_to_sse(event, sequence)

            # Try to queue
            try:
                if timeout:
                    await asyncio.wait_for(
                        client.queue.put(sse_msg),
                        timeout=timeout,
                    )
                else:
                    client.queue.put_nowait(sse_msg)

                client.mark_active()
                return True

            except (asyncio.QueueFull, asyncio.TimeoutError):
                return False

    async def emit_to_stream(
        self,
        stream_id: str,
        event: BaseStreamEvent,
        exclude_client: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Emit an event to all clients on a stream.

        Args:
            stream_id: Target stream
            event: Event to emit
            exclude_client: Optional client to exclude

        Returns:
            Dict mapping client_id to success status
        """
        async with self._lock:
            client_ids = self._stream_clients.get(stream_id, set()).copy()

        if exclude_client:
            client_ids.discard(exclude_client)

        results = {}
        for client_id in client_ids:
            try:
                results[client_id] = await self.emit(client_id, event)
            except ClientDisconnectedError:
                results[client_id] = False

        return results

    async def emit_batch(
        self,
        client_id: str,
        events: List[BaseStreamEvent],
        timeout: Optional[float] = None,
    ) -> int:
        """Emit multiple events to a client.

        Args:
            client_id: Target client
            events: Events to emit
            timeout: Max time to wait for queue space

        Returns:
            Number of events successfully queued
        """
        count = 0
        for event in events:
            if await self.emit(client_id, event, timeout):
                count += 1
            else:
                break
        return count

    def _event_to_sse(self, event: BaseStreamEvent, sequence: Optional[int] = None) -> SSEMessage:
        """Convert a stream event to SSE message."""
        payload = event.to_sse_payload()

        # Use provided sequence or fall back to event's sequence
        seq = sequence if sequence is not None else event.sequence

        return SSEMessage(
            event=event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
            data=json.dumps(payload),
            id=str(seq) if seq is not None else None,
        )

    async def event_generator(
        self,
        client_id: str,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate SSE formatted events for a client.

        This is the main generator to use with EventSourceResponse.

        Args:
            client_id: Client to generate events for
            cancel_event: Optional event to signal cancellation

        Yields:
            SSE formatted event strings
        """
        if client_id not in self._clients:
            raise ClientDisconnectedError(f"Client {client_id} not found")

        client = self._clients[client_id]

        try:
            while client.state == ConnectionState.CONNECTED:
                # Check for cancellation
                if cancel_event and cancel_event.is_set():
                    break

                # Wait for event with timeout
                try:
                    msg = await asyncio.wait_for(
                        client.queue.get(),
                        timeout=1.0,
                    )
                    yield msg.to_sse_format()
                    client.mark_active()

                except asyncio.TimeoutError:
                    # No events, continue loop
                    continue

        except asyncio.CancelledError:
            pass
        finally:
            await self.unregister_client(client_id)

    async def get_client(self, client_id: str) -> Optional[ClientConnection]:
        """Get client connection info."""
        async with self._lock:
            return self._clients.get(client_id)

    async def get_stream_clients(self, stream_id: str) -> List[ClientConnection]:
        """Get all clients connected to a stream."""
        async with self._lock:
            client_ids = self._stream_clients.get(stream_id, set())
            return [self._clients[cid] for cid in client_ids if cid in self._clients]

    async def disconnect_stream(self, stream_id: str, reason: Optional[str] = None):
        """Disconnect all clients from a stream."""
        async with self._lock:
            client_ids = list(self._stream_clients.get(stream_id, set()))
            for client_id in client_ids:
                await self._cleanup_client(client_id)

    async def disconnect_stale_clients(self, timeout_seconds: float = 60.0) -> int:
        """Disconnect clients that have been inactive too long.

        Returns:
            Number of clients disconnected
        """
        async with self._lock:
            stale_clients = [
                cid for cid, client in self._clients.items()
                if client.is_stale(timeout_seconds)
            ]

            for client_id in stale_clients:
                await self._cleanup_client(client_id)

            return len(stale_clients)

    async def get_stats(self) -> Dict[str, Any]:
        """Get emitter statistics."""
        async with self._lock:
            return {
                "total_clients": len(self._clients),
                "total_streams": len(self._stream_clients),
                "clients_per_stream": {
                    sid: len(cids) for sid, cids in self._stream_clients.items()
                },
                "heartbeat_tasks": len(self._heartbeat_tasks),
                "global_sequence": self._global_sequence,
            }

    async def close(self):
        """Close all connections and cleanup."""
        async with self._lock:
            client_ids = list(self._clients.keys())
            for client_id in client_ids:
                await self._cleanup_client(client_id)

            self._clients.clear()
            self._stream_clients.clear()
            self._heartbeat_tasks.clear()
