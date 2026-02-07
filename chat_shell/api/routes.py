"""
API routes for HTTP mode.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from ..agent.agent import ChatAgent
from ..config import config
from ..streaming import get_streaming_core, StreamConfig
from .schemas import (
    ChatRequest,
    ChatResponse,
    ChatEvent,
    SessionStatus,
    SessionHistory,
    HealthResponse,
    ErrorResponse,
    StreamRecoveryRequest,
    StreamRecoveryResponse,
    StreamStatusExtended,
)
from .dependencies import get_agent, get_session_manager
from .sse import (
    stream_chat_events,
    create_sse_stream,
    recover_sse_stream,
    cancel_sse_stream,
    get_stream_status,
)


router = APIRouter()


@router.post(
    "/response",
    response_model=ChatResponse,
    responses={500: {"model": ErrorResponse}},
)
async def start_chat(
    request: ChatRequest,
    agent: ChatAgent = Depends(get_agent),
) -> ChatResponse:
    """
    Start a new chat session.

    Creates a new subtask for processing the chat messages.
    Returns immediately with a subtask_id for polling or streaming.

    For streaming with recovery support, use the offset parameter to resume
    from a specific position in an existing stream.
    """
    subtask_id = str(uuid.uuid4())
    session_id = request.session_id or f"session-{int(datetime.now().timestamp())}"

    # Store session info
    from .app import app_state
    app_state["active_sessions"][subtask_id] = {
        "session_id": session_id,
        "status": "running",
        "created_at": datetime.now(),
        "messages": request.messages,
    }

    # If streaming requested, return SSE stream
    if request.stream:
        # Use new streaming infrastructure
        streaming_core = get_streaming_core()

        # Ensure streaming core is started
        if not streaming_core._running:
            await streaming_core.start()

        # Create stream configuration
        stream_config = StreamConfig(
            enable_recovery=True,
            emit_checkpoints=True,
            checkpoint_interval=50,
        )

        # Create SSE stream and get generator
        client_id, event_generator = await create_sse_stream(
            agent=agent,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            session_id=session_id,
            subtask_id=subtask_id,
            resume_from_offset=request.offset,
            show_thinking=request.metadata.get("show_thinking", False) if request.metadata else False,
            config=stream_config,
        )

        return EventSourceResponse(
            event_generator,
            headers={
                "X-Subtask-ID": subtask_id,
                "X-Client-ID": client_id,
                "X-Session-ID": session_id,
            },
        )

    # Non-streaming: process and return subtask_id
    return ChatResponse(
        subtask_id=subtask_id,
        session_id=session_id,
        status="created",
    )


@router.get("/response/{subtask_id}", response_model=SessionStatus)
async def get_session_status(
    subtask_id: str,
    session_manager=Depends(get_session_manager),
) -> SessionStatus:
    """
    Get status of a chat session.

    Used for polling when not using streaming.
    """
    from .app import app_state

    session = app_state["active_sessions"].get(subtask_id)
    if not session:
        raise HTTPException(status_code=404, detail="Subtask not found")

    return SessionStatus(
        subtask_id=subtask_id,
        session_id=session["session_id"],
        status=session["status"],
        created_at=session["created_at"],
        updated_at=datetime.now(),
        message_count=len(session.get("messages", [])),
    )


@router.get("/response/{subtask_id}/stream-status", response_model=StreamStatusExtended)
async def get_stream_status_endpoint(
    subtask_id: str,
    session_manager=Depends(get_session_manager),
) -> StreamStatusExtended:
    """
    Get detailed stream status including buffer and recovery information.

    This endpoint provides information about the streaming infrastructure
    state for a given subtask, including buffer coverage and client count.
    """
    try:
        status = await get_stream_status(subtask_id)
        return StreamStatusExtended(**status)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/response/{subtask_id}/recover", response_model=StreamRecoveryResponse)
async def recover_stream_endpoint(
    subtask_id: str,
    recovery_request: StreamRecoveryRequest,
    session_manager=Depends(get_session_manager),
) -> StreamRecoveryResponse:
    """
    Check if a stream can be recovered from a specific offset.

    This endpoint allows clients to check recovery possibilities before
    attempting to reconnect to a stream.
    """
    streaming_core = get_streaming_core()

    try:
        recovery_info = await streaming_core.get_recovery_info(
            subtask_id, recovery_request.offset
        )

        return StreamRecoveryResponse(
            stream_id=subtask_id,
            can_recover=recovery_info["can_recover"],
            from_offset=recovery_request.offset,
            available_offsets=recovery_info["buffer_coverage"],
            message=None if recovery_info["can_recover"] else "Offset not available in buffer",
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/response/{subtask_id}")
async def cancel_session(
    subtask_id: str,
    reason: str = Query(None, description="Reason for cancellation"),
    session_manager=Depends(get_session_manager),
):
    """
    Cancel a running chat session.

    This gracefully cancels the stream, notifies all connected clients,
    and updates the session status. Use this for explicit cancellation
    rather than just closing the connection.
    """
    from .app import app_state

    if subtask_id not in app_state["active_sessions"]:
        raise HTTPException(status_code=404, detail="Subtask not found")

    # Cancel via streaming infrastructure
    try:
        await cancel_sse_stream(subtask_id, reason=reason or "User requested cancellation")
    except Exception:
        # Stream might not be active in streaming core
        pass

    # Mark as cancelled in app state
    app_state["active_sessions"][subtask_id]["status"] = "cancelled"
    if reason:
        app_state["active_sessions"][subtask_id]["cancellation_reason"] = reason

    return {
        "status": "cancelled",
        "subtask_id": subtask_id,
        "reason": reason,
    }


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    """
    import time
    from .app import app_state

    uptime = time.time() - app_state["start_time"] if app_state["start_time"] else 0

    # Get streaming stats if available
    streaming_stats = {}
    try:
        streaming_core = get_streaming_core()
        streaming_stats = await streaming_core.get_stats()
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        uptime_seconds=uptime,
        active_sessions=len(app_state["active_sessions"]),
        models_available=[config.openai.model],
    )


@router.get("/health/streaming")
async def streaming_health_check():
    """
    Detailed health check for streaming infrastructure.
    """
    try:
        streaming_core = get_streaming_core()
        stats = await streaming_core.get_stats()

        return {
            "status": "healthy",
            "streaming": stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "error": str(e)}
        )


@router.get("/sessions/{session_id}/history", response_model=SessionHistory)
async def get_session_history(
    session_id: str,
) -> SessionHistory:
    """
    Get full message history for a session.
    """
    # Implementation would fetch from storage
    # For now, return empty history
    return SessionHistory(
        session_id=session_id,
        messages=[],
        total_messages=0,
    )


@router.get("/streams/{stream_id}/events")
async def get_stream_events(
    stream_id: str,
    from_offset: int = Query(0, description="Offset to start from"),
    limit: int = Query(100, description="Maximum events to return"),
    session_manager=Depends(get_session_manager),
):
    """
    Get buffered events for a stream (for recovery/debugging).

    This endpoint allows retrieving historical events from the buffer
    for stream recovery or debugging purposes.
    """
    streaming_core = get_streaming_core()

    try:
        context = await streaming_core.get_stream(stream_id)
        events = await context.buffer.get_range(from_offset, limit=limit)

        return {
            "stream_id": stream_id,
            "from_offset": from_offset,
            "events": [
                {
                    "type": e.event_type.value,
                    "offset": e.offset,
                    "timestamp": e.timestamp.isoformat(),
                    "data": e.to_sse_payload().get("data", {}),
                }
                for e in events
            ],
            "total": len(events),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
