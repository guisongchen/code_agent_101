"""WebSocket endpoints for real-time chat communication.

Implements WebSocket endpoint for task-based chat with streaming support.

Epic 14: WebSocket Chat Endpoint
Epic 15: Message History Management
Epic 16: Chat Session State Management
Epic 17: Real-time Event Broadcasting
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db_session
from backend.schemas import ChatMessage, CurrentUser, SessionCreateRequest
from backend.services import ChatService, MessageService, SessionService, TaskService
from backend.websocket.manager import get_room_manager
from backend.websocket.session_manager import get_session_manager
from backend.websocket.user_room_manager import get_user_room_manager
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
EVENT_HISTORY_REQUEST = "history:request"
EVENT_SESSION_RECOVER = "session:recover"
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
EVENT_HISTORY_SYNC = "history:sync"
EVENT_SESSION_STATE = "session:state"
EVENT_SESSION_RECOVERED = "session:recovered"
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
    Supports streaming AI responses, multi-client rooms, and session management.

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
        - session:recover - Recover a previous session
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
        - session:state - Session state update
        - session:recovered - Session recovery result
        - pong - Keep-alive response
    """
    room_manager = get_room_manager()
    user_room_manager = get_user_room_manager()
    session_manager = get_session_manager()
    chat_service = ChatService(session)
    task_service = TaskService(session)
    message_service = MessageService(session)
    session_service = SessionService(session)

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

    # Create or recover session
    websocket_id = str(id(websocket))
    chat_session = None
    session_id = None

    try:
        # Create new session
        session_request = SessionCreateRequest(
            user_id=user.id,
            task_id=task_id,
            thread_id=str(task_id),
            meta={"client_type": "websocket", "connected_at": datetime.utcnow().isoformat()},
        )
        chat_session = await session_service.create(session_request)
        await session.commit()
        session_id = chat_session.session_id

        # Track in memory
        await session_manager.create_session(
            session_id=session_id,
            user_id=user.id,
            task_id=task_id,
            thread_id=str(task_id),
        )
        await session_manager.associate_websocket(session_id, websocket_id)

        # Send session state to client
        await websocket.send_json({
            "type": EVENT_SESSION_STATE,
            "session_id": session_id,
            "status": "active",
            "connection_count": 1,
            "recovery_token": chat_session.recovery_token,
            "expires_at": chat_session.expires_at.isoformat(),
        })

    except ValueError as e:
        # Session limit reached
        await websocket.send_json({
            "type": EVENT_CHAT_ERROR,
            "data": {
                "message": str(e),
                "error_code": "SESSION_LIMIT_REACHED",
            },
        })
        await websocket.close()
        return

    # Join task room
    await room_manager.join_task(
        task_id,
        websocket,
        client_info={"user_id": user.id, "username": user.username, "session_id": session_id},
    )

    # Join user room for personal notifications
    await user_room_manager.join_user(
        user.id,
        websocket,
        client_info={"task_id": str(task_id), "session_id": session_id},
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
                        message_service=message_service,
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

            elif msg_type == EVENT_HISTORY_REQUEST:
                # Handle history request
                await _handle_history_request(
                    websocket=websocket,
                    message_service=message_service,
                    task_id=task_id,
                    message=message,
                )

            elif msg_type == EVENT_SESSION_RECOVER:
                # Handle session recovery
                await _handle_session_recover(
                    websocket=websocket,
                    session_service=session_service,
                    session_manager=session_manager,
                    current_session_id=session_id,
                    message=message,
                )

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

        # Update session connection count
        if session_id:
            await session_manager.disassociate_websocket(websocket_id)
            await session_service.decrement_connections(session_id)
            await session.commit()

        await room_manager.leave_task(task_id, websocket)
        await user_room_manager.leave_user(user.id, websocket)
        await websocket.close()


async def _handle_chat_send(
    websocket: WebSocket,
    room_manager: Any,
    chat_service: ChatService,
    message_service: MessageService,
    task: Any,
    message: Dict[str, Any],
    user: CurrentUser,
) -> None:
    """Handle a chat:send event.

    Streams chat events from chat_shell to all connected clients.
    Stores messages in database for history.

    Args:
        websocket: The WebSocket connection that sent the message.
        room_manager: The room manager for broadcasting.
        chat_service: The chat service for execution.
        message_service: The message service for history storage.
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

    # Store user message in database
    await message_service.create_user_message(
        task_id=task_id,
        content=content,
        thread_id=thread_id,
        metadata={"user_id": user.id, "username": user.username},
    )

    # Get bot name from task spec or use default
    # Task spec may contain bot reference
    bot_name = _get_bot_name_from_task(task)
    namespace = task.namespace or "default"

    # Prepare messages from history for context
    history_messages = await message_service.get_thread_messages(
        task_id=task_id,
        thread_id=thread_id,
        limit=50,
    )
    messages: List[Dict[str, str]] = [
        {"role": m.role.value, "content": m.content}
        for m in history_messages
    ]

    # Send start event to all clients
    await room_manager.broadcast_to_task(
        task_id,
        {
            "type": EVENT_CHAT_START,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    # Accumulate assistant response for storage
    assistant_content_parts: List[str] = []
    assistant_metadata: Dict[str, Any] = {"model": None, "tool_calls": []}

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

            # Accumulate content for storage
            event_type = event.get("type")
            event_data = event.get("data", {})

            if event_type == "content":
                assistant_content_parts.append(event_data.get("text", ""))
            elif event_type == "tool_call":
                assistant_metadata["tool_calls"].append({
                    "tool": event_data.get("tool"),
                    "input": event_data.get("args"),
                })
            elif event_type == "thinking":
                if "thinking" not in assistant_metadata:
                    assistant_metadata["thinking"] = []
                assistant_metadata["thinking"].append(event_data.get("text", ""))

        # Store assistant response in database
        assistant_content = "".join(assistant_content_parts)
        if assistant_content:
            await message_service.create_assistant_message(
                task_id=task_id,
                content=assistant_content,
                thread_id=thread_id,
                model=assistant_metadata.get("model"),
                metadata=assistant_metadata,
            )

        # Send completion event
        await room_manager.broadcast_to_task(
            task_id,
            {
                "type": EVENT_CHAT_DONE,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    except asyncio.CancelledError:
        # Store partial response before cancellation
        assistant_content = "".join(assistant_content_parts)
        if assistant_content:
            await message_service.create_assistant_message(
                task_id=task_id,
                content=assistant_content + "\n[Cancelled]",
                thread_id=thread_id,
                model=assistant_metadata.get("model"),
                metadata={**assistant_metadata, "cancelled": True},
            )

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


async def _handle_history_request(
    websocket: WebSocket,
    message_service: MessageService,
    task_id: UUID,
    message: Dict[str, Any],
) -> None:
    """Handle a history:request event.

    Sends message history to the requesting client.

    Args:
        websocket: The WebSocket connection.
        message_service: The message service for history retrieval.
        task_id: The task ID.
        message: The history request message.
    """
    from backend.schemas.message import MessageHistoryRequest

    # Extract request parameters
    thread_id = message.get("thread_id") or message.get("threadId") or "default"
    limit = message.get("limit", 50)
    offset = message.get("offset", 0)

    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        limit = 50
    if limit > 1000:
        limit = 1000

    # Validate offset
    if not isinstance(offset, int) or offset < 0:
        offset = 0

    # Build history request
    request = MessageHistoryRequest(
        thread_id=thread_id,
        limit=limit,
        offset=offset,
    )

    try:
        # Get message history
        history = await message_service.get_history(task_id, request)

        # Send history sync event
        await websocket.send_json({
            "type": EVENT_HISTORY_SYNC,
            "task_id": str(task_id),
            "thread_id": thread_id,
            "messages": [
                {
                    "id": str(m.id),
                    "task_id": str(m.task_id),
                    "role": m.role.value,
                    "message_type": m.message_type.value,
                    "content": m.content,
                    "thread_id": m.thread_id,
                    "sequence": m.sequence,
                    "tokens_used": m.tokens_used,
                    "prompt_tokens": m.prompt_tokens,
                    "completion_tokens": m.completion_tokens,
                    "model": m.model,
                    "tool_name": m.tool_name,
                    "tool_call_id": m.tool_call_id,
                    "meta": m.meta,
                    "generated_at": m.generated_at.isoformat() if m.generated_at else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in history.messages
            ],
            "total": history.total,
            "has_more": history.has_more,
        })

    except Exception as e:
        await websocket.send_json({
            "type": EVENT_CHAT_ERROR,
            "data": {
                "message": f"Failed to retrieve history: {str(e)}",
                "error_code": "HISTORY_ERROR",
            },
        })


async def _handle_session_recover(
    websocket: WebSocket,
    session_service: SessionService,
    session_manager: Any,
    current_session_id: Optional[str],
    message: Dict[str, Any],
) -> None:
    """Handle a session:recover event.

    Attempts to recover a previous session and migrate the WebSocket
    connection to the recovered session.

    Args:
        websocket: The WebSocket connection.
        session_service: The session service.
        session_manager: The in-memory session manager.
        current_session_id: The current session ID (if any).
        message: The recovery request message.
    """
    from backend.schemas.session import SessionRecoveryRequest

    recovery_token = message.get("recovery_token") or message.get("recoveryToken")
    if not recovery_token:
        await websocket.send_json({
            "type": EVENT_SESSION_RECOVERED,
            "success": False,
            "message": "Recovery token is required",
        })
        return

    request = SessionRecoveryRequest(
        recovery_token=recovery_token,
        session_id=message.get("session_id") or message.get("sessionId"),
        meta=message.get("meta"),
    )

    try:
        result = await session_service.recover_session(request)

        if result.success and result.session:
            # Update in-memory session tracking
            if current_session_id:
                await session_manager.close_session(current_session_id)

            await session_manager.create_session(
                session_id=result.session.session_id,
                user_id=result.session.user_id,
                task_id=result.session.task_id,
                thread_id=result.session.thread_id,
            )

            await websocket.send_json({
                "type": EVENT_SESSION_RECOVERED,
                "success": True,
                "session_id": result.session.session_id,
                "previous_session_id": current_session_id,
                "recovery_token": result.session.recovery_token,
                "expires_at": result.session.expires_at.isoformat(),
                "message": result.message,
            })
        else:
            await websocket.send_json({
                "type": EVENT_SESSION_RECOVERED,
                "success": False,
                "message": result.message,
            })

    except Exception as e:
        await websocket.send_json({
            "type": EVENT_SESSION_RECOVERED,
            "success": False,
            "message": f"Recovery failed: {str(e)}",
        })
