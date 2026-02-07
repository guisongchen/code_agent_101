"""
Tests for SSE emitter module.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from chat_shell.streaming.emitter import (
    SSEEmitter,
    ClientConnection,
    SSEMessage,
    ConnectionState,
)
from chat_shell.streaming.events import ChunkEvent, EventType
from chat_shell.streaming.exceptions import ClientDisconnectedError


class TestSSEMessage:
    """Tests for SSEMessage."""

    def test_create_sse_message(self):
        """Test creating an SSE message."""
        msg = SSEMessage(
            event="content",
            data='{"text": "Hello"}',
            id="123",
            retry=5000,
        )

        assert msg.event == "content"
        assert msg.data == '{"text": "Hello"}'
        assert msg.id == "123"
        assert msg.retry == 5000

    def test_to_sse_format(self):
        """Test converting to SSE wire format."""
        msg = SSEMessage(
            event="content",
            data='{"text": "Hello"}',
            id="123",
        )

        formatted = msg.to_sse_format()

        assert "event: content" in formatted
        assert 'data: {"text": "Hello"}' in formatted
        assert "id: 123" in formatted
        assert formatted.endswith("\n\n")

    def test_to_sse_format_multiline_data(self):
        """Test SSE format with multiline data."""
        msg = SSEMessage(
            event="content",
            data="Line 1\nLine 2\nLine 3",
        )

        formatted = msg.to_sse_format()

        assert "data: Line 1" in formatted
        assert "data: Line 2" in formatted
        assert "data: Line 3" in formatted

    def test_to_sse_format_with_comment(self):
        """Test SSE format with comment."""
        msg = SSEMessage(
            event="heartbeat",
            data="",
            comment="keepalive",
        )

        formatted = msg.to_sse_format()

        assert ": keepalive" in formatted


class TestClientConnection:
    """Tests for ClientConnection."""

    def test_create_client_connection(self):
        """Test creating a client connection."""
        client = ClientConnection(
            client_id="client-1",
            stream_id="stream-1",
        )

        assert client.client_id == "client-1"
        assert client.stream_id == "stream-1"
        assert client.state == ConnectionState.CONNECTED
        assert client.is_active is True

    def test_mark_active(self):
        """Test marking client as active."""
        client = ClientConnection(
            client_id="client-1",
            stream_id="stream-1",
        )

        # Set last activity to past
        client.last_activity = datetime.utcnow() - timedelta(minutes=1)

        client.mark_active()

        assert (datetime.utcnow() - client.last_activity).total_seconds() < 1

    def test_is_stale(self):
        """Test stale detection."""
        client = ClientConnection(
            client_id="client-1",
            stream_id="stream-1",
        )

        # Set last activity to past
        client.last_activity = datetime.utcnow() - timedelta(seconds=120)

        assert client.is_stale(timeout_seconds=60) is True
        assert client.is_stale(timeout_seconds=180) is False

    def test_disconnect(self):
        """Test disconnecting client."""
        client = ClientConnection(
            client_id="client-1",
            stream_id="stream-1",
        )

        client.disconnect()

        assert client.state == ConnectionState.DISCONNECTING

    @pytest.mark.asyncio
    async def test_wait_for_disconnect(self):
        """Test waiting for disconnect signal."""
        client = ClientConnection(
            client_id="client-1",
            stream_id="stream-1",
        )

        # Disconnect after short delay
        async def delayed_disconnect():
            await asyncio.sleep(0.1)
            client.disconnect()

        asyncio.create_task(delayed_disconnect())

        result = await client.wait_for_disconnect(timeout=1.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_disconnect_timeout(self):
        """Test wait for disconnect with timeout."""
        client = ClientConnection(
            client_id="client-1",
            stream_id="stream-1",
        )

        result = await client.wait_for_disconnect(timeout=0.1)

        assert result is False


class TestSSEEmitter:
    """Tests for SSEEmitter."""

    @pytest.fixture
    async def emitter(self):
        """Create a fresh SSEEmitter."""
        emitter = SSEEmitter(
            heartbeat_interval=0.1,  # Short for testing
            enable_heartbeats=False,  # Disable for most tests
        )
        yield emitter
        await emitter.close()

    @pytest.mark.asyncio
    async def test_register_client(self, emitter):
        """Test registering a client."""
        client = await emitter.register_client(
            stream_id="stream-1",
            client_id="client-1",
        )

        assert client.client_id == "client-1"
        assert client.stream_id == "stream-1"

    @pytest.mark.asyncio
    async def test_register_client_generates_id(self, emitter):
        """Test that client ID is generated if not provided."""
        client = await emitter.register_client(stream_id="stream-1")

        assert client.client_id is not None
        assert len(client.client_id) > 0

    @pytest.mark.asyncio
    async def test_unregister_client(self, emitter):
        """Test unregistering a client."""
        client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

        await emitter.unregister_client("client-1")

        # Client should be disconnected
        with pytest.raises(ClientDisconnectedError):
            await emitter.emit("client-1", ChunkEvent(offset=0, session_id="test", text="Hello"))

    @pytest.mark.asyncio
    async def test_emit_to_client(self, emitter):
        """Test emitting an event to a client."""
        client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

        event = ChunkEvent(offset=0, session_id="test", text="Hello")

        result = await emitter.emit("client-1", event)

        assert result is True

    @pytest.mark.asyncio
    async def test_emit_to_disconnected_client_raises(self, emitter):
        """Test that emitting to disconnected client raises error."""
        with pytest.raises(ClientDisconnectedError):
            await emitter.emit("nonexistent", ChunkEvent(offset=0, session_id="test", text="Hello"))

    @pytest.mark.asyncio
    async def test_emit_assigns_sequence(self, emitter):
        """Test that emit assigns sequence numbers to SSE messages."""
        client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

        event1 = ChunkEvent(offset=0, session_id="test", text="Hello")
        event2 = ChunkEvent(offset=1, session_id="test", text="World")

        await emitter.emit("client-1", event1)
        await emitter.emit("client-1", event2)

        # Check that messages were queued with sequence IDs
        # (events are immutable, so sequence is passed to SSE message)
        msg1 = client.queue.get_nowait()
        msg2 = client.queue.get_nowait()

        assert msg1.id == "1"
        assert msg2.id == "2"

    @pytest.mark.asyncio
    async def test_emit_to_stream(self, emitter):
        """Test emitting to all clients on a stream."""
        client1 = await emitter.register_client(stream_id="stream-1", client_id="client-1")
        client2 = await emitter.register_client(stream_id="stream-1", client_id="client-2")
        client3 = await emitter.register_client(stream_id="stream-2", client_id="client-3")

        event = ChunkEvent(offset=0, session_id="test", text="Hello")

        results = await emitter.emit_to_stream("stream-1", event)

        assert results["client-1"] is True
        assert results["client-2"] is True
        assert "client-3" not in results

    @pytest.mark.asyncio
    async def test_emit_batch(self, emitter):
        """Test emitting batch of events."""
        client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

        events = [
            ChunkEvent(offset=i, session_id="test", text=f"Message {i}")
            for i in range(5)
        ]

        count = await emitter.emit_batch("client-1", events)

        assert count == 5

    @pytest.mark.asyncio
    async def test_get_client(self, emitter):
        """Test getting client info."""
        await emitter.register_client(stream_id="stream-1", client_id="client-1")

        client = await emitter.get_client("client-1")

        assert client is not None
        assert client.client_id == "client-1"

        nonexistent = await emitter.get_client("nonexistent")
        assert nonexistent is None

    @pytest.mark.asyncio
    async def test_get_stream_clients(self, emitter):
        """Test getting all clients for a stream."""
        await emitter.register_client(stream_id="stream-1", client_id="client-1")
        await emitter.register_client(stream_id="stream-1", client_id="client-2")
        await emitter.register_client(stream_id="stream-2", client_id="client-3")

        clients = await emitter.get_stream_clients("stream-1")

        assert len(clients) == 2
        client_ids = {c.client_id for c in clients}
        assert client_ids == {"client-1", "client-2"}

    @pytest.mark.asyncio
    async def test_disconnect_stream(self, emitter):
        """Test disconnecting all clients from a stream."""
        await emitter.register_client(stream_id="stream-1", client_id="client-1")
        await emitter.register_client(stream_id="stream-1", client_id="client-2")

        await emitter.disconnect_stream("stream-1")

        clients = await emitter.get_stream_clients("stream-1")
        assert len(clients) == 0

    @pytest.mark.asyncio
    async def test_disconnect_stale_clients(self, emitter):
        """Test disconnecting stale clients."""
        client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

        # Set last activity to past
        client.last_activity = datetime.utcnow() - timedelta(seconds=120)

        disconnected = await emitter.disconnect_stale_clients(timeout_seconds=60)

        assert disconnected == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, emitter):
        """Test getting emitter statistics."""
        await emitter.register_client(stream_id="stream-1", client_id="client-1")
        await emitter.register_client(stream_id="stream-1", client_id="client-2")
        await emitter.register_client(stream_id="stream-2", client_id="client-3")

        stats = await emitter.get_stats()

        assert stats["total_clients"] == 3
        assert stats["total_streams"] == 2
        assert stats["clients_per_stream"]["stream-1"] == 2
        assert stats["clients_per_stream"]["stream-2"] == 1

    @pytest.mark.asyncio
    async def test_event_generator(self, emitter):
        """Test the event generator."""
        client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

        # Emit an event
        event = ChunkEvent(offset=0, session_id="test", text="Hello")
        await emitter.emit("client-1", event)

        # Collect events from generator
        events = []
        async for sse_str in emitter.event_generator("client-1"):
            events.append(sse_str)
            if len(events) >= 1:
                break

        assert len(events) == 1
        assert "event: chunk" in events[0]

    @pytest.mark.asyncio
    async def test_close(self, emitter):
        """Test closing the emitter."""
        await emitter.register_client(stream_id="stream-1", client_id="client-1")
        await emitter.register_client(stream_id="stream-2", client_id="client-2")

        await emitter.close()

        stats = await emitter.get_stats()
        assert stats["total_clients"] == 0


class TestSSEEmitterWithHeartbeats:
    """Tests for SSEEmitter with heartbeats enabled."""

    @pytest.mark.asyncio
    async def test_heartbeat_sent(self):
        """Test that heartbeats are sent to clients."""
        emitter = SSEEmitter(
            heartbeat_interval=0.05,  # Very short for testing
            enable_heartbeats=True,
        )

        try:
            client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

            # Wait for heartbeat
            await asyncio.sleep(0.1)

            # Check that something was queued
            assert not client.queue.empty()

        finally:
            await emitter.close()

    @pytest.mark.asyncio
    async def test_heartbeat_disconnects_stalled_client(self):
        """Test that stalled clients are disconnected."""
        emitter = SSEEmitter(
            heartbeat_interval=0.05,
            max_queue_size=1,  # Small queue
            enable_heartbeats=True,
        )

        try:
            client = await emitter.register_client(stream_id="stream-1", client_id="client-1")

            # Fill the queue without consuming
            try:
                while True:
                    event = ChunkEvent(offset=0, session_id="test", text="X")
                    await emitter.emit("client-1", event, timeout=0.01)
            except Exception:
                pass

            # Wait for heartbeat to detect stall
            await asyncio.sleep(0.15)

            # Client should be disconnecting
            assert client.state in (ConnectionState.DISCONNECTING, ConnectionState.DISCONNECTED)

        finally:
            await emitter.close()
