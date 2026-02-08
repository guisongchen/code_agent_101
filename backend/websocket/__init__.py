"""WebSocket support for Backend API.

Provides WebSocket endpoints for real-time chat communication.

Epic 14: WebSocket Chat Endpoint
"""

from backend.websocket.manager import TaskRoomManager, get_room_manager

__all__ = [
    "TaskRoomManager",
    "get_room_manager",
]
