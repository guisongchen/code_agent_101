"""WebSocket room manager for task-based chat.

Manages WebSocket connections for task rooms, enabling multiple clients
to connect to the same task chat session.

Epic 14: WebSocket Chat Endpoint
"""

import asyncio
from typing import Dict, Optional, Set
from uuid import UUID

from fastapi import WebSocket


class TaskRoomManager:
    """Manages WebSocket connections for task rooms.

    Provides room-based message routing for multi-client scenarios.
    Each task can have multiple connected clients that receive
    broadcast messages.
    """

    def __init__(self):
        """Initialize the room manager."""
        # task_id -> set of WebSocket connections
        self._rooms: Dict[UUID, Set[WebSocket]] = {}
        # task_id -> room metadata
        self._metadata: Dict[UUID, Dict] = {}
        self._lock = asyncio.Lock()

    async def join_task(
        self,
        task_id: UUID,
        websocket: WebSocket,
        client_info: Optional[Dict] = None,
    ) -> None:
        """Add a WebSocket connection to a task room.

        Args:
            task_id: The task ID to join.
            websocket: The WebSocket connection.
            client_info: Optional client information (user_id, etc.).
        """
        async with self._lock:
            if task_id not in self._rooms:
                self._rooms[task_id] = set()
                self._metadata[task_id] = {
                    "created_at": asyncio.get_event_loop().time(),
                    "client_count": 0,
                }
            self._rooms[task_id].add(websocket)
            self._metadata[task_id]["client_count"] = len(self._rooms[task_id])

    async def leave_task(
        self,
        task_id: UUID,
        websocket: WebSocket,
    ) -> None:
        """Remove a WebSocket connection from a task room.

        Args:
            task_id: The task ID to leave.
            websocket: The WebSocket connection.
        """
        async with self._lock:
            if task_id in self._rooms:
                self._rooms[task_id].discard(websocket)
                if task_id in self._metadata:
                    self._metadata[task_id]["client_count"] = len(self._rooms[task_id])

                # Clean up empty rooms
                if not self._rooms[task_id]:
                    del self._rooms[task_id]
                    if task_id in self._metadata:
                        del self._metadata[task_id]

    async def broadcast_to_task(
        self,
        task_id: UUID,
        message: Dict,
        exclude: Optional[WebSocket] = None,
    ) -> int:
        """Broadcast a message to all clients in a task room.

        Args:
            task_id: The task ID to broadcast to.
            message: The message to broadcast.
            exclude: Optional WebSocket to exclude from broadcast.

        Returns:
            Number of clients the message was sent to.
        """
        if task_id not in self._rooms:
            return 0

        disconnected = []
        sent_count = 0

        for ws in list(self._rooms[task_id]):
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
            await self.leave_task(task_id, ws)

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

    def get_client_count(self, task_id: UUID) -> int:
        """Get the number of connected clients for a task.

        Args:
            task_id: The task ID.

        Returns:
            Number of connected clients.
        """
        return len(self._rooms.get(task_id, set()))

    def get_room_info(self, task_id: UUID) -> Optional[Dict]:
        """Get information about a task room.

        Args:
            task_id: The task ID.

        Returns:
            Room metadata or None if room doesn't exist.
        """
        if task_id not in self._metadata:
            return None
        return {
            **self._metadata[task_id],
            "task_id": str(task_id),
        }

    def get_all_rooms(self) -> Dict[UUID, int]:
        """Get all active rooms with client counts.

        Returns:
            Dictionary mapping task_id to client count.
        """
        return {
            task_id: len(clients)
            for task_id, clients in self._rooms.items()
        }


# Global room manager instance
_room_manager: Optional[TaskRoomManager] = None


def get_room_manager() -> TaskRoomManager:
    """Get the global room manager instance.

    Returns:
        The global TaskRoomManager instance.
    """
    global _room_manager
    if _room_manager is None:
        _room_manager = TaskRoomManager()
    return _room_manager
