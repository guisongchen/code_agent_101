"""WebSocket endpoint for user notifications.

Provides real-time personal notifications and event delivery to users
across all their connected devices.

Epic 17: Real-time Event Broadcasting
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from backend.websocket.auth import authenticate_websocket
from backend.websocket.user_room_manager import get_user_room_manager

router = APIRouter()


# Event types
EVENT_USER_NOTIFICATION = "user:notification"
EVENT_USER_TASK_UPDATE = "user:task_update"
EVENT_PING = "ping"
EVENT_PONG = "pong"


@router.websocket("/user/notifications")
async def user_notifications_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
):
    """WebSocket endpoint for user notifications.

    Provides real-time personal notifications to users. This endpoint
    connects the client to their user room for receiving events like
    task updates, system notifications, etc.

    Args:
        websocket: The WebSocket connection.
        token: Optional JWT token for authentication.

    Events:
        Client -> Server:
        - ping: Keep-alive ping

        Server -> Client:
        - user:notification: General user notification
        - user:task_update: Task status update for user's tasks
        - pong: Keep-alive response
    """
    user_room_manager = get_user_room_manager()

    # Authenticate connection
    user = await authenticate_websocket(websocket, token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    # Accept connection
    await websocket.accept()

    # Join user room
    await user_room_manager.join_user(
        user.id,
        websocket,
        client_info={"client_type": "notifications"},
    )

    try:
        while True:
            # Receive message from client
            try:
                message = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            # Handle message based on type
            msg_type = message.get("type")

            if msg_type == EVENT_PING:
                await websocket.send_json({"type": EVENT_PONG})
            else:
                # Unknown event type - just acknowledge
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Unknown event type: {msg_type}"},
                })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # Clean up
        await user_room_manager.leave_user(user.id, websocket)
        try:
            await websocket.close()
        except Exception:
            pass
