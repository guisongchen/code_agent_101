"""
LangGraph Agent Builder for creating configured agents.
"""

from typing import List, Optional, TYPE_CHECKING

from langgraph.checkpoint.memory import MemorySaver

from .agent import ChatAgent
from .config import AgentConfig

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver

# Optional SQLite support
try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    AsyncSqliteSaver = None


class LangGraphAgentBuilder:
    """Builder pattern for creating configured LangGraph agents.

    This builder provides a clean, fluent API for configuring and creating
    ChatAgent instances with various settings including model configuration,
    tool selection, checkpointing, and context management.

    Example:
        builder = LangGraphAgentBuilder()
        agent = (builder
            .with_model("gpt-4")
            .with_temperature(0.5)
            .with_tools(["calculator"])
            .with_system_prompt("You are a math expert.")
            .with_memory_checkpoint()
            .build())

        await agent.initialize()
    """

    def __init__(self):
        self._config = AgentConfig()
        self._checkpointer: Optional["BaseCheckpointSaver"] = None

    def with_model(self, model: str) -> "LangGraphAgentBuilder":
        """Set the model to use.

        Args:
            model: The model identifier (e.g., "gpt-4", "deepseek-chat").

        Returns:
            Self for method chaining.
        """
        self._config.model = model
        return self

    def with_temperature(self, temperature: float) -> "LangGraphAgentBuilder":
        """Set the temperature for generation.

        Args:
            temperature: Sampling temperature (0.0 to 2.0).

        Returns:
            Self for method chaining.
        """
        self._config.temperature = temperature
        return self

    def with_max_tokens(self, max_tokens: int) -> "LangGraphAgentBuilder":
        """Set the maximum tokens to generate.

        Args:
            max_tokens: Maximum number of tokens in the response.

        Returns:
            Self for method chaining.
        """
        self._config.max_tokens = max_tokens
        return self

    def with_max_iterations(self, max_iterations: int) -> "LangGraphAgentBuilder":
        """Set the maximum tool execution iterations.

        Args:
            max_iterations: Maximum number of tool execution cycles.

        Returns:
            Self for method chaining.
        """
        self._config.max_iterations = max_iterations
        return self

    def with_tools(self, tools: List[str]) -> "LangGraphAgentBuilder":
        """Set the tools to bind to the agent.

        Args:
            tools: List of tool names to enable. Empty list enables all tools.

        Returns:
            Self for method chaining.
        """
        self._config.tools = tools
        return self

    def with_system_prompt(self, prompt: str) -> "LangGraphAgentBuilder":
        """Set the system prompt.

        Args:
            prompt: The system prompt to use.

        Returns:
            Self for method chaining.
        """
        self._config.system_prompt = prompt
        return self

    def with_memory_checkpoint(self) -> "LangGraphAgentBuilder":
        """Enable in-memory checkpointing for session recovery.

        Returns:
            Self for method chaining.
        """
        self._config.checkpoint_enabled = True
        self._config.checkpoint_type = "memory"
        self._checkpointer = MemorySaver()
        return self

    def with_sqlite_checkpoint(self, db_path: str) -> "LangGraphAgentBuilder":
        """Enable SQLite checkpointing for persistent session recovery.

        Args:
            db_path: Path to the SQLite database file.

        Returns:
            Self for method chaining.

        Raises:
            ImportError: If sqlite checkpoint support is not available.
        """
        if not SQLITE_AVAILABLE:
            raise ImportError(
                "SQLite checkpoint support is not available. "
                "Install with: pip install langgraph[sqlite]"
            )
        self._config.checkpoint_enabled = True
        self._config.checkpoint_type = "sqlite"
        self._config.checkpoint_path = db_path
        self._checkpointer = AsyncSqliteSaver(db_path)
        return self

    def with_checkpointer(self, checkpointer: "BaseCheckpointSaver") -> "LangGraphAgentBuilder":
        """Set a custom checkpointer.

        Args:
            checkpointer: A LangGraph checkpointer instance.

        Returns:
            Self for method chaining.
        """
        self._checkpointer = checkpointer
        self._config.checkpoint_enabled = True
        return self

    def with_context_compression(
        self,
        enabled: bool = True,
        max_context_tokens: int = 8000,
        compression_threshold: float = 0.8,
        keep_recent_messages: int = 4,
    ) -> "LangGraphAgentBuilder":
        """Configure context compression settings.

        Args:
            enabled: Whether to enable context compression.
            max_context_tokens: Maximum tokens before compression triggers.
            compression_threshold: Fraction of max tokens that triggers compression.
            keep_recent_messages: Number of recent messages to keep uncompressed.

        Returns:
            Self for method chaining.
        """
        self._config.compress_context = enabled
        self._config.max_context_tokens = max_context_tokens
        self._config.compression_threshold = compression_threshold
        self._config.keep_recent_messages = keep_recent_messages
        return self

    def with_config(self, config: AgentConfig) -> "LangGraphAgentBuilder":
        """Use a pre-built AgentConfig.

        Args:
            config: An AgentConfig instance with all settings.

        Returns:
            Self for method chaining.
        """
        self._config = config
        # Reset checkpointer if config specifies one
        if config.checkpoint_enabled:
            if config.checkpoint_type == "memory":
                self._checkpointer = MemorySaver()
            elif config.checkpoint_type == "sqlite" and config.checkpoint_path:
                if not SQLITE_AVAILABLE:
                    raise ImportError(
                        "SQLite checkpoint support is not available. "
                        "Install with: pip install langgraph[sqlite]"
                    )
                self._checkpointer = AsyncSqliteSaver(config.checkpoint_path)
        return self

    def build(self) -> ChatAgent:
        """Build and return the configured ChatAgent.

        Returns:
            A configured ChatAgent instance. Call initialize() before use.

        Raises:
            ValueError: If configuration is invalid.
        """
        agent = ChatAgent(self._config)

        if self._checkpointer:
            agent.with_checkpointer(self._checkpointer)
        elif self._config.checkpoint_enabled:
            # Create default checkpointer based on config
            if self._config.checkpoint_type == "memory":
                agent.with_checkpointer(MemorySaver())
            elif self._config.checkpoint_type == "sqlite" and self._config.checkpoint_path:
                if not SQLITE_AVAILABLE:
                    raise ImportError(
                        "SQLite checkpoint support is not available. "
                        "Install with: pip install langgraph[sqlite]"
                    )
                agent.with_checkpointer(AsyncSqliteSaver(self._config.checkpoint_path))

        return agent
