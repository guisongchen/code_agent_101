"""Tests for TaskRoomManager.

Tests: 8 tests covering room management functionality
- Room creation and joining
- Room leaving and cleanup
- Broadcasting messages
- Client counting

Epic 14: WebSocket Chat Endpoint
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from backend.websocket.manager import TaskRoomManager

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_14,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_14
@pytest.mark.unit
@pytest.mark.backend
class TestTaskRoomManager:
    """Test suite for TaskRoomManager - 8 tests."""

    async def test_room_manager_initialization(self):
        """Test room manager initializes with empty rooms."""
        manager = TaskRoomManager()

        assert manager._rooms == {}
        assert manager._metadata == {}

    async def test_join_task_creates_room(self):
        """Test joining a task creates a new room."""
        manager = TaskRoomManager()
        websocket = MagicMock()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")

        await manager.join_task(task_id, websocket)

        assert task_id in manager._rooms
        assert websocket in manager._rooms[task_id]
        assert manager.get_client_count(task_id) == 1

    async def test_join_task_multiple_clients(self):
        """Test multiple clients can join the same task."""
        manager = TaskRoomManager()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")

        ws1 = MagicMock()
        ws2 = MagicMock()

        await manager.join_task(task_id, ws1)
        await manager.join_task(task_id, ws2)

        assert manager.get_client_count(task_id) == 2
        assert ws1 in manager._rooms[task_id]
        assert ws2 in manager._rooms[task_id]

    async def test_leave_task_removes_client(self):
        """Test leaving a task removes the client."""
        manager = TaskRoomManager()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")
        websocket = MagicMock()

        await manager.join_task(task_id, websocket)
        assert manager.get_client_count(task_id) == 1

        await manager.leave_task(task_id, websocket)
        assert manager.get_client_count(task_id) == 0

    async def test_leave_task_cleans_empty_room(self):
        """Test leaving the last client cleans up the room."""
        manager = TaskRoomManager()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")
        websocket = MagicMock()

        await manager.join_task(task_id, websocket)
        await manager.leave_task(task_id, websocket)

        assert task_id not in manager._rooms
        assert task_id not in manager._metadata

    async def test_broadcast_to_task(self):
        """Test broadcasting message to all clients in a room."""
        manager = TaskRoomManager()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")

        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.join_task(task_id, ws1)
        await manager.join_task(task_id, ws2)

        message = {"type": "test", "data": "hello"}
        sent_count = await manager.broadcast_to_task(task_id, message)

        assert sent_count == 2
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    async def test_broadcast_excludes_sender(self):
        """Test broadcasting can exclude the sender."""
        manager = TaskRoomManager()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")

        sender = AsyncMock()
        other = AsyncMock()

        await manager.join_task(task_id, sender)
        await manager.join_task(task_id, other)

        message = {"type": "test", "data": "hello"}
        sent_count = await manager.broadcast_to_task(task_id, message, exclude=sender)

        assert sent_count == 1
        sender.send_json.assert_not_called()
        other.send_json.assert_called_once_with(message)

    async def test_send_to_client(self):
        """Test sending message to specific client."""
        manager = TaskRoomManager()
        websocket = AsyncMock()

        message = {"type": "test", "data": "hello"}
        result = await manager.send_to_client(websocket, message)

        assert result is True
        websocket.send_json.assert_called_once_with(message)

    async def test_send_to_client_failure(self):
        """Test sending message to disconnected client."""
        manager = TaskRoomManager()
        websocket = AsyncMock()
        websocket.send_json.side_effect = Exception("Connection closed")

        message = {"type": "test", "data": "hello"}
        result = await manager.send_to_client(websocket, message)

        assert result is False

    async def test_get_all_rooms(self):
        """Test getting all active rooms."""
        manager = TaskRoomManager()

        task1 = UUID("12345678-1234-1234-1234-123456789abc")
        task2 = UUID("12345678-1234-1234-1234-123456789abd")

        await manager.join_task(task1, MagicMock())
        await manager.join_task(task1, MagicMock())
        await manager.join_task(task2, MagicMock())

        rooms = manager.get_all_rooms()

        assert rooms[task1] == 2
        assert rooms[task2] == 1

    async def test_get_room_info(self):
        """Test getting room information."""
        manager = TaskRoomManager()
        task_id = UUID("12345678-1234-1234-1234-123456789abc")

        await manager.join_task(task_id, MagicMock())

        info = manager.get_room_info(task_id)

        assert info is not None
        assert info["task_id"] == str(task_id)
        assert info["client_count"] == 1
        assert "created_at" in info
