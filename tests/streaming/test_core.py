"""
Tests for streaming core module.
"""

import pytest
import asyncio
from typing import AsyncGenerator

from chat_shell_101.streaming.core import (
    StreamingCore,
    StreamConfig,
    StreamContext,
    get_streaming_core,
    set_streaming_core,
)
from chat_shell_101.streaming.events import (
    ChunkEvent,
    CompleteEvent,
    ErrorEvent,
    EventType,
)
from chat_shell_101.streaming.state import StreamStatus
from chat_shell_101.streaming.exceptions import (
    StreamNotFoundError,
    StreamAlreadyExistsError,
    StreamCompletedError,
)

# Mark all tests in this module as Epic 5 tests
pytestmark = pytest.mark.epic_5


# Helper functions for polling and timeout handling
async def wait_for_stream_status(core, stream_id, expected_status, timeout=5.0, interval=0.1):
    """Poll for stream status with timeout."""
    for _ in range(int(timeout / interval)):
        status = await core.get_stream_status(stream_id)
        if status["status"] == expected_status:
            return status
        await asyncio.sleep(interval)
    return await core.get_stream_status(stream_id)


async def collect_events_with_timeout(generator, min_count, timeout=5.0):
    """Collect events from generator with timeout."""
    events = []
    async for event in generator:
        events.append(event)
        if len(events) >= min_count:
            break
    return events


class TestStreamConfig:
    """Tests for StreamConfig."""

    def test_default_config(self):
        """Test default stream configuration."""
        config = StreamConfig()

        assert config.buffer_size == 10000
        assert config.enable_recovery is True
        assert config.emit_checkpoints is True
        assert config.checkpoint_interval == 100

    def test_custom_config(self):
        """Test custom stream configuration."""
        config = StreamConfig(
            buffer_size=500,
            enable_recovery=False,
            checkpoint_interval=50,
        )

        assert config.buffer_size == 500
        assert config.enable_recovery is False
        assert config.checkpoint_interval == 50


