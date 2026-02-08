"""WebSocket support for Backend API.

Provides WebSocket endpoints for real-time chat communication.

Epic 14: WebSocket Chat Endpoint
Epic 16: Chat Session State Management
"""

from backend.websocket.manager import TaskRoomManager, get_room_manager
from backend.websocket.session_manager import SessionManager, SessionState, get_session_manager

__all__ = [
    "TaskRoomManager",
    "get_room_manager",
    "SessionManager",
    "SessionState",
    "get_session_manager",
]
