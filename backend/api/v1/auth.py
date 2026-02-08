"""Authentication API endpoints.

Epic 11: Authentication & Authorization
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, require_admin
from backend.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_token_expiry_seconds,
)
from backend.database.engine import get_db_session
from backend.schemas.auth import (
    CurrentUser,
    LoginRequest,
    RegisterRequest,
    Token,
    UserResponse,
)
from backend.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password.",
)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Register a new user account.

    Args:
        request: The user registration request.
        session: The database session.

    Returns:
        The created user response.

    Raises:
        HTTPException: 409 if username or email already exists.
    """
    auth_service = AuthService(session)

    try:
        user = await auth_service.create_user(request)
        return auth_service.to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/auth/login",
    response_model=Token,
    summary="Login and get access token",
    description="Authenticate with username and password to receive a JWT access token.",
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> Token:
    """Authenticate and get JWT access token.

    Args:
        request: The login request with username and password.
        session: The database session.

    Returns:
        The JWT token response.

    Raises:
        HTTPException: 401 if authentication fails.
    """
    auth_service = AuthService(session)

    user = await auth_service.authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user info
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
        },
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds(),
    )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current user info",
    description="Get information about the currently authenticated user.",
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Get current authenticated user information.

    Args:
        current_user: The current authenticated user from token.
        session: The database session.

    Returns:
        The current user response.
    """
    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(str(current_user.id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return auth_service.to_response(user)


@router.post(
    "/auth/admin/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new admin user (admin only)",
    description="Create a new admin user account. Requires admin privileges.",
)
async def register_admin(
    request: RegisterRequest,
    admin_user: CurrentUser = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Register a new admin user (requires admin privileges).

    Args:
        request: The user registration request.
        admin_user: The current admin user (verified by dependency).
        session: The database session.

    Returns:
        The created admin user response.

    Raises:
        HTTPException: 409 if username or email already exists.
    """
    auth_service = AuthService(session)

    try:
        user = await auth_service.create_admin_user(request)
        return auth_service.to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
