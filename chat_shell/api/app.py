"""
FastAPI application for HTTP mode.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..config import config
from ..agent.agent import ChatAgent
from ..agent.config import AgentConfig
from .routes import router


# Global state
app_state: Dict = {
    "agent": None,
    "start_time": None,
    "active_sessions": {},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    app_state["start_time"] = time.time()

    # Initialize agent
    agent_config = AgentConfig(
        model=config.openai.model,
        temperature=config.openai.temperature,
    )
    app_state["agent"] = ChatAgent(agent_config)
    await app_state["agent"].initialize()

    yield

    # Shutdown
    app_state["agent"] = None


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Chat Shell 101 API",
        description="HTTP API for Chat Shell 101 AI agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include routes
    app.include_router(router, prefix="/v1")

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": str(exc),
            },
        )

    return app


app = create_app()
