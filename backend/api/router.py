"""Main API router that combines all endpoint routers."""

from fastapi import APIRouter

from backend.api.v1 import auth, chat, chat_ws, kinds, messages, sessions, tasks, user_ws

api_router = APIRouter()

# Include v1 routes
api_router.include_router(kinds.router, prefix="/v1", tags=["kinds"])
api_router.include_router(tasks.router, prefix="/v1", tags=["tasks"])
api_router.include_router(chat.router, prefix="/v1", tags=["chat"])
api_router.include_router(auth.router, prefix="/v1", tags=["auth"])

# Include message routes
api_router.include_router(messages.router, prefix="/v1", tags=["messages"])

# Include session routes
api_router.include_router(sessions.router, prefix="/v1", tags=["sessions"])

# Include WebSocket routes (these are handled separately by FastAPI)
api_router.include_router(chat_ws.router, prefix="/v1")
api_router.include_router(user_ws.router, prefix="/v1")
