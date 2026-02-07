"""
Central stream coordination for the streaming response system.

Provides stream lifecycle management, event routing and ordering,
multi-client stream sharing, and stream recovery capabilities.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set

from .events import (
    BaseStreamEvent,
    ChunkEvent,
    CompleteEvent,
    CancelledEvent,
    ErrorEvent,
    EventType,
    StreamOffsetEvent,
)
from .state import StreamingState, StreamSession, StreamStatus
from .buffer import EventBuffer, PerStreamBuffer
from .emitter import SSEEmitter, ClientConnection
from .exceptions import (
    StreamingError,
    StreamNotFoundError,
    StreamAlreadyExistsError,
    StreamCompletedError,
    StreamCancelledError,
    ClientDisconnectedError,
)


@dataclass
class StreamConfig:
    """Configuration for a streaming session.

    Attributes:
        buffer_size: Maximum events to buffer per stream
        buffer_age_seconds: Maximum age of buffered events
        enable_recovery: Whether to support stream recovery
        emit_checkpoints: Whether to emit offset checkpoints
        checkpoint_interval: Events between checkpoints
        heartbeat_interval: Seconds between heartbeats
        max_concurrent_clients: Maximum clients per stream
    """

    buffer_size: int = 10000
    buffer_age_seconds: Optional[float] = 3600
    enable_recovery: bool = True
    emit_checkpoints: bool = True
    checkpoint_interval: int = 100
    heartbeat_interval: float = 30.0
    max_concurrent_clients: int = 100


@dataclass
class StreamContext:
    """Context for an active stream.

    Attributes:
        stream_id: Unique stream identifier
        session_id: Parent session identifier
        config: Stream configuration
        session: Stream session state
        buffer: Event buffer for this stream
        cancel_event: Event to signal cancellation
        task: The stream processing task
        metadata: Additional stream metadata
    """

    stream_id: str
    session_id: str
    config: StreamConfig
    session: StreamSession
    buffer: EventBuffer
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    task: Optional[asyncio.Task] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamingCore:
    """Central coordinator for all streaming operations.

    Manages stream lifecycle, coordinates between state, buffer, and emitter,
    and provides recovery capabilities for disconnected clients.
    """

    def __init__(
        self,
        state: Optional[StreamingState] = None,
        emitter: Optional[SSEEmitter] = None,
        default_config: Optional[StreamConfig] = None,
    ):
        self.state = state or StreamingState()
        self.emitter = emitter or SSEEmitter()
        self.default_config = default_config or StreamConfig()
        self._buffers = PerStreamBuffer()
        self._streams: Dict[str, StreamContext] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the streaming core and background tasks."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the streaming core and cleanup all streams."""
        self._running = False

        # Cancel all streams - get stream IDs first, then cancel each
        stream_ids = list(self._streams.keys())
        for stream_id in stream_ids:
            try:
                await self.cancel_stream(stream_id, reason="StreamingCore shutdown")
            except Exception:
                # Ignore errors during shutdown
                pass

        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close emitter
        await self.emitter.close()

        # Cleanup buffers
        await self._buffers.cleanup_all()

    async def create_stream(
        self,
        stream_id: str,
        session_id: str,
        config: Optional[StreamConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StreamContext:
        """Create a new stream context.

        Args:
            stream_id: Unique stream identifier
            session_id: Parent session identifier
            config: Optional stream-specific configuration
            metadata: Optional stream metadata

        Returns:
            New StreamContext

        Raises:
            StreamAlreadyExistsError: If stream already exists
        """
        config = config or self.default_config

        async with self._lock:
            if stream_id in self._streams:
                raise StreamAlreadyExistsError(
                    f"Stream {stream_id} already exists", stream_id
                )

            # Create state session
            session = await self.state.create_stream(
                stream_id=stream_id,
                session_id=session_id,
                metadata=metadata,
            )

            # Get or create buffer
            buffer = await self._buffers.get_or_create_buffer(stream_id)

            # Create context
            context = StreamContext(
                stream_id=stream_id,
                session_id=session_id,
                config=config,
                session=session,
                buffer=buffer,
                metadata=metadata or {},
            )

            self._streams[stream_id] = context
            return context

    async def start_stream(
        self,
        stream_id: str,
        event_generator: Callable[[StreamContext], AsyncGenerator[BaseStreamEvent, None]],
    ):
        """Start processing a stream with the given event generator.

        Args:
            stream_id: Stream to start
            event_generator: Async generator that produces events

        Raises:
            StreamNotFoundError: If stream not found
        """
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            context = self._streams[stream_id]

            # Update status
            await self.state.update_stream_status(stream_id, StreamStatus.RUNNING)

            # Start processing task
            context.task = asyncio.create_task(
                self._process_stream(context, event_generator)
            )

    async def _process_stream(
        self,
        context: StreamContext,
        event_generator: Callable[[StreamContext], AsyncGenerator[BaseStreamEvent, None]],
    ):
        """Process events from generator and route to clients."""
        stream_id = context.stream_id

        try:
            async for event in event_generator(context):
                # Check for cancellation
                if context.cancel_event.is_set():
                    raise StreamCancelledError(f"Stream {stream_id} was cancelled", stream_id)

                # Assign offset - use model_copy since events are frozen Pydantic models
                offset = context.session.get_next_offset()
                event = event.model_copy(update={"offset": offset, "session_id": context.session_id})

                # Buffer event
                await context.buffer.append(event)

                # Emit checkpoint if needed
                if context.config.emit_checkpoints and event.offset % context.config.checkpoint_interval == 0:
                    checkpoint = StreamOffsetEvent(
                        offset=event.offset,
                        session_id=context.session_id,
                        checkpoint_data={"last_event_offset": event.offset},
                    )
                    await self._emit_to_stream(stream_id, checkpoint)

                # Emit to clients
                await self._emit_to_stream(stream_id, event)

            # Stream completed successfully
            await self._complete_stream(stream_id)

        except StreamCancelledError:
            await self._cancel_stream(stream_id, reason="Cancelled by request")
        except asyncio.CancelledError:
            await self._cancel_stream(stream_id, reason="Cancelled by request")
        except Exception as e:
            await self._error_stream(stream_id, str(e))

    async def _emit_to_stream(self, stream_id: str, event: BaseStreamEvent):
        """Emit an event to all clients on a stream."""
        try:
            await self.emitter.emit_to_stream(stream_id, event)
        except Exception:
            # Log but don't fail the stream
            pass

    async def _complete_stream(self, stream_id: str):
        """Mark a stream as completed."""
        async with self._lock:
            if stream_id not in self._streams:
                return

            context = self._streams[stream_id]

            # Update session
            context.session.mark_complete()

            # Emit completion event
            complete_event = CompleteEvent(
                offset=context.session.get_next_offset(),
                session_id=context.session_id,
                final_offset=context.session.current_offset - 1,
            )
            await self._emit_to_stream(stream_id, complete_event)

            # Disconnect all clients
            await self.emitter.disconnect_stream(stream_id)

    async def _cancel_stream(self, stream_id: str, reason: Optional[str] = None):
        """Mark a stream as cancelled."""
        async with self._lock:
            if stream_id not in self._streams:
                return

            context = self._streams[stream_id]

            # Update session
            context.session.mark_cancelled(reason)

            # Emit cancellation event
            cancel_event = CancelledEvent(
                offset=context.session.get_next_offset(),
                session_id=context.session_id,
                cancelled_at_offset=context.session.current_offset - 1,
                reason=reason,
            )
            await self._emit_to_stream(stream_id, cancel_event)

            # Disconnect all clients
            await self.emitter.disconnect_stream(stream_id)

    async def _error_stream(self, stream_id: str, message: str, error_code: str = "STREAM_ERROR"):
        """Mark a stream as errored."""
        async with self._lock:
            if stream_id not in self._streams:
                return

            context = self._streams[stream_id]

            # Update session
            context.session.mark_error(error_code, message)

            # Emit error event
            error_event = ErrorEvent(
                offset=context.session.get_next_offset(),
                session_id=context.session_id,
                error_code=error_code,
                message=message,
            )
            await self._emit_to_stream(stream_id, error_event)

            # Disconnect all clients
            await self.emitter.disconnect_stream(stream_id)

    async def cancel_stream(self, stream_id: str, reason: Optional[str] = None):
        """Cancel a running stream.

        Args:
            stream_id: Stream to cancel
            reason: Optional reason for cancellation
        """
        task = None
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            context = self._streams[stream_id]
            context.cancel_event.set()
            task = context.task

        # Cancel and wait for task outside the lock to avoid deadlock
        if task:
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

    async def connect_client(
        self,
        stream_id: str,
        client_id: Optional[str] = None,
        resume_from_offset: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClientConnection:
        """Connect a client to a stream with optional recovery.

        Args:
            stream_id: Stream to connect to
            client_id: Optional client ID (generated if not provided)
            resume_from_offset: Offset to resume from (for recovery)
            metadata: Optional client metadata

        Returns:
            ClientConnection instance

        Raises:
            StreamNotFoundError: If stream not found
            StreamCompletedError: If stream is already completed
        """
        client_id = client_id or str(uuid.uuid4())

        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            context = self._streams[stream_id]

            if context.session.is_terminal():
                raise StreamCompletedError(
                    f"Stream {stream_id} is already {context.session.status.value}",
                    stream_id,
                )

            # Register with state
            start_offset = resume_from_offset or 0
            await self.state.register_client(client_id, stream_id, start_offset)

            # Register with emitter
            client = await self.emitter.register_client(stream_id, client_id, metadata)

            # If recovering, replay buffered events
            if resume_from_offset is not None and context.config.enable_recovery:
                events = await context.buffer.get_from_offset(resume_from_offset)
                await self.emitter.emit_batch(client_id, events)

            return client

    async def disconnect_client(self, client_id: str, stream_id: str):
        """Disconnect a client from a stream."""
        await self.state.disconnect_client(client_id, stream_id)
        await self.emitter.unregister_client(client_id)

    async def get_event_generator(
        self,
        client_id: str,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[str, None]:
        """Get the SSE event generator for a client.

        This should be used with EventSourceResponse.
        """
        async for event_str in self.emitter.event_generator(client_id, cancel_event):
            yield event_str

    async def get_stream(self, stream_id: str) -> StreamContext:
        """Get stream context by ID."""
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)
            return self._streams[stream_id]

    async def get_stream_status(self, stream_id: str) -> Dict[str, Any]:
        """Get detailed status for a stream."""
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            context = self._streams[stream_id]
            buffer_stats = await context.buffer.get_stats()

            return {
                "stream_id": stream_id,
                "session_id": context.session_id,
                "status": context.session.status.value,
                "current_offset": context.session.current_offset,
                "created_at": context.session.created_at.isoformat(),
                "updated_at": context.session.updated_at.isoformat(),
                "buffer": buffer_stats,
                "client_count": len(context.session.client_ids),
            }

    async def get_recovery_info(self, stream_id: str, offset: int) -> Dict[str, Any]:
        """Get information about recovery possibilities for a stream at an offset.

        Args:
            stream_id: Stream to check
            offset: The offset a client wants to recover from

        Returns:
            Dict with recovery information
        """
        async with self._lock:
            if stream_id not in self._streams:
                raise StreamNotFoundError(f"Stream {stream_id} not found", stream_id)

            context = self._streams[stream_id]
            coverage = await context.buffer.get_buffer_coverage(offset)

            return {
                "stream_id": stream_id,
                "session_id": context.session_id,
                "status": context.session.status.value,
                "requested_offset": offset,
                "can_recover": coverage["can_recover"],
                "buffer_coverage": coverage,
                "stream_active": context.session.is_active(),
            }

    async def _cleanup_loop(self):
        """Background task for periodic cleanup."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute

                if not self._running:
                    break

                # Clean up expired buffer events
                await self._buffers.cleanup_expired_all()

                # Disconnect stale clients
                await self.emitter.disconnect_stale_clients(timeout_seconds=120)

                # Clean up old completed streams
                await self.state.cleanup_old_streams(max_age_seconds=3600)

            except asyncio.CancelledError:
                break
            except Exception:
                # Log but continue
                pass

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive streaming statistics."""
        state_stats = await self.state.get_stats()
        emitter_stats = await self.emitter.get_stats()
        buffer_stats = await self._buffers.get_stats()

        return {
            "state": state_stats,
            "emitter": emitter_stats,
            "buffers": buffer_stats,
            "active_streams": len(self._streams),
        }


# Global streaming core instance
_streaming_core: Optional[StreamingCore] = None


def get_streaming_core() -> StreamingCore:
    """Get the global streaming core instance."""
    global _streaming_core
    if _streaming_core is None:
        _streaming_core = StreamingCore()
    return _streaming_core


def set_streaming_core(core: StreamingCore):
    """Set the global streaming core instance."""
    global _streaming_core
    _streaming_core = core