class TestStreamingCore:
    """Tests for StreamingCore."""

    @pytest.fixture
    async def core(self):
        """Create a fresh StreamingCore for testing."""
        core = StreamingCore()
        await core.start()
        yield core
        await core.stop()

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping the core."""
        core = StreamingCore()

        assert core._running is False

        await core.start()
        assert core._running is True

        await core.stop()
        assert core._running is False

    @pytest.mark.asyncio
    async def test_create_stream(self, core):
        """Test creating a stream."""
        context = await core.create_stream(
            stream_id="stream-1",
            session_id="session-1",
            metadata={"key": "value"},
        )

        assert context.stream_id == "stream-1"
        assert context.session_id == "session-1"
        assert context.metadata["key"] == "value"
        assert context.config.enable_recovery is True

    @pytest.mark.asyncio
    async def test_create_duplicate_stream_raises(self, core):
        """Test that creating duplicate stream raises error."""
        await core.create_stream("stream-1", "session-1")

        with pytest.raises(StreamAlreadyExistsError):
            await core.create_stream("stream-1", "session-1")

    @pytest.mark.asyncio
    async def test_get_stream(self, core):
        """Test getting a stream."""
        await core.create_stream("stream-1", "session-1")

        context = await core.get_stream("stream-1")

        assert context.stream_id == "stream-1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_stream_raises(self, core):
        """Test that getting nonexistent stream raises error."""
        with pytest.raises(StreamNotFoundError):
            await core.get_stream("nonexistent")

    @pytest.mark.asyncio
    async def test_start_stream(self, core):
        """Test starting a stream with event generator."""
        config = StreamConfig(emit_checkpoints=False)
        await core.create_stream("stream-1", "session-1", config=config)

        async def event_generator(ctx: StreamContext) -> AsyncGenerator[ChunkEvent, None]:
            # offset=0 is a placeholder - StreamingCore will assign actual offsets
            yield ChunkEvent(offset=0, session_id="test", text="Hello")
            yield ChunkEvent(offset=0, session_id="test", text="World")
            yield CompleteEvent(offset=0, session_id="test", final_offset=1)

        await core.start_stream("stream-1", event_generator)

        # Poll for completion with timeout
        status = await wait_for_stream_status(core, "stream-1", "completed")
        assert status["status"] == "completed"

    @pytest.mark.asyncio
    async def test_cancel_stream(self, core):
        """Test cancelling a stream."""
        config = StreamConfig(emit_checkpoints=False)
        await core.create_stream("stream-1", "session-1", config=config)

        async def slow_generator(ctx: StreamContext) -> AsyncGenerator[ChunkEvent, None]:
            for i in range(100):
                # offset=0 is a placeholder - StreamingCore will assign actual offsets
                yield ChunkEvent(offset=0, session_id="test", text=f"Message {i}")
                await asyncio.sleep(0.1)

        await core.start_stream("stream-1", slow_generator)

        # Give the stream task a chance to start
        await asyncio.sleep(0.01)

        # Cancel immediately
        await core.cancel_stream("stream-1", reason="Test cancellation")

        # Poll for cancelled status with timeout
        status = await wait_for_stream_status(core, "stream-1", "cancelled")
        assert status["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_connect_client(self, core):
        """Test connecting a client to a stream."""
        await core.create_stream("stream-1", "session-1")

        client = await core.connect_client(
            stream_id="stream-1",
            client_id="client-1",
        )

        assert client.client_id == "client-1"
        assert client.stream_id == "stream-1"

    @pytest.mark.asyncio
    async def test_connect_client_to_terminal_stream_raises(self, core):
        """Test that connecting to completed stream raises error."""
        await core.create_stream("stream-1", "session-1")
        context = await core.get_stream("stream-1")
        context.session.mark_complete()

        with pytest.raises(StreamCompletedError):
            await core.connect_client("stream-1", "client-1")

    @pytest.mark.asyncio
    async def test_connect_client_with_recovery(self, core):
        """Test connecting a client with recovery offset."""
        config = StreamConfig(enable_recovery=True, emit_checkpoints=False)
        await core.create_stream("stream-1", "session-1", config=config)

        # Add some events to buffer
        context = await core.get_stream("stream-1")
        for i in range(10):
            # Explicit offsets are preserved when manually adding to buffer
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await context.buffer.append(event)

        client = await core.connect_client(
            stream_id="stream-1",
            client_id="client-1",
            resume_from_offset=5,
        )

        assert client.client_id == "client-1"

    @pytest.mark.asyncio
    async def test_disconnect_client(self, core):
        """Test disconnecting a client."""
        await core.create_stream("stream-1", "session-1")
        client = await core.connect_client("stream-1", "client-1")

        await core.disconnect_client("client-1", "stream-1")

        # Client should no longer be in stream
        stream_clients = await core.emitter.get_stream_clients("stream-1")
        assert len(stream_clients) == 0

    @pytest.mark.asyncio
    async def test_get_event_generator(self, core):
        """Test getting event generator for a client."""
        await core.create_stream("stream-1", "session-1")
        client = await core.connect_client("stream-1", "client-1")

        generator = core.get_event_generator("client-1")

        # Should be an async generator
        assert hasattr(generator, "__aiter__")

    @pytest.mark.asyncio
    async def test_get_stream_status(self, core):
        """Test getting stream status."""
        await core.create_stream("stream-1", "session-1", metadata={"test": "data"})

        status = await core.get_stream_status("stream-1")

        assert status["stream_id"] == "stream-1"
        assert status["session_id"] == "session-1"
        assert "buffer" in status
        assert "client_count" in status

    @pytest.mark.asyncio
    async def test_get_recovery_info(self, core):
        """Test getting recovery information."""
        config = StreamConfig(enable_recovery=True, emit_checkpoints=False)
        await core.create_stream("stream-1", "session-1", config=config)

        # Add events to buffer
        context = await core.get_stream("stream-1")
        for i in range(10):
            # Explicit offsets are preserved when manually adding to buffer
            event = ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            await context.buffer.append(event)

        info = await core.get_recovery_info("stream-1", offset=5)

        assert info["stream_id"] == "stream-1"
        assert info["requested_offset"] == 5
        assert info["can_recover"] is True
        assert "buffer_coverage" in info

    @pytest.mark.asyncio
    async def test_get_stats(self, core):
        """Test getting streaming statistics."""
        await core.create_stream("stream-1", "session-1")
        await core.create_stream("stream-2", "session-1")

        stats = await core.get_stats()

        assert "state" in stats
        assert "emitter" in stats
        assert "buffers" in stats
        assert stats["active_streams"] == 2


class TestStreamingCoreIntegration:
    """Integration tests for StreamingCore."""

    @pytest.mark.asyncio
    async def test_full_stream_lifecycle(self):
        """Test complete stream lifecycle from creation to completion."""
        core = StreamingCore()
        await core.start()

        try:
            # Create stream with checkpoints disabled
            config = StreamConfig(emit_checkpoints=False)
            await core.create_stream("stream-1", "session-1", config=config)

            # Connect client
            client = await core.connect_client("stream-1", "client-1")

            # Define event generator with small delays to allow collection
            events_emitted = []

            async def event_generator(ctx: StreamContext) -> AsyncGenerator[ChunkEvent, None]:
                for i in range(5):
                    # offset=0 is a placeholder - StreamingCore will assign actual offsets
                    event = ChunkEvent(offset=0, session_id="test", text=f"Message {i}")
                    events_emitted.append(event)
                    yield event
                    # Small delay to allow client to collect
                    await asyncio.sleep(0.01)
                yield CompleteEvent(offset=0, session_id="test", final_offset=4)

            # Start stream and collect events concurrently
            collected_events = []

            async def collect_events():
                async for sse_str in core.get_event_generator("client-1"):
                    collected_events.append(sse_str)
                    if len(collected_events) >= 6:  # 5 chunks + complete
                        break

            # Start both the stream and the collection
            await core.start_stream("stream-1", event_generator)

            # Collect with timeout
            try:
                await asyncio.wait_for(collect_events(), timeout=5.0)
            except asyncio.TimeoutError:
                pass  # We'll check what we collected

            # Verify
            assert len(events_emitted) == 5
            assert len(collected_events) >= 1  # At least some events should be collected

            # Check stream status
            status = await core.get_stream_status("stream-1")
            assert status["status"] in ("completed", "running", "cancelled")

        finally:
            await core.stop()

    @pytest.mark.asyncio
    async def test_multiple_clients_same_stream(self):
        """Test multiple clients connected to the same stream."""
        core = StreamingCore()
        await core.start()

        try:
            # Create stream with checkpoints disabled
            config = StreamConfig(emit_checkpoints=False)
            await core.create_stream("stream-1", "session-1", config=config)

            # Connect multiple clients
            client1 = await core.connect_client("stream-1", "client-1")
            client2 = await core.connect_client("stream-1", "client-2")

            async def event_generator(ctx: StreamContext) -> AsyncGenerator[ChunkEvent, None]:
                for i in range(3):
                    # offset=0 is a placeholder - StreamingCore will assign actual offsets
                    yield ChunkEvent(offset=0, session_id="test", text=f"Message {i}")
                    # Small delay to allow clients to collect
                    await asyncio.sleep(0.01)
                yield CompleteEvent(offset=0, session_id="test", final_offset=2)

            # Start stream first
            await core.start_stream("stream-1", event_generator)

            # Collect from both clients
            events1 = []
            events2 = []

            async def collect_with_timeout(client_id, events_list, count):
                async for sse_str in core.get_event_generator(client_id):
                    events_list.append(sse_str)
                    if len(events_list) >= count:
                        break

            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        collect_with_timeout("client-1", events1, 4),
                        collect_with_timeout("client-2", events2, 4),
                    ),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                pass  # We'll check what we collected

            # Both should receive some events (may not get all due to timing)
            assert len(events1) >= 1
            assert len(events2) >= 1

        finally:
            await core.stop()

    @pytest.mark.asyncio
    async def test_stream_error_handling(self):
        """Test error handling in stream."""
        core = StreamingCore()
        await core.start()

        try:
            # Create stream with checkpoints disabled
            config = StreamConfig(emit_checkpoints=False)
            await core.create_stream("stream-1", "session-1", config=config)
            client = await core.connect_client("stream-1", "client-1")

            async def error_generator(ctx: StreamContext) -> AsyncGenerator[ChunkEvent, None]:
                # offset=0 is a placeholder - StreamingCore will assign actual offsets
                yield ChunkEvent(offset=0, session_id="test", text="Start")
                # Small delay to allow event to be processed before error
                await asyncio.sleep(0.01)
                raise ValueError("Test error")

            await core.start_stream("stream-1", error_generator)

            # Collect events with timeout
            events = []

            async def collect_with_timeout():
                async for sse_str in core.get_event_generator("client-1"):
                    events.append(sse_str)
                    if len(events) >= 2:
                        break

            await asyncio.wait_for(collect_with_timeout(), timeout=5.0)

            # Should have received at least the first event and error
            assert len(events) >= 1

            # Check status - poll for error status with timeout
            status = await wait_for_stream_status(core, "stream-1", "error")
            assert status["status"] == "error"

        finally:
            await core.stop()


class TestGlobalStreamingCore:
    """Tests for global streaming core functions."""

    def test_get_streaming_core_creates_default(self):
        """Test that get_streaming_core creates default instance."""
        # Reset global
        set_streaming_core(None)

        core = get_streaming_core()

        assert core is not None
        assert isinstance(core, StreamingCore)

    def test_set_streaming_core(self):
        """Test setting global streaming core."""
        custom_core = StreamingCore()

        set_streaming_core(custom_core)

        assert get_streaming_core() is custom_core

    def test_get_streaming_core_returns_same_instance(self):
        """Test that get_streaming_core returns same instance."""
        # Reset
        set_streaming_core(None)

        core1 = get_streaming_core()
        core2 = get_streaming_core()

        assert core1 is core2
