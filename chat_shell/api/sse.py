"""
Server-Sent Events streaming for chat responses.

Uses the streaming infrastructure for event management, buffering,
and session recovery.
"""

import asyncio
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from ..agent.agent import ChatAgent
from ..streaming import (
    StreamingCore,
    get_streaming_core,
    StreamContext,
    StreamConfig,
    ChunkEvent,
    ToolStartEvent,
    ToolResultEvent,
    ThinkingEvent,
    ErrorEvent,
    CompleteEvent,
    CancelledEvent,
    BaseStreamEvent,
)
from ..streaming.events import EventType
from .schemas import ChatEvent


async def stream_chat_events(
    agent: ChatAgent,
    messages: list,
    session_id: str,
    subtask_id: str,
    resume_from_offset: Optional[int] = None,
    show_thinking: bool = False,
) -> AsyncGenerator[ChatEvent, None]:
    """
    Stream chat events as SSE using the streaming infrastructure.

    This is the legacy compatibility function. New code should use
    StreamingCore directly.

    Args:
        agent: The ChatAgent instance
        messages: List of messages to process
        session_id: Session identifier
        subtask_id: Subtask/stream identifier
        resume_from_offset: Optional offset to resume from
        show_thinking: Whether to include thinking events

    Yields:
        ChatEvent objects for content, tool calls, and completion.
    """
    streaming_core = get_streaming_core()

    # Ensure streaming core is started
    if not streaming_core._running:
        await streaming_core.start()

    # Create stream configuration
    config = StreamConfig(
        enable_recovery=True,
        emit_checkpoints=True,
        checkpoint_interval=50,
    )

    # Create or get stream context
    try:
        context = await streaming_core.create_stream(
            stream_id=subtask_id,
            session_id=session_id,
            config=config,
            metadata={"show_thinking": show_thinking},
        )
    except Exception:
        # Stream might already exist for recovery
        context = await streaming_core.get_stream(subtask_id)

    # Define event generator from agent
    async def agent_event_generator(ctx: StreamContext) -> AsyncGenerator[BaseStreamEvent, None]:
        """Generate events from agent streaming."""
        try:
            async for event in agent.stream(
                messages=messages,
                thread_id=session_id,
                show_thinking=show_thinking,
            ):
                event_type = event.get("type", "")
                data = event.get("data", {})

                # Convert to formal event types
                if event_type == "content":
                    yield ChunkEvent(
                        offset=0,  # Will be assigned by StreamingCore
                        session_id=session_id,
                        text=data.get("text", ""),
                        is_delta=True,
                    )
                elif event_type == "tool_call":
                    yield ToolStartEvent(
                        offset=0,
                        session_id=session_id,
                        tool_name=data.get("tool", ""),
                        tool_input=data.get("input", {}),
                        tool_call_id=data.get("tool_call_id", ""),
                    )
                elif event_type == "tool_result":
                    yield ToolResultEvent(
                        offset=0,
                        session_id=session_id,
                        tool_name=data.get("tool", ""),
                        tool_call_id=data.get("tool_call_id", ""),
                        result=data.get("result"),
                    )
                elif event_type == "thinking":
                    yield ThinkingEvent(
                        offset=0,
                        session_id=session_id,
                        text=data.get("text", ""),
                    )
                elif event_type == "error":
                    yield ErrorEvent(
                        offset=0,
                        session_id=session_id,
                        error_code="AGENT_ERROR",
                        message=data.get("message", "Unknown error"),
                    )

        except asyncio.CancelledError:
            raise
        except Exception as e:
            yield ErrorEvent(
                offset=0,
                session_id=session_id,
                error_code="STREAM_ERROR",
                message=str(e),
            )

    # Start the stream
    await streaming_core.start_stream(subtask_id, agent_event_generator)

    # Connect a client to receive events
    client = await streaming_core.connect_client(
        stream_id=subtask_id,
        resume_from_offset=resume_from_offset,
    )

    try:
        # Yield events from the streaming core
        async for sse_str in streaming_core.get_event_generator(client.client_id):
            # Parse SSE string back to ChatEvent for compatibility
            # SSE format: "event: <type>\ndata: <json>\n\n"
            event = _parse_sse_to_chat_event(sse_str)
            if event:
                yield event

    except asyncio.CancelledError:
        # Handle cancellation gracefully
        yield ChatEvent(
            event_type="cancelled",
            data={"reason": "Client disconnected"},
        )
        raise
    finally:
        await streaming_core.disconnect_client(client.client_id, subtask_id)


def _parse_sse_to_chat_event(sse_str: str) -> Optional[ChatEvent]:
    """Parse an SSE formatted string to ChatEvent."""
    import json

    lines = sse_str.strip().split("\n")
    event_type = None
    data_str = None

    for line in lines:
        if line.startswith("event: "):
            event_type = line[7:].strip()
        elif line.startswith("data: "):
            data_str = line[6:].strip()

    if event_type and data_str:
        try:
            data = json.loads(data_str)
            # Extract offset and sequence if present in payload
            offset = data.get("offset")
            sequence = data.get("sequence")

            # Map new event types to legacy types
            type_mapping = {
                "chunk": "content",
                "tool_start": "tool_call",
                "tool_result": "tool_result",
                "thinking": "thinking",
                "error": "error",
                "complete": "complete",
                "cancelled": "cancelled",
                "offset": "offset",
            }

            return ChatEvent(
                event_type=type_mapping.get(event_type, event_type),
                data=data.get("data", data),
                offset=offset,
                sequence=sequence,
            )
        except json.JSONDecodeError:
            pass

    return None


