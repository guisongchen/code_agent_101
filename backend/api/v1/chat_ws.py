"""WebSocket endpoints for real-time chat communication.

Implements WebSocket endpoint for task-based chat with streaming support.

Epic 14: WebSocket Chat Endpoint
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db_session
from backend.schemas import ChatMessage, CurrentUser
from backend.services import ChatService, TaskService
from backend.websocket.manager import get_room_manager
from backend.websocket.auth import authenticate_websocket

router = APIRouter()


# =============================================================================
# WebSocket Event Types
# =============================================================================

# Client -> Server events
EVENT_CHAT_SEND = "chat:send"
EVENT_CHAT_CANCEL = "chat:cancel"
EVENT_TASK_JOIN = "task:join"
EVENT_TASK_LEAVE = "task:leave"
EVENT_PING = "ping"

# Server -> Client events
EVENT_CHAT_START = "chat:start"
EVENT_CHAT_CHUNK = "chat:chunk"
EVENT_CHAT_DONE = "chat:done"
EVENT_CHAT_ERROR = "chat:error"
EVENT_CHAT_CANCELLED = "chat:cancelled"
EVENT_CHAT_TOOL_START = "chat:tool_start"
EVENT_CHAT_TOOL_RESULT = "chat:tool_result"
EVENT_CHAT_THINKING = "chat:thinking"
EVENT_TASK_STATUS = "task:status"
EVENT_PONG = "pong"


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@router.websocket("/tasks/{task_id}/chat")
async def task_chat_websocket(
    websocket: WebSocket,
    task_id: UUID,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
    session: AsyncSession = Depends(get_db_session),
):
    """WebSocket endpoint for task-based chat.

    Provides real-time bidirectional chat communication for tasks.
    Supports streaming AI responses and multi-client rooms.

    Args:
        websocket: The WebSocket connection.
        task_id: The task ID to chat with.
        token: Optional JWT token for authentication.
        session: Database session.

    Events:
        Client -> Server:
        - chat:send - Send a chat message
        - chat:cancel - Cancel ongoing generation
        - task:join - Join task room (implicit on connect)
        - task:leave - Leave task room
        - ping - Keep-alive ping

        Server -> Client:
        - chat:start - AI started generating
        - chat:chunk - Streaming content chunk
        - chat:done - AI response completed
        - chat:error - Error occurred
        - chat:cancelled - Stream was cancelled
        - chat:tool_start - Tool execution started
        - chat:tool_result - Tool execution completed
        - chat:thinking - Agent thinking/thought process
        - task:status - Task status update
        - pong - Keep-alive response
    """
    room_manager = get_room_manager()
    chat_service = ChatService(session)
    task_service = TaskService(session)

    # Authenticate connection
    user = await authenticate_websocket(websocket, token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    # Verify task exists
    task = await task_service.get(task_id)
    if not task:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
        return

    # Accept connection
    await websocket.accept()

    # Join task room
    await room_manager.join_task(
        task_id,
        websocket,
        client_info={"user_id": user.id, "username": user.username},
    )

    # Track active generation for cancellation
    active_generation: Optional[asyncio.Task] = None

    try:
        while True:
            # Receive message from client
            try:
                message = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            # Handle message based on type
            msg_type = message.get("type")

            if msg_type == EVENT_CHAT_SEND:
                # Cancel any active generation
                if active_generation and not active_generation.done():
                    active_generation.cancel()
                    try:
                        await active_generation
                    except asyncio.CancelledError:
                        pass

                # Start new generation
                active_generation = asyncio.create_task(
                    _handle_chat_send(
                        websocket=websocket,
                        room_manager=room_manager,
                        chat_service=chat_service,
                        task=task,
                        message=message,
                        user=user,
                    )
                )

            elif msg_type == EVENT_CHAT_CANCEL:
                if active_generation and not active_generation.done():
                    active_generation.cancel()
                    await room_manager.broadcast_to_task(
                        task_id,
                        {
                            "type": EVENT_CHAT_CANCELLED,
                            "data": {"reason": "User cancelled"},
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

            elif msg_type == EVENT_TASK_JOIN:
                # Already joined, just confirm
                await websocket.send_json({
                    "type": EVENT_TASK_STATUS,
                    "data": {
                        "status": "joined",
                        "task_id": str(task_id),
                        "client_count": room_manager.get_client_count(task_id),
                    },
                })

            elif msg_type == EVENT_TASK_LEAVE:
                break

            elif msg_type == EVENT_PING:
                await websocket.send_json({"type": EVENT_PONG})

            else:
                await websocket.send_json({
                    "type": EVENT_CHAT_ERROR,
                    "data": {
                        "message": f"Unknown event type: {msg_type}",
                        "error_code": "UNKNOWN_EVENT_TYPE",
                    },
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": EVENT_CHAT_ERROR,
                "data": {
                    "message": str(e),
                    "error_code": "INTERNAL_ERROR",
                },
            })
        except Exception:
            pass
    finally:
        # Clean up
        if active_generation and not active_generation.done():
            active_generation.cancel()

        await room_manager.leave_task(task_id, websocket)
        await websocket.close()


async def _handle_chat_send(
    websocket: WebSocket,
    room_manager: Any,
    chat_service: ChatService,
    task: Any,
    message: Dict[str, Any],
    user: CurrentUser,
) -> None:
    """Handle a chat:send event.

    Streams chat events from chat_shell to all connected clients.

    Args:
        websocket: The WebSocket connection that sent the message.
        room_manager: The room manager for broadcasting.
        chat_service: The chat service for execution.
        task: The task being chatted with.
        message: The chat message from client.
        user: The authenticated user.
    """
    task_id = task.id

    # Extract message data
    content = message.get("message", "")
    thread_id = message.get("thread_id") or str(task_id)
    show_thinking = message.get("show_thinking", True)

    if not content:
        await websocket.send_json({
            "type": EVENT_CHAT_ERROR,
            "data": {
                "message": "Message content is required",
                "error_code": "EMPTY_MESSAGE",
            },
        })
        return

    # Get bot name from task spec or use default
    # Task spec may contain bot reference
    bot_name = _get_bot_name_from_task(task)
    namespace = task.namespace or "default"

    # Prepare messages
    messages: List[Dict[str, str]] = [{"role": "user", "content": content}]

    # Send start event to all clients
    await room_manager.broadcast_to_task(
        task_id,
        {
            "type": EVENT_CHAT_START,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    try:
        # Stream chat events
        async for event in chat_service.execute_chat(
            bot_name=bot_name,
            messages=messages,
            namespace=namespace,
            thread_id=thread_id,
            show_thinking=show_thinking,
        ):
            # Map chat_shell events to WebSocket events
            ws_event = _map_event_to_websocket(event)
            if ws_event:
                await room_manager.broadcast_to_task(task_id, ws_event)

        # Send completion event
        await room_manager.broadcast_to_task(
            task_id,
            {
                "type": EVENT_CHAT_DONE,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    except asyncio.CancelledError:
        # Handle cancellation
        await room_manager.broadcast_to_task(
            task_id,
            {
                "type": EVENT_CHAT_CANCELLED,
                "data": {"reason": "Generation cancelled"},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        raise

    except Exception as e:
        await room_manager.broadcast_to_task(
            task_id,
            {
                "type": EVENT_CHAT_ERROR,
                "data": {
                    "message": str(e),
                    "error_code": "CHAT_EXECUTION_ERROR",
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


def _map_event_to_websocket(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Map chat_shell events to WebSocket events.

    Args:
        event: The chat_shell event.

    Returns:
        WebSocket event or None if event should be skipped.
    """
    event_type = event.get("type")
    event_data = event.get("data", {})

    if event_type == "content":
        return {
            "type": EVENT_CHAT_CHUNK,
            "data": {"text": event_data.get("text", "")},
            "timestamp": datetime.utcnow().isoformat(),
        }

    elif event_type == "tool_call":
        return {
            "type": EVENT_CHAT_TOOL_START,
            "data": {
                "tool": event_data.get("tool"),
                "input": event_data.get("args"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    elif event_type == "tool_result":
        return {
            "type": EVENT_CHAT_TOOL_RESULT,
            "data": {
                "tool": event_data.get("tool"),
                "result": event_data.get("result"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    elif event_type == "thinking":
        return {
            "type": EVENT_CHAT_THINKING,
            "data": {"text": event_data.get("text", "")},
            "timestamp": datetime.utcnow().isoformat(),
        }

    elif event_type == "error":
        return {
            "type": EVENT_CHAT_ERROR,
            "data": {
                "message": event_data.get("message", "Unknown error"),
                "error_code": event_data.get("error_code", "UNKNOWN"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    return None


def _get_bot_name_from_task(task: Any) -> str:
    """Extract bot name from task.

    Args:
        task: The task object.

    Returns:
        Bot name to use for chat.
    """
    # Check task spec for bot reference
    spec = task.spec or {}

    # If task has a team_id, we need to get the bot from the team
    # For now, use a default or look for bot in spec
    if "bot_name" in spec:
        return spec["bot_name"]

    if "botRef" in spec:
        return spec["botRef"].get("name", "default")

    # Default bot name
    return "default"
