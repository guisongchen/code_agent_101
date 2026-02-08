"""API endpoints for chat session management.

Provides REST endpoints for session lifecycle management.

Epic 16: Chat Session State Management
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db_session
from backend.schemas import (
    CurrentUser,
    SessionCreateRequest,
    SessionListRequest,
    SessionListResponse,
    SessionMetrics,
    SessionRecoveryRequest,
    SessionRecoveryResponse,
    SessionResponse,
    SessionUpdateRequest,
)
from backend.services import SessionService
from backend.api.dependencies import get_current_user

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new chat session for a user.",
)
async def create_session(
    request: SessionCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    """Create a new chat session.

    Args:
        request: Session creation request.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        Created SessionResponse.

    Raises:
        HTTPException: If session limit reached or validation fails.
    """
    # Ensure user can only create sessions for themselves
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create session for another user",
        )

    service = SessionService(session)
    try:
        result = await service.create(request)
        await session.commit()
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List sessions",
    description="List sessions with optional filtering.",
)
async def list_sessions(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    active_only: bool = Query(False, description="Only active sessions"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Skip N results"),
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionListResponse:
    """List sessions.

    Args:
        user_id: Optional user filter.
        task_id: Optional task filter.
        status: Optional status filter.
        active_only: Only return active sessions.
        limit: Maximum results.
        offset: Skip N results.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        SessionListResponse with sessions.
    """
    # Users can only see their own sessions unless admin
    if user_id is None:
        user_id = current_user.id
    elif user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view sessions for another user",
        )

    from backend.models.session import SessionStatus

    request = SessionListRequest(
        user_id=user_id,
        task_id=task_id,
        status=SessionStatus(status) if status else None,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )

    service = SessionService(session)
    return await service.list_sessions(request)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
    description="Get details for a specific session.",
)
async def get_session(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    """Get a session by ID.

    Args:
        session_id: Session identifier.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        SessionResponse.

    Raises:
        HTTPException: If session not found or access denied.
    """
    service = SessionService(session)
    result = await service.get(session_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Users can only see their own sessions
    if result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return result


@router.post(
    "/sessions/recover",
    response_model=SessionRecoveryResponse,
    summary="Recover a session",
    description="Recover a previous session using a recovery token.",
)
async def recover_session(
    request: SessionRecoveryRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionRecoveryResponse:
    """Recover a previous session.

    Args:
        request: Recovery request with token.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        SessionRecoveryResponse with result.
    """
    service = SessionService(session)

    # Verify the session belongs to the current user
    old_session = await service.get_by_recovery_token(request.recovery_token)
    if old_session and old_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid recovery token",
        )

    result = await service.recover_session(request)
    await session.commit()

    return result


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Update session",
    description="Update session metadata or extend expiration.",
)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    """Update a session.

    Args:
        session_id: Session identifier.
        request: Update request.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        Updated SessionResponse.

    Raises:
        HTTPException: If session not found or access denied.
    """
    service = SessionService(session)

    # Check session exists and belongs to user
    existing = await service.get(session_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await service.update_session(session_id, request)
    await session.commit()

    return result


@router.post(
    "/sessions/{session_id}/heartbeat",
    response_model=SessionResponse,
    summary="Session heartbeat",
    description="Update session activity timestamp.",
)
async def session_heartbeat(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    """Update session activity (heartbeat).

    Args:
        session_id: Session identifier.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        Updated SessionResponse.

    Raises:
        HTTPException: If session not found or access denied.
    """
    service = SessionService(session)

    # Check session exists and belongs to user
    existing = await service.get(session_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await service.update_activity(session_id)
    await session.commit()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    return result


@router.post(
    "/sessions/{session_id}/close",
    response_model=SessionResponse,
    summary="Close session",
    description="Close a session and mark it as inactive.",
)
async def close_session(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionResponse:
    """Close a session.

    Args:
        session_id: Session identifier.
        session: Database session.
        current_user: Authenticated user.

    Returns:
        Closed SessionResponse.

    Raises:
        HTTPException: If session not found or access denied.
    """
    service = SessionService(session)

    # Check session exists and belongs to user
    existing = await service.get(session_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if existing.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    result = await service.close_session(session_id)
    await session.commit()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    return result


@router.get(
    "/sessions/metrics",
    response_model=SessionMetrics,
    summary="Get session metrics",
    description="Get aggregated session metrics for monitoring.",
)
async def get_session_metrics(
    session: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> SessionMetrics:
    """Get session metrics.

    Args:
        session: Database session.
        current_user: Authenticated user.

    Returns:
        SessionMetrics.
    """
    service = SessionService(session)
    return await service.get_metrics()