async def create_sse_stream(
    agent: ChatAgent,
    messages: List[Dict[str, str]],
    session_id: str,
    subtask_id: str,
    client_id: Optional[str] = None,
    resume_from_offset: Optional[int] = None,
    show_thinking: bool = False,
    config: Optional[StreamConfig] = None,
) -> tuple[str, AsyncGenerator[str, None]]:
    """
    Create a new SSE stream and return the client ID and event generator.

    This is the recommended way to create SSE streams for new code.

    Args:
        agent: The ChatAgent instance
        messages: List of messages to process
        session_id: Session identifier
        subtask_id: Subtask/stream identifier
        client_id: Optional client ID (generated if not provided)
        resume_from_offset: Optional offset to resume from
        show_thinking: Whether to include thinking events
        config: Optional stream configuration

    Returns:
        Tuple of (client_id, event_generator)
    """
    streaming_core = get_streaming_core()

    # Ensure streaming core is started
    if not streaming_core._running:
        await streaming_core.start()

    # Use default config if not provided
    config = config or StreamConfig(
        enable_recovery=True,
        emit_checkpoints=True,
    )

    # Create stream context
    try:
        await streaming_core.create_stream(
            stream_id=subtask_id,
            session_id=session_id,
            config=config,
            metadata={"show_thinking": show_thinking},
        )
    except Exception:
        # Stream might already exist
        pass

    # Define event generator
    async def agent_event_generator(ctx: StreamContext) -> AsyncGenerator[BaseStreamEvent, None]:
        """Generate events from agent streaming."""
        try:
            async for event in agent.stream(
                messages=messages,
                thread_id=session_id,
                show_thinking=show_thinking,
            ):
                event_type = event.get("type", "")
                data = event.get("data", {})

                if event_type == "content":
                    yield ChunkEvent(
                        offset=0,
                        session_id=session_id,
                        text=data.get("text", ""),
                        is_delta=True,
                    )
                elif event_type == "tool_call":
                    yield ToolStartEvent(
                        offset=0,
                        session_id=session_id,
                        tool_name=data.get("tool", ""),
                        tool_input=data.get("input", {}),
                        tool_call_id=data.get("tool_call_id", ""),
                    )
                elif event_type == "tool_result":
                    yield ToolResultEvent(
                        offset=0,
                        session_id=session_id,
                        tool_name=data.get("tool", ""),
                        tool_call_id=data.get("tool_call_id", ""),
                        result=data.get("result"),
                    )
                elif event_type == "thinking":
                    yield ThinkingEvent(
                        offset=0,
                        session_id=session_id,
                        text=data.get("text", ""),
                    )
                elif event_type == "error":
                    yield ErrorEvent(
                        offset=0,
                        session_id=session_id,
                        error_code="AGENT_ERROR",
                        message=data.get("message", "Unknown error"),
                    )

        except asyncio.CancelledError:
            raise
        except Exception as e:
            yield ErrorEvent(
                offset=0,
                session_id=session_id,
                error_code="STREAM_ERROR",
                message=str(e),
            )

    # Start the stream
    await streaming_core.start_stream(subtask_id, agent_event_generator)

    # Connect client
    client = await streaming_core.connect_client(
        stream_id=subtask_id,
        client_id=client_id,
        resume_from_offset=resume_from_offset,
    )

    return client.client_id, streaming_core.get_event_generator(client.client_id)


async def recover_sse_stream(
    stream_id: str,
    offset: int,
    client_id: Optional[str] = None,
) -> tuple[str, AsyncGenerator[str, None]]:
    """
    Recover an existing SSE stream from a specific offset.

    Args:
        stream_id: The stream to recover
        offset: Offset to resume from
        client_id: Optional client ID (generated if not provided)

    Returns:
        Tuple of (client_id, event_generator)

    Raises:
        StreamNotFoundError: If stream not found
        ValueError: If recovery is not possible from the given offset
    """
    streaming_core = get_streaming_core()

    # Check recovery possibility
    recovery_info = await streaming_core.get_recovery_info(stream_id, offset)

    if not recovery_info["can_recover"]:
        raise ValueError(
            f"Cannot recover stream {stream_id} from offset {offset}. "
            f"Buffer coverage: {recovery_info['buffer_coverage']}"
        )

    # Connect client with recovery
    client = await streaming_core.connect_client(
        stream_id=stream_id,
        client_id=client_id,
        resume_from_offset=offset,
    )

    return client.client_id, streaming_core.get_event_generator(client.client_id)


async def cancel_sse_stream(stream_id: str, reason: Optional[str] = None):
    """
    Cancel a running SSE stream.

    Args:
        stream_id: The stream to cancel
        reason: Optional reason for cancellation
    """
    streaming_core = get_streaming_core()
    await streaming_core.cancel_stream(stream_id, reason)


async def get_stream_status(stream_id: str) -> Dict[str, Any]:
    """
    Get detailed status for a stream.

    Args:
        stream_id: The stream to check

    Returns:
        Dict with stream status information
    """
    streaming_core = get_streaming_core()
    return await streaming_core.get_stream_status(stream_id)
