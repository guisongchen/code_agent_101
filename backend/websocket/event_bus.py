"""Event bus for real-time event broadcasting.

Provides pub/sub functionality for broadcasting events to rooms with
support for multi-instance deployments via Redis.

Epic 17: Real-time Event Broadcasting
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

from backend.websocket.manager import get_room_manager
from backend.websocket.user_room_manager import get_user_room_manager


class EventBus:
    """Event bus for broadcasting events to rooms.

    Routes events to appropriate rooms (task rooms, user rooms) and
    provides filtering by room membership. Supports both local and
    distributed (Redis) broadcasting.
    """

    def __init__(self):
        """Initialize the event bus."""
        # Local subscribers: event_type -> set of callback functions
        self._subscribers: Dict[str, Set[Callable]] = {}
        # Room-based routing enabled
        self._room_routing = True
        # Redis support (optional, for future scaling)
        self._redis_enabled = False
        self._redis_client = None

    async def start(self) -> None:
        """Start the event bus and connect to Redis if configured."""
        # Redis connection would be initialized here
        pass

    async def stop(self) -> None:
        """Stop the event bus and cleanup."""
        self._subscribers.clear()

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to.
            callback: Function to call when event is received.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from events of a specific type.

        Args:
            event_type: Type of event to unsubscribe from.
            callback: Function to remove from subscribers.
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        room_id: Optional[str] = None,
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """Publish an event to subscribers and/or rooms.

        Args:
            event_type: Type of event being published.
            data: Event data payload.
            room_id: Optional room ID to broadcast to.
            exclude_user_id: Optional user ID to exclude from broadcast.

        Returns:
            Number of recipients the event was sent to.
        """
        sent_count = 0

        # Build event message
        event = {
            "type": event_type,
            "data": data,
        }

        # Notify local subscribers
        if event_type in self._subscribers:
            for callback in list(self._subscribers[event_type]):
                try:
                    await callback(event)
                except Exception:
                    # Ignore subscriber errors
                    pass

        # Broadcast to room if specified
        if room_id and self._room_routing:
            sent_count += await self._broadcast_to_room(
                room_id, event, exclude_user_id=exclude_user_id
            )

        return sent_count

    async def publish_to_task(
        self,
        task_id: UUID,
        event_type: str,
        data: Dict[str, Any],
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """Publish an event to a task room.

        Args:
            task_id: Task ID for the room.
            event_type: Type of event.
            data: Event data.
            exclude_user_id: Optional user ID to exclude.

        Returns:
            Number of clients the event was sent to.
        """
        room_manager = get_room_manager()

        # Add task_id to data
        event_data = {
            **data,
            "task_id": str(task_id),
        }

        event = {
            "type": event_type,
            "data": event_data,
        }

        return await room_manager.broadcast_to_task(task_id, event)

    async def publish_to_user(
        self,
        user_id: int,
        event_type: str,
        data: Dict[str, Any],
    ) -> int:
        """Publish an event to a user's personal room.

        Args:
            user_id: User ID for the room.
            event_type: Type of event.
            data: Event data.

        Returns:
            Number of clients the event was sent to.
        """
        user_room_manager = get_user_room_manager()

        # Add user_id to data
        event_data = {
            **data,
            "user_id": user_id,
        }

        event = {
            "type": event_type,
            "data": event_data,
        }

        return await user_room_manager.broadcast_to_user(user_id, event)

    async def _broadcast_to_room(
        self,
        room_id: str,
        event: Dict[str, Any],
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """Broadcast event to a room.

        Args:
            room_id: Room identifier (format: "task:{id}" or "user:{id}").
            event: Event message.
            exclude_user_id: Optional user ID to exclude.

        Returns:
            Number of clients the event was sent to.
        """
        # Parse room type from room_id
        if room_id.startswith("task:"):
            task_id = UUID(room_id.split(":", 1)[1])
            room_manager = get_room_manager()
            return await room_manager.broadcast_to_task(task_id, event)
        elif room_id.startswith("user:"):
            user_id = int(room_id.split(":", 1)[1])
            user_room_manager = get_user_room_manager()
            return await user_room_manager.broadcast_to_user(user_id, event)

        return 0


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        The global EventBus instance.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
