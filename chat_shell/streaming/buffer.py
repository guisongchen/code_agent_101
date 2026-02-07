"""
Event buffering for stream recovery and replay.
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypeVar

from .events import BaseStreamEvent
from .exceptions import BufferOverflowError, InvalidOffsetError


@dataclass
class BufferedEvent:
    """An event stored in the buffer with metadata."""

    event: BaseStreamEvent
    inserted_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0


T = TypeVar("T", bound=BaseStreamEvent)


class EventBuffer:
    """Ring buffer for recent events with recovery support.

    Maintains a fixed-size buffer of recent events that can be
    retrieved by offset for client recovery scenarios.

    Attributes:
        max_size: Maximum number of events to buffer
        max_age_seconds: Maximum age of events to keep
    """

    def __init__(
        self,
        max_size: int = 10000,
        max_age_seconds: Optional[float] = 3600,  # 1 hour default
    ):
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self._buffer: deque[BufferedEvent] = deque(maxlen=max_size)
        self._events_by_offset: Dict[int, BufferedEvent] = {}
        self._lock = asyncio.Lock()
        self._total_inserted = 0
        self._total_evicted = 0

    async def append(self, event: BaseStreamEvent) -> bool:
        """Add an event to the buffer.

        Args:
            event: The event to buffer

        Returns:
            True if event was added, False if rejected

        Raises:
            BufferOverflowError: If buffer is at capacity and cannot evict
        """
        async with self._lock:
            # Check if we need to evict
            if len(self._buffer) >= self.max_size:
                # Evict oldest event
                oldest = self._buffer.popleft()
                if oldest.event.offset in self._events_by_offset:
                    del self._events_by_offset[oldest.event.offset]
                self._total_evicted += 1

            # Create buffered event
            buffered = BufferedEvent(event=event)

            # Add to buffer
            self._buffer.append(buffered)
            self._events_by_offset[event.offset] = buffered
            self._total_inserted += 1

            return True

    async def get(self, offset: int) -> Optional[BaseStreamEvent]:
        """Get a single event by offset.

        Args:
            offset: The event offset to retrieve

        Returns:
            The event if found, None otherwise
        """
        async with self._lock:
            buffered = self._events_by_offset.get(offset)
            if buffered:
                buffered.access_count += 1
                return buffered.event
            return None

    async def get_range(
        self,
        start_offset: int,
        end_offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[BaseStreamEvent]:
        """Get events in an offset range.

        Args:
            start_offset: Starting offset (inclusive)
            end_offset: Ending offset (inclusive), or None for all after start
            limit: Maximum number of events to return

        Returns:
            List of events in the range, sorted by offset
        """
        async with self._lock:
            events = []

            for offset, buffered in self._events_by_offset.items():
                if offset < start_offset:
                    continue
                if end_offset is not None and offset > end_offset:
                    continue
                events.append(buffered.event)
                buffered.access_count += 1

            # Sort by offset
            events.sort(key=lambda e: e.offset)

            # Apply limit
            if limit is not None:
                events = events[:limit]

            return events

    async def get_from_offset(
        self,
        offset: int,
        limit: Optional[int] = None,
    ) -> List[BaseStreamEvent]:
        """Get all events from a given offset onwards.

        This is the primary method for client recovery.

        Args:
            offset: Starting offset (inclusive)
            limit: Maximum number of events to return

        Returns:
            List of events from offset onwards
        """
        return await self.get_range(offset, limit=limit)

    async def has_offset(self, offset: int) -> bool:
        """Check if an offset exists in the buffer."""
        async with self._lock:
            return offset in self._events_by_offset

    async def get_min_offset(self) -> Optional[int]:
        """Get the minimum offset currently in buffer."""
        async with self._lock:
            if not self._events_by_offset:
                return None
            return min(self._events_by_offset.keys())

    async def get_max_offset(self) -> Optional[int]:
        """Get the maximum offset currently in buffer."""
        async with self._lock:
            if not self._events_by_offset:
                return None
            return max(self._events_by_offset.keys())

    async def get_buffer_coverage(self, required_offset: int) -> Dict:
        """Get information about buffer coverage for a given offset.

        Args:
            required_offset: The offset a client wants to recover from

        Returns:
            Dict with coverage information:
                - has_offset: Whether the exact offset is available
                - min_available: Minimum offset in buffer
                - max_available: Maximum offset in buffer
                - can_recover: Whether recovery is possible
                - missing_count: Number of events before buffer start
        """
        async with self._lock:
            if not self._events_by_offset:
                return {
                    "has_offset": False,
                    "min_available": None,
                    "max_available": None,
                    "can_recover": False,
                    "missing_count": required_offset,
                }

            min_offset = min(self._events_by_offset.keys())
            max_offset = max(self._events_by_offset.keys())

            has_offset = required_offset in self._events_by_offset
            can_recover = required_offset <= max_offset
            # missing_count: how many events are missing (gaps) within the buffer range
            # Events before min_offset are not "missing" - they were never in the buffer
            # Only count gaps between min_offset and required_offset
            if required_offset <= min_offset:
                # Client wants events at or before buffer start - no gaps to count
                missing_count = 0
            else:
                # Client wants events within or after our buffer
                # Count gaps in the buffer between min and required
                missing_count = sum(
                    1 for o in range(min_offset, required_offset)
                    if o not in self._events_by_offset
                )

            return {
                "has_offset": has_offset,
                "min_available": min_offset,
                "max_available": max_offset,
                "can_recover": can_recover,
                "missing_count": missing_count,
            }

    async def cleanup_expired(self) -> int:
        """Remove events older than max_age_seconds.

        Returns:
            Number of events removed
        """
        if self.max_age_seconds is None:
            return 0

        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(seconds=self.max_age_seconds)
            to_remove = []

            for offset, buffered in list(self._events_by_offset.items()):
                if buffered.inserted_at < cutoff:
                    to_remove.append(offset)

            for offset in to_remove:
                del self._events_by_offset[offset]

            # Rebuild buffer deque
            self._buffer = deque(
                [b for b in self._buffer if b.event.offset not in to_remove],
                maxlen=self.max_size,
            )

            return len(to_remove)

    async def clear(self):
        """Clear all events from the buffer."""
        async with self._lock:
            self._buffer.clear()
            self._events_by_offset.clear()

    async def get_stats(self) -> Dict:
        """Get buffer statistics."""
        async with self._lock:
            min_offset = min(self._events_by_offset.keys()) if self._events_by_offset else None
            max_offset = max(self._events_by_offset.keys()) if self._events_by_offset else None

            return {
                "current_size": len(self._buffer),
                "max_size": self.max_size,
                "total_inserted": self._total_inserted,
                "total_evicted": self._total_evicted,
                "min_offset": min_offset,
                "max_offset": max_offset,
                "max_age_seconds": self.max_age_seconds,
            }

    async def get_recent_events(self, count: int = 10) -> List[BaseStreamEvent]:
        """Get the most recent N events.

        Args:
            count: Number of events to retrieve

        Returns:
            List of recent events, newest first
        """
        async with self._lock:
            # Get last N from deque
            recent = list(self._buffer)[-count:]
            return [r.event for r in reversed(recent)]


class PerStreamBuffer:
    """Manages separate EventBuffers for each stream.

    Provides isolation between streams while sharing configuration.
    """

    def __init__(
        self,
        max_size: int = 10000,
        max_age_seconds: Optional[float] = 3600,
    ):
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self._buffers: Dict[str, EventBuffer] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_buffer(self, stream_id: str) -> EventBuffer:
        """Get existing buffer or create new one for stream."""
        async with self._lock:
            if stream_id not in self._buffers:
                self._buffers[stream_id] = EventBuffer(
                    max_size=self.max_size,
                    max_age_seconds=self.max_age_seconds,
                )
            return self._buffers[stream_id]

    async def get_buffer(self, stream_id: str) -> Optional[EventBuffer]:
        """Get buffer for stream if it exists."""
        async with self._lock:
            return self._buffers.get(stream_id)

    async def remove_buffer(self, stream_id: str):
        """Remove buffer for a stream."""
        async with self._lock:
            if stream_id in self._buffers:
                await self._buffers[stream_id].clear()
                del self._buffers[stream_id]

    async def cleanup_all(self):
        """Clear all buffers."""
        async with self._lock:
            for buffer in self._buffers.values():
                await buffer.clear()
            self._buffers.clear()

    async def cleanup_expired_all(self) -> Dict[str, int]:
        """Clean up expired events in all buffers.

        Returns:
            Dict mapping stream_id to count of removed events
        """
        async with self._lock:
            results = {}
            for stream_id, buffer in self._buffers.items():
                results[stream_id] = await buffer.cleanup_expired()
            return results

    async def get_stats(self) -> Dict[str, Dict]:
        """Get stats for all buffers."""
        async with self._lock:
            stats = {}
            for stream_id, buffer in self._buffers.items():
                stats[stream_id] = await buffer.get_stats()
            return stats
