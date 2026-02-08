"""FastAPI application for Backend CRD API.

Epic 10: RESTful API Endpoints
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import api_router
from backend.database.engine import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Wegent Backend API",
        description="Kubernetes-style RESTful API for managing CRD resources (Ghost, Model, Shell, Bot, Team, Skill)",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api")

    # Mount static files for UI
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/")
    async def root() -> dict:
        """Root endpoint with API info."""
        return {
            "name": "Wegent Backend API",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return app


# Create the application instance
app = create_app()
