"""Main API router that combines all endpoint routers."""

from fastapi import APIRouter

from backend.api.v1 import kinds

api_router = APIRouter()

# Include v1 routes
api_router.include_router(kinds.router, prefix="/v1", tags=["kinds"])
