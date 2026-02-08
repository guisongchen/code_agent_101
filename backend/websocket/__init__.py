"""WebSocket support for Backend API.

Provides WebSocket endpoints for real-time chat communication.

Epic 14: WebSocket Chat Endpoint
Epic 16: Chat Session State Management
Epic 17: Real-time Event Broadcasting
"""

from backend.websocket.event_bus import EventBus, get_event_bus
from backend.websocket.manager import TaskRoomManager, get_room_manager
from backend.websocket.session_manager import SessionManager, SessionState, get_session_manager
from backend.websocket.task_events import (
    TaskEventBroadcaster,
    get_task_event_broadcaster,
)
from backend.websocket.user_room_manager import UserRoomManager, get_user_room_manager

__all__ = [
    "EventBus",
    "get_event_bus",
    "TaskRoomManager",
    "get_room_manager",
    "SessionManager",
    "SessionState",
    "get_session_manager",
    "TaskEventBroadcaster",
    "get_task_event_broadcaster",
    "UserRoomManager",
    "get_user_room_manager",
]
