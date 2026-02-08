"""Main API router that combines all endpoint routers."""

from fastapi import APIRouter

from backend.api.v1 import auth, kinds, tasks

api_router = APIRouter()

# Include v1 routes
api_router.include_router(kinds.router, prefix="/v1", tags=["kinds"])
api_router.include_router(tasks.router, prefix="/v1", tags=["tasks"])
api_router.include_router(auth.router, prefix="/v1", tags=["auth"])
