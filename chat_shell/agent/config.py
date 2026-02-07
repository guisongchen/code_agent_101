"""
Agent configuration for Chat Shell 101.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AgentConfig:
    """Configuration for the chat agent.

    This class provides flexible agent configuration separate from global config.
    It allows fine-grained control over agent behavior including model settings,
    tool execution limits, context management, and checkpointing.
    """

    # Model settings
    provider: Optional[str] = None
    """LLM provider (openai, anthropic, google). Auto-detected if not specified."""

    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096

    # Fallback configuration
    fallback_models: List[str] = field(default_factory=list)
    """List of fallback model names to try if primary fails."""

    enable_fallback: bool = False
    """Enable automatic fallback to backup models on failures."""

    # Tool execution settings
    max_iterations: int = 10
    """Maximum number of tool execution cycles to prevent infinite loops."""

    # System prompt
    system_prompt: str = "You are a helpful AI assistant."

    # Tool selection
    tools: List[str] = field(default_factory=list)
    """List of tool names to bind to the agent. Empty list means all available tools."""

    # Checkpointing settings
    checkpoint_enabled: bool = True
    """Enable state checkpointing for session recovery."""

    checkpoint_type: str = "memory"
    """Type of checkpoint storage: 'memory' or 'sqlite'."""

    checkpoint_path: Optional[str] = None
    """Path for sqlite checkpoint database (required if checkpoint_type='sqlite')."""

    # Context management settings
    compress_context: bool = True
    """Enable automatic context compression when approaching token limits."""

    max_context_tokens: int = 8000
    """Maximum tokens allowed in context before compression triggers."""

    compression_threshold: float = 0.8
    """Fraction of max_context_tokens that triggers compression (0.0-1.0)."""

    keep_recent_messages: int = 4
    """Number of most recent messages to always keep uncompressed."""

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if self.max_context_tokens < 1:
            raise ValueError("max_context_tokens must be at least 1")
        if self.compression_threshold <= 0 or self.compression_threshold > 1:
            raise ValueError("compression_threshold must be between 0 and 1")
        if self.keep_recent_messages < 0:
            raise ValueError("keep_recent_messages must be non-negative")
        if self.checkpoint_type not in ("memory", "sqlite"):
            raise ValueError("checkpoint_type must be 'memory' or 'sqlite'")
        if self.checkpoint_type == "sqlite" and not self.checkpoint_path:
            raise ValueError("checkpoint_path is required when checkpoint_type='sqlite'")
