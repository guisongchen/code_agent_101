"""API endpoints for message history management.

Provides REST endpoints for retrieving chat message history.

Epic 15: Message History Management
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db_session
from backend.schemas import (
    CurrentUser,
    MessageHistoryRequest,
    MessageHistoryResponse,
    MessageResponse,
)
from backend.services import MessageService, TaskService
from backend.api.dependencies import get_current_user

router = APIRouter()


@router.get(
    "/tasks/{task_id}/messages",
    response_model=MessageHistoryResponse,
    summary="Get message history for a task",
    description="Retrieve paginated message history for a specific task.",
)
async def get_task_messages(
    task_id: UUID,
    thread_id: Optional[str] = Query(None, description="Filter by thread ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    before_sequence: Optional[int] = Query(None, description="Get messages before sequence"),
    after_sequence: Optional[int] = Query(None, description="Get messages after sequence"),
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> MessageHistoryResponse:
    """Get message history for a task.

    Args:
        task_id: Task UUID.
        thread_id: Optional thread ID filter.
        limit: Maximum number of messages to return.
        offset: Number of messages to skip.
        before_sequence: Get messages before this sequence number.
        after_sequence: Get messages after this sequence number.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        MessageHistoryResponse with messages and pagination info.

    Raises:
        HTTPException: If task not found.
    """
    # Verify task exists
    task_service = TaskService(session)
    task = await task_service.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    # Build history request
    request = MessageHistoryRequest(
        thread_id=thread_id,
        limit=limit,
        offset=offset,
        before_sequence=before_sequence,
        after_sequence=after_sequence,
    )

    # Get message history
    message_service = MessageService(session)
    return await message_service.get_history(task_id, request)


@router.get(
    "/tasks/{task_id}/messages/{message_id}",
    response_model=MessageResponse,
    summary="Get a specific message",
    description="Retrieve a single message by ID.",
)
async def get_message(
    task_id: UUID,
    message_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> MessageResponse:
    """Get a specific message.

    Args:
        task_id: Task UUID.
        message_id: Message UUID.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        MessageResponse with message details.

    Raises:
        HTTPException: If task or message not found.
    """
    # Verify task exists
    task_service = TaskService(session)
    task = await task_service.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    # Get message
    message_service = MessageService(session)
    message = await message_service.get(message_id)

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}",
        )

    # Verify message belongs to task
    if message.task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found in task: {message_id}",
        )

    return message


@router.get(
    "/tasks/{task_id}/threads/{thread_id}/messages",
    response_model=MessageHistoryResponse,
    summary="Get messages for a specific thread",
    description="Retrieve all messages for a specific thread within a task.",
)
async def get_thread_messages(
    task_id: UUID,
    thread_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> MessageHistoryResponse:
    """Get messages for a specific thread.

    Args:
        task_id: Task UUID.
        thread_id: Thread ID.
        limit: Maximum number of messages to return.
        offset: Number of messages to skip.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        MessageHistoryResponse with messages and pagination info.

    Raises:
        HTTPException: If task not found.
    """
    # Verify task exists
    task_service = TaskService(session)
    task = await task_service.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    # Build history request
    request = MessageHistoryRequest(
        thread_id=thread_id,
        limit=limit,
        offset=offset,
    )

    # Get message history
    message_service = MessageService(session)
    return await message_service.get_history(task_id, request)


@router.delete(
    "/tasks/{task_id}/messages",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all messages for a task",
    description="Delete all message history for a task. Requires admin privileges.",
)
async def delete_task_messages(
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete all messages for a task.

    Args:
        task_id: Task UUID.
        session: Database session.
        current_user: Authenticated user.

    Raises:
        HTTPException: If task not found or user not authorized.
    """
    # Verify task exists
    task_service = TaskService(session)
    task = await task_service.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    # Delete messages
    message_service = MessageService(session)
    await message_service.delete_task_messages(task_id)
    await session.commit()
