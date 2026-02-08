"""FastAPI dependencies for authentication and authorization.

Epic 11: Authentication & Authorization
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import decode_access_token
from backend.database.engine import get_db_session
from backend.models.user import User, UserRole
from backend.schemas.auth import CurrentUser
from backend.services.auth_service import AuthService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Optional[CurrentUser]:
    """Get the current authenticated user (optional).

    This dependency allows anonymous access - it returns None if no valid token.

    Args:
        token: The JWT token from the Authorization header.
        session: The database session.

    Returns:
        The current user if authenticated, None otherwise.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        return None

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)

    if not user or not user.is_active:
        return None

    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        default_namespace=user.default_namespace,
    )


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    """Get the current authenticated user (required).

    This dependency requires authentication - raises 401 if no valid token.

    Args:
        token: The JWT token from the Authorization header.
        session: The database session.

    Returns:
        The current authenticated user.

    Raises:
        HTTPException: 401 if authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise credentials_exception

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)

    if not user or not user.is_active:
        raise credentials_exception

    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        default_namespace=user.default_namespace,
    )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Get the current active user.

    Args:
        current_user: The current authenticated user.

    Returns:
        The current active user.

    Raises:
        HTTPException: 403 if user is inactive.
    """
    # This is a placeholder for future inactive user checks
    # The get_current_user already checks is_active, but this provides
    # a separate dependency point for additional checks
    return current_user


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Require admin role for the current user.

    Args:
        current_user: The current authenticated user.

    Returns:
        The current user with admin role.

    Raises:
        HTTPException: 403 if user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_user_namespace(
    current_user: CurrentUser = Depends(get_current_user),
) -> str:
    """Get the default namespace for the current user.

    Args:
        current_user: The current authenticated user.

    Returns:
        The user's default namespace.
    """
    return current_user.default_namespace
