"""
HTTP API mode for Chat Shell 101.

This module provides a FastAPI-based HTTP server for chat interactions.

Example:
    # Start server programmatically
    from chat_shell_101.api import app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Or use the CLI:
    # chat-shell serve --port 8000

API Endpoints:
    POST /v1/response        - Start a new chat session
    GET /v1/response/{id}    - Get session status
    DELETE /v1/response/{id} - Cancel a session
    GET /v1/health           - Health check
"""

from .app import create_app, app
from .schemas import (
    ChatRequest,
    ChatResponse,
    ChatEvent,
    ChatMessage,
    SessionStatus,
    SessionHistory,
    HealthResponse,
    ErrorResponse,
)

__all__ = [
    "create_app",
    "app",
    "ChatRequest",
    "ChatResponse",
    "ChatEvent",
    "ChatMessage",
    "SessionStatus",
    "SessionHistory",
    "HealthResponse",
    "ErrorResponse",
]
