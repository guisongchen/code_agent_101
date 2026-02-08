"""
Tests for event buffer module.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from chat_shell.streaming.buffer import EventBuffer, BufferedEvent, PerStreamBuffer
from chat_shell.streaming.events import ChunkEvent, EventType


class TestEventBuffer:
    """Tests for EventBuffer."""

    @pytest.fixture
    def buffer(self):
        """Create a fresh EventBuffer for testing."""
        return EventBuffer(max_size=100, max_age_seconds=3600)

    @pytest.mark.asyncio
    async def test_append_event(self, buffer):
        """Test appending an event."""
        event = ChunkEvent(offset=0, session_id="test", text="Hello")

        result = await buffer.append(event)

        assert result is True
        assert await buffer.get(0) == event

    @pytest.mark.asyncio
    async def test_get_event(self, buffer):
        """Test getting an event by offset."""
        event1 = ChunkEvent(offset=0, session_id="test", text="Hello")
        event2 = ChunkEvent(offset=1, session_id="test", text="World")

        await buffer.append(event1)
        await buffer.append(event2)

        assert await buffer.get(0) == event1
        assert await buffer.get(1) == event2

    @pytest.mark.asyncio
    async def test_get_nonexistent_event(self, buffer):
        """Test getting an event that doesn't exist."""
        result = await buffer.get(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_range(self, buffer):
        """Test getting events in a range."""
        for i in range(10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        events = await buffer.get_range(start_offset=3, end_offset=6)

        assert len(events) == 4  # 3, 4, 5, 6
        assert events[0].offset == 3
        assert events[-1].offset == 6

    @pytest.mark.asyncio
    async def test_get_range_no_end(self, buffer):
        """Test getting events from offset to end."""
        for i in range(10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        events = await buffer.get_range(start_offset=7)

        assert len(events) == 3  # 7, 8, 9

    @pytest.mark.asyncio
    async def test_get_range_with_limit(self, buffer):
        """Test getting events with limit."""
        for i in range(20):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        events = await buffer.get_range(start_offset=0, limit=5)

        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_get_from_offset(self, buffer):
        """Test getting events from a specific offset."""
        for i in range(10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        events = await buffer.get_from_offset(5)

        assert len(events) == 5  # 5, 6, 7, 8, 9
        assert events[0].offset == 5

    @pytest.mark.asyncio
    async def test_has_offset(self, buffer):
        """Test checking if offset exists."""
        event = ChunkEvent(offset=5, session_id="test", text="Hello")
        await buffer.append(event)

        assert await buffer.has_offset(5) is True
        assert await buffer.has_offset(0) is False

    @pytest.mark.asyncio
    async def test_get_min_max_offset(self, buffer):
        """Test getting min and max offsets."""
        for i in range(5, 15):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        assert await buffer.get_min_offset() == 5
        assert await buffer.get_max_offset() == 14

    @pytest.mark.asyncio
    async def test_get_min_max_offset_empty(self, buffer):
        """Test getting min/max on empty buffer."""
        assert await buffer.get_min_offset() is None
        assert await buffer.get_max_offset() is None

    @pytest.mark.asyncio
    async def test_buffer_eviction(self):
        """Test that old events are evicted when buffer is full."""
        buffer = EventBuffer(max_size=5)

        for i in range(10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        # Only last 5 should remain
        assert await buffer.get(0) is None
        assert await buffer.get(4) is None
        assert await buffer.get(5) is not None
        assert await buffer.get(9) is not None

    @pytest.mark.asyncio
    async def test_get_buffer_coverage(self, buffer):
        """Test getting buffer coverage info."""
        for i in range(10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        coverage = await buffer.get_buffer_coverage(required_offset=5)

        assert coverage["has_offset"] is True
        assert coverage["min_available"] == 0
        assert coverage["max_available"] == 9
        assert coverage["can_recover"] is True
        assert coverage["missing_count"] == 0

    @pytest.mark.asyncio
    async def test_get_buffer_coverage_before_start(self, buffer):
        """Test coverage when required offset is before buffer start."""
        for i in range(5, 15):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        coverage = await buffer.get_buffer_coverage(required_offset=2)

        assert coverage["has_offset"] is False
        assert coverage["can_recover"] is True
        assert coverage["missing_count"] == 0  # Offset 2 is before min

    @pytest.mark.asyncio
    async def test_get_buffer_coverage_after_end(self, buffer):
        """Test coverage when required offset is after buffer end."""
        for i in range(5):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        coverage = await buffer.get_buffer_coverage(required_offset=10)

        assert coverage["has_offset"] is False
        assert coverage["can_recover"] is False

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleaning up expired events."""
        buffer = EventBuffer(max_size=100, max_age_seconds=1)

        # Add events
        for i in range(5):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Add more events
        for i in range(5, 10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        removed = await buffer.cleanup_expired()

        assert removed == 5
        assert await buffer.get(0) is None
        assert await buffer.get(5) is not None

    @pytest.mark.asyncio
    async def test_cleanup_expired_no_max_age(self):
        """Test that cleanup does nothing when no max age is set."""
        buffer = EventBuffer(max_size=100, max_age_seconds=None)

        for i in range(5):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        removed = await buffer.cleanup_expired()

        assert removed == 0

    @pytest.mark.asyncio
    async def test_clear(self, buffer):
        """Test clearing the buffer."""
        for i in range(10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        await buffer.clear()

        assert await buffer.get(0) is None
        stats = await buffer.get_stats()
        assert stats["current_size"] == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, buffer):
        """Test getting buffer statistics."""
        for i in range(10):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        stats = await buffer.get_stats()

        assert stats["current_size"] == 10
        assert stats["max_size"] == 100
        assert stats["total_inserted"] == 10
        assert stats["min_offset"] == 0
        assert stats["max_offset"] == 9

    @pytest.mark.asyncio
    async def test_get_recent_events(self, buffer):
        """Test getting recent events."""
        for i in range(20):
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await buffer.append(event)

        recent = await buffer.get_recent_events(count=5)

        assert len(recent) == 5
        # Should be newest first
        assert recent[0].offset == 19
        assert recent[4].offset == 15


class TestPerStreamBuffer:
    """Tests for PerStreamBuffer."""

    @pytest.fixture
    def per_stream(self):
        """Create a fresh PerStreamBuffer."""
        return PerStreamBuffer(max_size=100, max_age_seconds=3600)

    @pytest.mark.asyncio
    async def test_get_or_create_buffer(self, per_stream):
        """Test getting or creating buffer for stream."""
        buffer1 = await per_stream.get_or_create_buffer("stream-1")
        buffer2 = await per_stream.get_or_create_buffer("stream-1")
        buffer3 = await per_stream.get_or_create_buffer("stream-2")

        assert buffer1 is buffer2
        assert buffer1 is not buffer3

    @pytest.mark.asyncio
    async def test_get_buffer(self, per_stream):
        """Test getting existing buffer."""
        await per_stream.get_or_create_buffer("stream-1")

        buffer = await per_stream.get_buffer("stream-1")

        assert buffer is not None

        nonexistent = await per_stream.get_buffer("nonexistent")
        assert nonexistent is None

    @pytest.mark.asyncio
    async def test_remove_buffer(self, per_stream):
        """Test removing a buffer."""
        await per_stream.get_or_create_buffer("stream-1")

        await per_stream.remove_buffer("stream-1")

        assert await per_stream.get_buffer("stream-1") is None

    @pytest.mark.asyncio
    async def test_cleanup_all(self, per_stream):
        """Test cleaning up all buffers."""
        await per_stream.get_or_create_buffer("stream-1")
        await per_stream.get_or_create_buffer("stream-2")

        await per_stream.cleanup_all()

        assert await per_stream.get_buffer("stream-1") is None
        assert await per_stream.get_buffer("stream-2") is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_all(self, per_stream):
        """Test cleaning up expired events in all buffers."""
        # Create buffer with short max age
        per_stream.max_age_seconds = 1

        buffer1 = await per_stream.get_or_create_buffer("stream-1")
        buffer2 = await per_stream.get_or_create_buffer("stream-2")

        # Add events to both
        for i in range(5):
            await buffer1.append(ChunkEvent(offset=i, session_id="test", text=f"M{i}"))
            await buffer2.append(ChunkEvent(offset=i, session_id="test", text=f"M{i}"))

        # Wait for expiration
        await asyncio.sleep(1.1)

        results = await per_stream.cleanup_expired_all()

        assert results["stream-1"] == 5
        assert results["stream-2"] == 5

    @pytest.mark.asyncio
    async def test_get_stats(self, per_stream):
        """Test getting stats for all buffers."""
        buffer1 = await per_stream.get_or_create_buffer("stream-1")
        buffer2 = await per_stream.get_or_create_buffer("stream-2")

        await buffer1.append(ChunkEvent(offset=0, session_id="test", text="Hello"))
        await buffer2.append(ChunkEvent(offset=0, session_id="test", text="World"))

        stats = await per_stream.get_stats()

        assert "stream-1" in stats
        assert "stream-2" in stats
        assert stats["stream-1"]["current_size"] == 1
        assert stats["stream-2"]["current_size"] == 1


pytestmark = [pytest.mark.unit, pytest.mark.chat_shell]
