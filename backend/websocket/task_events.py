"""Task event broadcasting integration.

Integrates Task service operations with event broadcasting to notify
connected clients of task lifecycle changes.

Epic 17: Real-time Event Broadcasting
"""

from typing import Any, Dict, Optional
from uuid import UUID

from backend.websocket.event_bus import get_event_bus
from backend.websocket.manager import get_room_manager


# Event type constants
EVENT_TASK_CREATED = "task:created"
EVENT_TASK_STARTED = "task:started"
EVENT_TASK_COMPLETED = "task:completed"
EVENT_TASK_FAILED = "task:failed"
EVENT_TASK_CANCELLED = "task:cancelled"
EVENT_TASK_STATUS_CHANGED = "task:status"
EVENT_TASK_DELETED = "task:deleted"


class TaskEventBroadcaster:
    """Broadcasts task lifecycle events to connected clients.

    Provides methods to broadcast task events to:
    - Task rooms (clients watching a specific task)
    - User rooms (task owner/creator)
    """

    def __init__(self):
        """Initialize the task event broadcaster."""
        self.event_bus = get_event_bus()

    async def broadcast_task_created(
        self,
        task_id: UUID,
        task_data: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> int:
        """Broadcast task created event.

        Args:
            task_id: The created task ID.
            task_data: Task data including name, namespace, status, etc.
            user_id: Optional user ID who created the task.

        Returns:
            Number of clients the event was sent to.
        """
        event_data = {
            "task_id": str(task_id),
            **task_data,
        }

        sent_count = 0

        # Broadcast to task room
        sent_count += await self.event_bus.publish_to_task(
            task_id,
            EVENT_TASK_CREATED,
            event_data,
        )

        # Notify task creator's user room
        if user_id:
            sent_count += await self.event_bus.publish_to_user(
                user_id,
                EVENT_TASK_CREATED,
                event_data,
            )

        return sent_count

    async def broadcast_task_started(
        self,
        task_id: UUID,
        task_data: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> int:
        """Broadcast task started event.

        Args:
            task_id: The task ID.
            task_data: Task data.
            user_id: Optional user ID who owns the task.

        Returns:
            Number of clients the event was sent to.
        """
        event_data = {
            "task_id": str(task_id),
            "status": "running",
            "previous_status": "pending",
            **task_data,
        }

        sent_count = await self.event_bus.publish_to_task(
            task_id,
            EVENT_TASK_STARTED,
            event_data,
        )

        if user_id:
            sent_count += await self.event_bus.publish_to_user(
                user_id,
                EVENT_TASK_STATUS_CHANGED,
                event_data,
            )

        return sent_count

    async def broadcast_task_completed(
        self,
        task_id: UUID,
        task_data: Dict[str, Any],
        output: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """Broadcast task completed event.

        Args:
            task_id: The task ID.
            task_data: Task data.
            output: Optional task output.
            user_id: Optional user ID who owns the task.

        Returns:
            Number of clients the event was sent to.
        """
        event_data = {
            "task_id": str(task_id),
            "status": "completed",
            "previous_status": "running",
            **task_data,
        }

        if output:
            event_data["output"] = output

        sent_count = await self.event_bus.publish_to_task(
            task_id,
            EVENT_TASK_COMPLETED,
            event_data,
        )

        if user_id:
            sent_count += await self.event_bus.publish_to_user(
                user_id,
                EVENT_TASK_STATUS_CHANGED,
                event_data,
            )

        return sent_count

    async def broadcast_task_failed(
        self,
        task_id: UUID,
        task_data: Dict[str, Any],
        error: str,
        user_id: Optional[int] = None,
    ) -> int:
        """Broadcast task failed event.

        Args:
            task_id: The task ID.
            task_data: Task data.
            error: Error message.
            user_id: Optional user ID who owns the task.

        Returns:
            Number of clients the event was sent to.
        """
        event_data = {
            "task_id": str(task_id),
            "status": "failed",
            "previous_status": "running",
            "error": error,
            **task_data,
        }

        sent_count = await self.event_bus.publish_to_task(
            task_id,
            EVENT_TASK_FAILED,
            event_data,
        )

        if user_id:
            sent_count += await self.event_bus.publish_to_user(
                user_id,
                EVENT_TASK_STATUS_CHANGED,
                event_data,
            )

        return sent_count

    async def broadcast_task_cancelled(
        self,
        task_id: UUID,
        task_data: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> int:
        """Broadcast task cancelled event.

        Args:
            task_id: The task ID.
            task_data: Task data.
            user_id: Optional user ID who owns the task.

        Returns:
            Number of clients the event was sent to.
        """
        event_data = {
            "task_id": str(task_id),
            "status": "cancelled",
            "previous_status": "running",
            **task_data,
        }

        sent_count = await self.event_bus.publish_to_task(
            task_id,
            EVENT_TASK_CANCELLED,
            event_data,
        )

        if user_id:
            sent_count += await self.event_bus.publish_to_user(
                user_id,
                EVENT_TASK_STATUS_CHANGED,
                event_data,
            )

        return sent_count

    async def broadcast_task_status_changed(
        self,
        task_id: UUID,
        new_status: str,
        previous_status: str,
        task_data: Dict[str, Any],
        user_id: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Broadcast generic task status change event.

        Args:
            task_id: The task ID.
            new_status: New task status.
            previous_status: Previous task status.
            task_data: Task data.
            user_id: Optional user ID who owns the task.
            additional_data: Optional additional data to include.

        Returns:
            Number of clients the event was sent to.
        """
        event_data = {
            "task_id": str(task_id),
            "status": new_status,
            "previous_status": previous_status,
            **task_data,
        }

        if additional_data:
            event_data.update(additional_data)

        sent_count = await self.event_bus.publish_to_task(
            task_id,
            EVENT_TASK_STATUS_CHANGED,
            event_data,
        )

        if user_id:
            sent_count += await self.event_bus.publish_to_user(
                user_id,
                EVENT_TASK_STATUS_CHANGED,
                event_data,
            )

        return sent_count

    async def broadcast_task_deleted(
        self,
        task_id: UUID,
        task_data: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> int:
        """Broadcast task deleted event.

        Args:
            task_id: The deleted task ID.
            task_data: Task data.
            user_id: Optional user ID who deleted the task.

        Returns:
            Number of clients the event was sent to.
        """
        event_data = {
            "task_id": str(task_id),
            **task_data,
        }

        sent_count = await self.event_bus.publish_to_task(
            task_id,
            EVENT_TASK_DELETED,
            event_data,
        )

        if user_id:
            sent_count += await self.event_bus.publish_to_user(
                user_id,
                EVENT_TASK_DELETED,
                event_data,
            )

        return sent_count


# Global task event broadcaster instance
_task_event_broadcaster: Optional[TaskEventBroadcaster] = None


def get_task_event_broadcaster() -> TaskEventBroadcaster:
    """Get the global task event broadcaster instance.

    Returns:
        The global TaskEventBroadcaster instance.
    """
    global _task_event_broadcaster
    if _task_event_broadcaster is None:
        _task_event_broadcaster = TaskEventBroadcaster()
    return _task_event_broadcaster
