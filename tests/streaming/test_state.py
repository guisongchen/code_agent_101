"""
Tests for streaming state management.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from chat_shell.streaming.state import (
    StreamingState,
    StreamSession,
    StreamStatus,
    ClientInfo,
)
from chat_shell.streaming.exceptions import (
    StreamNotFoundError,
    StreamAlreadyExistsError,
    InvalidOffsetError,
)


class TestStreamSession:
    """Tests for StreamSession model."""

    def test_create_stream_session(self):
        """Test creating a stream session."""
        session = StreamSession(
            stream_id="stream-1",
            session_id="session-1",
        )

        assert session.stream_id == "stream-1"
        assert session.session_id == "session-1"
        assert session.status == StreamStatus.PENDING
        assert session.current_offset == 0

    def test_get_next_offset(self):
        """Test getting next offset increments counter."""
        session = StreamSession(
            stream_id="stream-1",
            session_id="session-1",
        )

        offset1 = session.get_next_offset()
        offset2 = session.get_next_offset()
        offset3 = session.get_next_offset()

        assert offset1 == 0
        assert offset2 == 1
        assert offset3 == 2
        assert session.current_offset == 3

    def test_is_active(self):
        """Test is_active status check."""
        pending = StreamSession(stream_id="s1", session_id="sess1", status=StreamStatus.PENDING)
        running = StreamSession(stream_id="s2", session_id="sess1", status=StreamStatus.RUNNING)
        paused = StreamSession(stream_id="s3", session_id="sess1", status=StreamStatus.PAUSED)
        completed = StreamSession(stream_id="s4", session_id="sess1", status=StreamStatus.COMPLETED)

        assert pending.is_active() is True
        assert running.is_active() is True
        assert paused.is_active() is True
        assert completed.is_active() is False

    def test_is_terminal(self):
        """Test is_terminal status check."""
        running = StreamSession(stream_id="s1", session_id="sess1", status=StreamStatus.RUNNING)
        completed = StreamSession(stream_id="s2", session_id="sess1", status=StreamStatus.COMPLETED)
        cancelled = StreamSession(stream_id="s3", session_id="sess1", status=StreamStatus.CANCELLED)
        error = StreamSession(stream_id="s4", session_id="sess1", status=StreamStatus.ERROR)

        assert running.is_terminal() is False
        assert completed.is_terminal() is True
        assert cancelled.is_terminal() is True
        assert error.is_terminal() is True

    def test_mark_complete(self):
        """Test marking session as complete."""
        session = StreamSession(stream_id="s1", session_id="sess1")

        session.mark_complete()

        assert session.status == StreamStatus.COMPLETED
        assert session.completed_at is not None
        assert session.is_terminal() is True

    def test_mark_cancelled(self):
        """Test marking session as cancelled."""
        session = StreamSession(stream_id="s1", session_id="sess1")

        session.mark_cancelled(reason="User request")

        assert session.status == StreamStatus.CANCELLED
        assert session.metadata.get("cancellation_reason") == "User request"

    def test_mark_error(self):
        """Test marking session as errored."""
        session = StreamSession(stream_id="s1", session_id="sess1")

        session.mark_error("TOOL_ERROR", "Tool failed", {"tool": "calculator"})

        assert session.status == StreamStatus.ERROR
        assert session.error_info is not None
        assert session.error_info["error_code"] == "TOOL_ERROR"
        assert session.error_info["details"]["tool"] == "calculator"

    def test_update_checkpoint(self):
        """Test updating checkpoint data."""
        session = StreamSession(stream_id="s1", session_id="sess1")

        session.update_checkpoint(100, {"messages": []})

        assert session.checkpoint_data["offset"] == 100
        assert session.checkpoint_data["data"]["messages"] == []

    def test_add_remove_client(self):
        """Test adding and removing clients."""
        session = StreamSession(stream_id="s1", session_id="sess1")

        session.add_client("client-1")
        session.add_client("client-2")

        assert "client-1" in session.client_ids
        assert "client-2" in session.client_ids

        session.remove_client("client-1")

        assert "client-1" not in session.client_ids
        assert "client-2" in session.client_ids


class TestStreamingState:
    """Tests for StreamingState."""

    @pytest.fixture
    async def state(self):
        """Create a fresh StreamingState for testing."""
        return StreamingState()

    @pytest.mark.asyncio
    async def test_create_stream(self, state):
        """Test creating a stream."""
        session = await state.create_stream(
            stream_id="stream-1",
            session_id="session-1",
            metadata={"key": "value"},
        )

        assert session.stream_id == "stream-1"
        assert session.session_id == "session-1"
        assert session.metadata["key"] == "value"

    @pytest.mark.asyncio
    async def test_create_duplicate_stream_raises_error(self, state):
        """Test that creating duplicate stream raises error."""
        await state.create_stream("stream-1", "session-1")

        with pytest.raises(StreamAlreadyExistsError):
            await state.create_stream("stream-1", "session-1")

    @pytest.mark.asyncio
    async def test_get_stream(self, state):
        """Test getting a stream by ID."""
        await state.create_stream("stream-1", "session-1")

        session = await state.get_stream("stream-1")

        assert session.stream_id == "stream-1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_stream_raises_error(self, state):
        """Test that getting nonexistent stream raises error."""
        with pytest.raises(StreamNotFoundError):
            await state.get_stream("nonexistent")

    @pytest.mark.asyncio
    async def test_get_or_create_stream(self, state):
        """Test get_or_create stream method."""
        # First call creates
        session1 = await state.get_or_create_stream("stream-1", "session-1")
        assert session1.stream_id == "stream-1"

        # Second call returns existing
        session2 = await state.get_or_create_stream("stream-1", "session-1")
        assert session2.stream_id == "stream-1"
        assert session1 is session2

    @pytest.mark.asyncio
    async def test_update_stream_status(self, state):
        """Test updating stream status."""
        await state.create_stream("stream-1", "session-1")

        session = await state.update_stream_status("stream-1", StreamStatus.RUNNING)

        assert session.status == StreamStatus.RUNNING

    @pytest.mark.asyncio
    async def test_delete_stream(self, state):
        """Test deleting a stream."""
        await state.create_stream("stream-1", "session-1")

        await state.delete_stream("stream-1")

        with pytest.raises(StreamNotFoundError):
            await state.get_stream("stream-1")

    @pytest.mark.asyncio
    async def test_get_session_streams(self, state):
        """Test getting all streams for a session."""
        await state.create_stream("stream-1", "session-1")
        await state.create_stream("stream-2", "session-1")
        await state.create_stream("stream-3", "session-2")

        session1_streams = await state.get_session_streams("session-1")

        assert len(session1_streams) == 2
        stream_ids = {s.stream_id for s in session1_streams}
        assert stream_ids == {"stream-1", "stream-2"}

    @pytest.mark.asyncio
    async def test_register_client(self, state):
        """Test registering a client."""
        await state.create_stream("stream-1", "session-1")

        client = await state.register_client("client-1", "stream-1", start_offset=10)

        assert client.client_id == "client-1"
        assert client.last_offset == 10
        assert client.is_active is True

    @pytest.mark.asyncio
    async def test_disconnect_client(self, state):
        """Test disconnecting a client."""
        await state.create_stream("stream-1", "session-1")
        await state.register_client("client-1", "stream-1")

        await state.disconnect_client("client-1", "stream-1")

        client = await state.get_client("client-1")
        assert client.is_active is False
        assert client.disconnected_at is not None

    @pytest.mark.asyncio
    async def test_update_client_offset(self, state):
        """Test updating client offset."""
        await state.create_stream("stream-1", "session-1")
        await state.register_client("client-1", "stream-1", start_offset=0)

        await state.update_client_offset("client-1", 100)

        client = await state.get_client("client-1")
        assert client.last_offset == 100

    @pytest.mark.asyncio
    async def test_get_recovery_offset(self, state):
        """Test getting recovery offset for client."""
        await state.create_stream("stream-1", "session-1")
        await state.register_client("client-1", "stream-1", start_offset=50)

        offset = await state.get_recovery_offset("stream-1", "client-1")

        assert offset == 50

    @pytest.mark.asyncio
    async def test_get_recovery_offset_new_client(self, state):
        """Test getting recovery offset for new client."""
        await state.create_stream("stream-1", "session-1")

        offset = await state.get_recovery_offset("stream-1", "new-client")

        assert offset == 0

    @pytest.mark.asyncio
    async def test_validate_offset(self, state):
        """Test validating offsets."""
        await state.create_stream("stream-1", "session-1")
        session = await state.get_stream("stream-1")
        session.current_offset = 100

        # Valid offset
        assert await state.validate_offset("stream-1", 50) is True
        assert await state.validate_offset("stream-1", 0) is True
        assert await state.validate_offset("stream-1", 100) is True

    @pytest.mark.asyncio
    async def test_validate_offset_negative_raises(self, state):
        """Test that negative offset raises error."""
        await state.create_stream("stream-1", "session-1")

        with pytest.raises(InvalidOffsetError):
            await state.validate_offset("stream-1", -1)

    @pytest.mark.asyncio
    async def test_validate_offset_too_large_raises(self, state):
        """Test that offset beyond current raises error."""
        await state.create_stream("stream-1", "session-1")
        session = await state.get_stream("stream-1")
        session.current_offset = 50

        with pytest.raises(InvalidOffsetError):
            await state.validate_offset("stream-1", 51)

    @pytest.mark.asyncio
    async def test_get_active_streams(self, state):
        """Test getting active streams."""
        await state.create_stream("stream-1", "session-1")
        await state.create_stream("stream-2", "session-1")
        await state.create_stream("stream-3", "session-2")

        # Mark one as completed
        session = await state.get_stream("stream-3")
        session.mark_complete()

        active = await state.get_active_streams()

        assert len(active) == 2
        active_ids = {s.stream_id for s in active}
        assert active_ids == {"stream-1", "stream-2"}

    @pytest.mark.asyncio
    async def test_get_stats(self, state):
        """Test getting statistics."""
        await state.create_stream("stream-1", "session-1")
        await state.create_stream("stream-2", "session-1")

        session = await state.get_stream("stream-2")
        session.mark_complete()

        await state.register_client("client-1", "stream-1")

        stats = await state.get_stats()

        assert stats["total_streams"] == 2
        assert stats["active_streams"] == 1
        assert stats["completed_streams"] == 1
        assert stats["total_clients"] == 1

    @pytest.mark.asyncio
    async def test_cleanup_old_streams(self, state):
        """Test cleaning up old completed streams."""
        await state.create_stream("stream-1", "session-1")
        await state.create_stream("stream-2", "session-1")

        # Mark as completed with old timestamp
        session = await state.get_stream("stream-1")
        session.mark_complete()
        session.completed_at = datetime.utcnow() - timedelta(hours=2)

        # Keep stream-2 running

        removed = await state.cleanup_old_streams(max_age_seconds=3600)

        # stream-1 should be removed, stream-2 remains
        assert removed == 1

        with pytest.raises(StreamNotFoundError):
            await state.get_stream("stream-1")

        # stream-2 should still exist
        remaining = await state.get_stream("stream-2")
        assert remaining.stream_id == "stream-2"


class TestClientInfo:
    """Tests for ClientInfo model."""

    def test_create_client_info(self):
        """Test creating client info."""
        client = ClientInfo(client_id="client-1")

        assert client.client_id == "client-1"
        assert client.is_active is True
        assert client.last_offset == 0

    def test_is_stale(self):
        """Test stale detection."""
        client = ClientInfo(client_id="client-1")
        # Manually set last activity to be old
        client.last_activity = datetime.utcnow() - timedelta(minutes=2)

        assert client.is_stale(timeout_seconds=60) is True
        assert client.is_stale(timeout_seconds=300) is False
