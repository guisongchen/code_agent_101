"""RESTful API endpoints for Chat execution.

Implements chat endpoints that integrate chat_shell module with Backend API.

Epic 13: Chat Shell Integration
"""

from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db_session
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    ChatValidationResponse,
)
from backend.services import ChatService

router = APIRouter()


# =============================================================================
# Chat Endpoints
# =============================================================================


@router.post(
    "/chat/{bot_name}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute chat with a Bot",
    description="Execute a chat session with the specified Bot. Returns the complete response (non-streaming).",
)
async def chat_with_bot(
    bot_name: str,
    request: ChatRequest,
    namespace: Optional[str] = Query(default="default", description="Namespace for the Bot"),
    session: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    """Execute chat with a Bot and return complete response.

    Args:
        bot_name: Name of the Bot resource to use.
        request: Chat request with messages and options.
        namespace: Namespace for the Bot resource.
        session: Database session.

    Returns:
        Complete chat response with content and metadata.

    Raises:
        HTTPException: 404 if Bot not found.
        HTTPException: 400 if bot configuration is invalid.
        HTTPException: 500 if chat execution fails.
    """
    chat_service = ChatService(session)

    try:
        result = await chat_service.execute_chat_sync(
            bot_name=bot_name,
            messages=[msg.model_dump() for msg in request.messages],
            namespace=namespace,
            thread_id=request.thread_id,
        )

        return ChatResponse(
            content=result["content"],
            tool_calls=result.get("tool_calls"),
            thinking=result.get("thinking"),
            error=result.get("error"),
            bot_name=bot_name,
            namespace=namespace,
            thread_id=request.thread_id,
        )

    except chat_service.BotConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bot configuration error: {str(e)}",
        )
    except chat_service.ChatServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/chat/{bot_name}/stream",
    summary="Execute streaming chat with a Bot",
    description="Execute a chat session with the specified Bot. Streams response events (SSE format).",
)
async def chat_with_bot_stream(
    bot_name: str,
    request: ChatRequest,
    namespace: Optional[str] = Query(default="default", description="Namespace for the Bot"),
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Execute chat with a Bot and stream response events.

    Args:
        bot_name: Name of the Bot resource to use.
        request: Chat request with messages and options.
        namespace: Namespace for the Bot resource.
        session: Database session.

    Returns:
        StreamingResponse with Server-Sent Events (SSE).

    Raises:
        HTTPException: 404 if Bot not found.
        HTTPException: 400 if bot configuration is invalid.
    """
    chat_service = ChatService(session)

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from chat stream."""
        try:
            async for event in chat_service.execute_chat(
                bot_name=bot_name,
                messages=[msg.model_dump() for msg in request.messages],
                namespace=namespace,
                thread_id=request.thread_id,
                show_thinking=request.show_thinking,
            ):
                # Format as SSE
                event_type = event.get("type", "unknown")
                event_data = event.get("data", {})

                # Build SSE formatted event
                sse_event = f"event: {event_type}\n"
                sse_event += f"data: {event_data}\n\n"
                yield sse_event

            # Send completion event
            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            # Send error event
            yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n"

    try:
        # Validate bot configuration first
        validation = await chat_service.validate_bot_configuration(bot_name, namespace)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bot configuration invalid: {', '.join(validation['errors'])}",
            )

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start chat stream: {str(e)}",
        )


@router.post(
    "/chat/{bot_name}/validate",
    response_model=ChatValidationResponse,
    summary="Validate Bot chat configuration",
    description="Validate that a Bot has valid configuration and all references exist for chat execution.",
)
async def validate_bot_chat_config(
    bot_name: str,
    namespace: Optional[str] = Query(default="default", description="Namespace for the Bot"),
    session: AsyncSession = Depends(get_db_session),
) -> ChatValidationResponse:
    """Validate Bot configuration for chat execution.

    Args:
        bot_name: Name of the Bot resource to validate.
        namespace: Namespace for the Bot resource.
        session: Database session.

    Returns:
        Validation results with errors and warnings.

    Raises:
        HTTPException: 404 if Bot not found.
    """
    chat_service = ChatService(session)

    try:
        result = await chat_service.validate_bot_configuration(bot_name, namespace)
        return ChatValidationResponse(
            valid=result["valid"],
            bot_name=result["bot_name"],
            namespace=result["namespace"],
            errors=result["errors"],
            warnings=result["warnings"],
            ghost=result.get("ghost"),
            model=result.get("model"),
            shell=result.get("shell"),
        )

    except chat_service.BotConfigurationError as e:
        # Bot not found or other config error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        return ChatValidationResponse(
            valid=False,
            bot_name=bot_name,
            namespace=namespace,
            errors=[str(e)],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )
