"""Tests for EventBus.

Tests: 8 tests covering event publishing and broadcasting
- Event subscription
- Publishing to rooms
- Publishing to tasks
- Publishing to users

Epic 17: Real-time Event Broadcasting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from backend.websocket.event_bus import EventBus, get_event_bus

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_17,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_17
@pytest.mark.unit
@pytest.mark.backend
class TestEventBus:
    """Test suite for EventBus - 8 tests."""

    async def test_event_bus_initialization(self):
        """Test event bus initializes correctly."""
        bus = EventBus()

        assert bus._subscribers == {}
        assert bus._room_routing is True
        assert bus._redis_enabled is False

    async def test_subscribe_and_unsubscribe(self):
        """Test subscribing and unsubscribing from events."""
        bus = EventBus()
        callback = AsyncMock()

        # Subscribe
        bus.subscribe("test:event", callback)
        assert "test:event" in bus._subscribers
        assert callback in bus._subscribers["test:event"]

        # Unsubscribe
        bus.unsubscribe("test:event", callback)
        assert callback not in bus._subscribers.get("test:event", set())

    async def test_publish_to_subscribers(self):
        """Test publishing events to subscribers."""
        bus = EventBus()
        callback = AsyncMock()

        bus.subscribe("test:event", callback)

        event_data = {"message": "hello"}
        await bus.publish("test:event", event_data)

        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["type"] == "test:event"
        assert call_args["data"] == event_data

    async def test_publish_to_task_room(self):
        """Test publishing events to task room."""
        bus = EventBus()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")

        with patch("backend.websocket.event_bus.get_room_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.broadcast_to_task = AsyncMock(return_value=3)
            mock_get_manager.return_value = mock_manager

            event_data = {"status": "running"}
            sent = await bus.publish_to_task(task_id, "task:status", event_data)

            assert sent == 3
            mock_manager.broadcast_to_task.assert_called_once()
            call_args = mock_manager.broadcast_to_task.call_args[0]
            assert call_args[0] == task_id
            assert call_args[1]["type"] == "task:status"
            assert call_args[1]["data"]["task_id"] == str(task_id)

    async def test_publish_to_user_room(self):
        """Test publishing events to user room."""
        bus = EventBus()
        user_id = 123

        with patch("backend.websocket.event_bus.get_user_room_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.broadcast_to_user = AsyncMock(return_value=2)
            mock_get_manager.return_value = mock_manager

            event_data = {"notification": "Task completed"}
            sent = await bus.publish_to_user(user_id, "user:notification", event_data)

            assert sent == 2
            mock_manager.broadcast_to_user.assert_called_once()
            call_args = mock_manager.broadcast_to_user.call_args[0]
            assert call_args[0] == user_id
            assert call_args[1]["type"] == "user:notification"
            assert call_args[1]["data"]["user_id"] == user_id

    async def test_multiple_subscribers(self):
        """Test multiple subscribers receive events."""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        bus.subscribe("test:event", callback1)
        bus.subscribe("test:event", callback2)

        await bus.publish("test:event", {"data": "test"})

        callback1.assert_called_once()
        callback2.assert_called_once()

    async def test_unsubscribe_removes_only_specified_callback(self):
        """Test unsubscribing only removes the specified callback."""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        bus.subscribe("test:event", callback1)
        bus.subscribe("test:event", callback2)

        bus.unsubscribe("test:event", callback1)

        await bus.publish("test:event", {"data": "test"})

        callback1.assert_not_called()
        callback2.assert_called_once()

    async def test_get_event_bus_singleton(self):
        """Test get_event_bus returns singleton instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2
