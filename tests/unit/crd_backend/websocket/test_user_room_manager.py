"""Tests for UserRoomManager.

Tests: 10 tests covering user room management functionality
- Room creation and joining
- Room leaving and cleanup
- Broadcasting messages
- Client counting
- WebSocket to user mapping

Epic 17: Real-time Event Broadcasting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.websocket.user_room_manager import UserRoomManager, get_user_room_manager

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_17,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_17
@pytest.mark.unit
@pytest.mark.backend
class TestUserRoomManager:
    """Test suite for UserRoomManager - 10 tests."""

    async def test_user_room_manager_initialization(self):
        """Test user room manager initializes with empty rooms."""
        manager = UserRoomManager()

        assert manager._user_rooms == {}
        assert manager._metadata == {}
        assert manager._websocket_users == {}

    async def test_join_user_creates_room(self):
        """Test joining a user creates a new room."""
        manager = UserRoomManager()
        websocket = MagicMock()
        user_id = 123

        await manager.join_user(user_id, websocket)

        assert user_id in manager._user_rooms
        assert websocket in manager._user_rooms[user_id]
        assert manager.get_client_count(user_id) == 1

    async def test_join_user_multiple_clients(self):
        """Test multiple clients can join the same user room."""
        manager = UserRoomManager()
        user_id = 123

        ws1 = MagicMock()
        ws2 = MagicMock()

        await manager.join_user(user_id, ws1)
        await manager.join_user(user_id, ws2)

        assert manager.get_client_count(user_id) == 2
        assert ws1 in manager._user_rooms[user_id]
        assert ws2 in manager._user_rooms[user_id]

    async def test_leave_user_removes_client(self):
        """Test leaving a user removes the client."""
        manager = UserRoomManager()
        user_id = 123
        websocket = MagicMock()

        await manager.join_user(user_id, websocket)
        assert manager.get_client_count(user_id) == 1

        await manager.leave_user(user_id, websocket)
        assert manager.get_client_count(user_id) == 0

    async def test_leave_user_cleans_empty_room(self):
        """Test leaving the last client cleans up the room."""
        manager = UserRoomManager()
        user_id = 123
        websocket = MagicMock()

        await manager.join_user(user_id, websocket)
        await manager.leave_user(user_id, websocket)

        assert user_id not in manager._user_rooms
        assert user_id not in manager._metadata

    async def test_leave_by_websocket(self):
        """Test leaving by websocket object."""
        manager = UserRoomManager()
        user_id = 123
        websocket = MagicMock()

        await manager.join_user(user_id, websocket)
        result = await manager.leave_by_websocket(websocket)

        assert result == user_id
        assert manager.get_client_count(user_id) == 0

    async def test_broadcast_to_user(self):
        """Test broadcasting message to all clients in a user room."""
        manager = UserRoomManager()
        user_id = 123

        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.join_user(user_id, ws1)
        await manager.join_user(user_id, ws2)

        message = {"type": "test", "data": "hello"}
        sent_count = await manager.broadcast_to_user(user_id, message)

        assert sent_count == 2
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    async def test_get_user_id_for_websocket(self):
        """Test getting user ID for a websocket."""
        manager = UserRoomManager()
        user_id = 123
        websocket = MagicMock()

        await manager.join_user(user_id, websocket)

        result = manager.get_user_id_for_websocket(websocket)
        assert result == user_id

    async def test_is_user_connected(self):
        """Test checking if user is connected."""
        manager = UserRoomManager()
        user_id = 123
        websocket = MagicMock()

        assert manager.is_user_connected(user_id) is False

        await manager.join_user(user_id, websocket)
        assert manager.is_user_connected(user_id) is True

        await manager.leave_user(user_id, websocket)
        assert manager.is_user_connected(user_id) is False

    async def test_get_user_room_manager_singleton(self):
        """Test get_user_room_manager returns singleton instance."""
        manager1 = get_user_room_manager()
        manager2 = get_user_room_manager()

        assert manager1 is manager2
