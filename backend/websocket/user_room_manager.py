"""User room manager for personal notification rooms.

Manages WebSocket connections for user-specific rooms, enabling
personal notifications and event delivery.

Epic 17: Real-time Event Broadcasting
"""

import asyncio
from typing import Dict, Optional, Set

from fastapi import WebSocket


class UserRoomManager:
    """Manages WebSocket connections for user rooms.

    Provides room-based message routing for user-specific notifications.
    Each user can have multiple connected clients (devices/tabs) that
    receive broadcast messages.
    """

    def __init__(self):
        """Initialize the user room manager."""
        # user_id -> set of WebSocket connections
        self._user_rooms: Dict[int, Set[WebSocket]] = {}
        # user_id -> room metadata
        self._metadata: Dict[int, Dict] = {}
        # websocket -> user_id mapping for reverse lookup
        self._websocket_users: Dict[WebSocket, int] = {}
        self._lock = asyncio.Lock()

    async def join_user(
        self,
        user_id: int,
        websocket: WebSocket,
        client_info: Optional[Dict] = None,
    ) -> None:
        """Add a WebSocket connection to a user room.

        Args:
            user_id: The user ID to join.
            websocket: The WebSocket connection.
            client_info: Optional client information (device, etc.).
        """
        async with self._lock:
            if user_id not in self._user_rooms:
                self._user_rooms[user_id] = set()
                self._metadata[user_id] = {
                    "created_at": asyncio.get_event_loop().time(),
                    "client_count": 0,
                }
            self._user_rooms[user_id].add(websocket)
            self._websocket_users[websocket] = user_id
            self._metadata[user_id]["client_count"] = len(self._user_rooms[user_id])

    async def leave_user(
        self,
        user_id: int,
        websocket: WebSocket,
    ) -> None:
        """Remove a WebSocket connection from a user room.

        Args:
            user_id: The user ID to leave.
            websocket: The WebSocket connection.
        """
        async with self._lock:
            await self._remove_websocket(user_id, websocket)

    async def leave_by_websocket(self, websocket: WebSocket) -> Optional[int]:
        """Remove a WebSocket connection using the websocket object.

        This is useful when the user_id is not known (e.g., on disconnect).

        Args:
            websocket: The WebSocket connection to remove.

        Returns:
            The user_id if found, None otherwise.
        """
        async with self._lock:
            user_id = self._websocket_users.get(websocket)
            if user_id is not None:
                await self._remove_websocket(user_id, websocket)
                return user_id
            return None

    async def _remove_websocket(self, user_id: int, websocket: WebSocket) -> None:
        """Internal method to remove a websocket from a user room.

        Args:
            user_id: The user ID.
            websocket: The WebSocket connection.
        """
        if user_id in self._user_rooms:
            self._user_rooms[user_id].discard(websocket)
            if user_id in self._metadata:
                self._metadata[user_id]["client_count"] = len(self._user_rooms[user_id])

            # Clean up empty rooms
            if not self._user_rooms[user_id]:
                del self._user_rooms[user_id]
                if user_id in self._metadata:
                    del self._metadata[user_id]

        # Remove reverse mapping
        if websocket in self._websocket_users:
            del self._websocket_users[websocket]

    async def broadcast_to_user(
        self,
        user_id: int,
        message: Dict,
        exclude: Optional[WebSocket] = None,
    ) -> int:
        """Broadcast a message to all clients in a user room.

        Args:
            user_id: The user ID to broadcast to.
            message: The message to broadcast.
            exclude: Optional WebSocket to exclude from broadcast.

        Returns:
            Number of clients the message was sent to.
        """
        if user_id not in self._user_rooms:
            return 0

        disconnected = []
        sent_count = 0

        for ws in list(self._user_rooms[user_id]):
            if ws == exclude:
                continue
            try:
                await ws.send_json(message)
                sent_count += 1
            except Exception:
                # Mark for cleanup
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.leave_user(user_id, ws)

        return sent_count

    async def send_to_client(
        self,
        websocket: WebSocket,
        message: Dict,
    ) -> bool:
        """Send a message to a specific client.

        Args:
            websocket: The WebSocket connection.
            message: The message to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            return False

    def get_client_count(self, user_id: int) -> int:
        """Get the number of connected clients for a user.

        Args:
            user_id: The user ID.

        Returns:
            Number of connected clients.
        """
        return len(self._user_rooms.get(user_id, set()))

    def get_user_id_for_websocket(self, websocket: WebSocket) -> Optional[int]:
        """Get the user ID associated with a WebSocket connection.

        Args:
            websocket: The WebSocket connection.

        Returns:
            User ID if found, None otherwise.
        """
        return self._websocket_users.get(websocket)

    def get_room_info(self, user_id: int) -> Optional[Dict]:
        """Get information about a user room.

        Args:
            user_id: The user ID.

        Returns:
            Room metadata or None if room doesn't exist.
        """
        if user_id not in self._metadata:
            return None
        return {
            **self._metadata[user_id],
            "user_id": user_id,
        }

    def get_all_rooms(self) -> Dict[int, int]:
        """Get all active user rooms with client counts.

        Returns:
            Dictionary mapping user_id to client count.
        """
        return {
            user_id: len(clients)
            for user_id, clients in self._user_rooms.items()
        }

    def is_user_connected(self, user_id: int) -> bool:
        """Check if a user has any connected clients.

        Args:
            user_id: The user ID.

        Returns:
            True if user has connected clients, False otherwise.
        """
        return user_id in self._user_rooms and len(self._user_rooms[user_id]) > 0


# Global user room manager instance
_user_room_manager: Optional[UserRoomManager] = None


def get_user_room_manager() -> UserRoomManager:
    """Get the global user room manager instance.

    Returns:
        The global UserRoomManager instance.
    """
    global _user_room_manager
    if _user_room_manager is None:
        _user_room_manager = UserRoomManager()
    return _user_room_manager
