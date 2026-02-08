"""WebSocket authentication utilities.

Provides authentication for WebSocket connections using JWT tokens.

Epic 14: WebSocket Chat Endpoint
"""

from typing import Optional

from fastapi import WebSocket

from backend.schemas import CurrentUser
from backend.services.auth_service import AuthService
from backend.api.dependencies import decode_access_token
from backend.database.engine import AsyncSessionLocal


async def authenticate_ws_token(token: Optional[str]) -> Optional[CurrentUser]:
    """Authenticate a WebSocket connection using a JWT token.

    Args:
        token: The JWT token from query parameter or header.

    Returns:
        CurrentUser if authentication succeeds, None otherwise.
    """
    if not token:
        return None

    # Decode token
    payload = decode_access_token(token)
    if not payload:
        return None

    # Get user ID from token
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        return None

    # Look up user in database
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        user = await auth_service.get_user_by_id(int(user_id))

        if not user or not user.is_active:
            return None

        return CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            default_namespace=user.default_namespace or "default",
        )


async def authenticate_websocket(
    websocket: WebSocket,
    token: Optional[str] = None,
) -> Optional[CurrentUser]:
    """Authenticate a WebSocket connection.

    Attempts to authenticate using token from query param or headers.

    Args:
        websocket: The WebSocket connection.
        token: Optional token passed directly.

    Returns:
        CurrentUser if authentication succeeds, None otherwise.
    """
    # If token not provided, try to get from query params
    if token is None:
        token = websocket.query_params.get("token")

    # If still no token, try to get from headers
    if token is None:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    return await authenticate_ws_token(token)
