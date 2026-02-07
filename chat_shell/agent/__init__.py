"""
Agent module for Chat Shell 101.

This module provides the ReAct agent implementation with LangGraph,
including configuration, building, context compression, and checkpointing.
"""

from .agent import ChatAgent, AgentState, ToolIterationLimitError
from .builder import LangGraphAgentBuilder
from .config import AgentConfig
from .compressor import (
    MessageCompressor,
    CompressionResult,
    CompressionStrategy,
    TokenCounter,
)

__all__ = [
    # Core agent
    "ChatAgent",
    "AgentState",
    "ToolIterationLimitError",
    # Builder
    "LangGraphAgentBuilder",
    # Configuration
    "AgentConfig",
    # Compression
    "MessageCompressor",
    "CompressionResult",
    "CompressionStrategy",
    "TokenCounter",
]
