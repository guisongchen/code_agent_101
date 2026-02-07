"""
FastAPI dependencies.
"""

from typing import Dict

from ..agent.agent import ChatAgent


def get_agent() -> ChatAgent:
    """Get initialized agent from app state."""
    from .app import app_state

    if app_state.get("agent") is None:
        raise RuntimeError("Agent not initialized")
    return app_state["agent"]


def get_session_manager() -> Dict:
    """Get session manager."""
    from .app import app_state

    return app_state.get("active_sessions", {})
