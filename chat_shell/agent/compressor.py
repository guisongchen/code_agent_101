"""
Message compressor for context management.

This module provides automatic context compression when approaching token limits,
with support for multiple compression strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

if TYPE_CHECKING:
    from .agent import AgentState


class CompressionStrategy(Enum):
    """Available compression strategies."""
    SUMMARIZE = "summarize"
    """Summarize older messages into a condensed form."""

    TRUNCATE = "truncate"
    """Truncate history, keeping only recent messages."""

    WINDOW = "window"
    """Smart windowing: keep N recent messages, summarize older ones."""


@dataclass
class CompressionResult:
    """Result of compression operation."""
    messages: List[BaseMessage]
    """The compressed message list."""

    original_token_count: int
    """Token count before compression."""

    compressed_token_count: int
    """Token count after compression."""

    compression_ratio: float
    """Ratio of compressed to original (e.g., 0.5 means 50% reduction)."""

    strategy_used: CompressionStrategy
    """The compression strategy that was applied."""


class TokenCounter:
    """Token counter for different models."""

    # Tokenizer mappings for different model families
    TOKENIZER_MAP = {
        "gpt-4": "cl100k_base",
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "deepseek": "cl100k_base",  # DeepSeek uses cl100k_base
        "claude": "cl100k_base",  # Approximation - Anthropic uses different tokenizer
    }

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self._encoder = None

        if TIKTOKEN_AVAILABLE:
            # Find the best matching tokenizer
            tokenizer_name = self._get_tokenizer_name(model)
            try:
                self._encoder = tiktoken.get_encoding(tokenizer_name)
            except Exception:
                # Fallback to cl100k_base
                self._encoder = tiktoken.get_encoding("cl100k_base")

    def _get_tokenizer_name(self, model: str) -> str:
        """Get the appropriate tokenizer name for a model."""
        model_lower = model.lower()

        for prefix, tokenizer in self.TOKENIZER_MAP.items():
            if prefix in model_lower:
                return tokenizer

        return "cl100k_base"  # Default fallback

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        if self._encoder:
            return len(self._encoder.encode(text))
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4

    def count_message_tokens(self, message: BaseMessage) -> int:
        """Count tokens in a single message."""
        # Every message follows <|im_start|>{role}\n{content}<|im_end|>\n
        content = ""
        if hasattr(message, "content") and message.content:
            content = str(message.content)

        # Add tokens for message format (approximation)
        format_tokens = 4  # <|im_start|>, role, \n, <|im_end|>\n
        return format_tokens + self.count_tokens(content)

    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """Count total tokens in a list of messages."""
        total = 0
        for msg in messages:
            total += self.count_message_tokens(msg)
        # Add tokens for priming (assistant start)
        total += 2
        return total


class BaseCompressor(ABC):
    """Abstract base class for compression strategies."""

    @abstractmethod
    def compress(
        self,
        messages: List[BaseMessage],
        target_tokens: int,
        keep_recent: int = 4,
    ) -> CompressionResult:
        """Compress messages to fit within target token count.

        Args:
            messages: The list of messages to compress.
            target_tokens: The target maximum token count.
            keep_recent: Number of most recent messages to preserve.

        Returns:
            CompressionResult with compressed messages and metadata.
        """
        pass


class SummarizeCompressor(BaseCompressor):
    """Compressor that summarizes older messages."""

    def __init__(self, token_counter: TokenCounter):
        self.token_counter = token_counter

    def compress(
        self,
        messages: List[BaseMessage],
        target_tokens: int,
        keep_recent: int = 4,
    ) -> CompressionResult:
        """Summarize older messages while keeping recent ones intact."""
        original_count = self.token_counter.count_messages_tokens(messages)

        if original_count <= target_tokens:
            return CompressionResult(
                messages=messages,
                original_token_count=original_count,
                compressed_token_count=original_count,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.SUMMARIZE,
            )

        # Split into older and recent messages
        if keep_recent >= len(messages):
            return CompressionResult(
                messages=messages,
                original_token_count=original_count,
                compressed_token_count=original_count,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.SUMMARIZE,
            )

        older_messages = messages[:-keep_recent]
        recent_messages = messages[-keep_recent:]

        # Create a summary of older messages
        summary = self._create_summary(older_messages)
        summary_message = SystemMessage(content=f"Previous conversation summary: {summary}")

        # Combine summary with recent messages
        compressed = [summary_message] + recent_messages
        compressed_count = self.token_counter.count_messages_tokens(compressed)

        return CompressionResult(
            messages=compressed,
            original_token_count=original_count,
            compressed_token_count=compressed_count,
            compression_ratio=compressed_count / original_count if original_count > 0 else 1.0,
            strategy_used=CompressionStrategy.SUMMARIZE,
        )

    def _create_summary(self, messages: List[BaseMessage]) -> str:
        """Create a summary of the given messages."""
        # Extract key information from conversation pairs
        summary_parts = []
        user_assistant_pairs = []
        current_pair = {}

        for msg in messages:
            if isinstance(msg, HumanMessage):
                if current_pair:
                    user_assistant_pairs.append(current_pair)
                current_pair = {"user": str(msg.content)[:100], "assistant": None}
            elif isinstance(msg, AIMessage) and current_pair:
                current_pair["assistant"] = str(msg.content)[:100]

        if current_pair:
            user_assistant_pairs.append(current_pair)

        # Create condensed summary
        for i, pair in enumerate(user_assistant_pairs[-3:], 1):  # Keep last 3 exchanges
            user_text = pair.get("user", "")
            if user_text:
                summary_parts.append(f"Q{i}: {user_text}...")

        if not summary_parts:
            return "Earlier conversation context available."

        return " | ".join(summary_parts)


class TruncateCompressor(BaseCompressor):
    """Compressor that truncates older messages."""

    def __init__(self, token_counter: TokenCounter):
        self.token_counter = token_counter

    def compress(
        self,
        messages: List[BaseMessage],
        target_tokens: int,
        keep_recent: int = 4,
    ) -> CompressionResult:
        """Truncate messages, keeping only the most recent ones."""
        original_count = self.token_counter.count_messages_tokens(messages)

        if original_count <= target_tokens:
            return CompressionResult(
                messages=messages,
                original_token_count=original_count,
                compressed_token_count=original_count,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.TRUNCATE,
            )

        # Always keep system message if present
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        non_system = [m for m in messages if not isinstance(m, SystemMessage)]

        # Keep recent messages
        keep_count = min(keep_recent, len(non_system))
        kept_messages = non_system[-keep_count:]

        compressed = system_messages + kept_messages
        compressed_count = self.token_counter.count_messages_tokens(compressed)

        return CompressionResult(
            messages=compressed,
            original_token_count=original_count,
            compressed_token_count=compressed_count,
            compression_ratio=compressed_count / original_count if original_count > 0 else 1.0,
            strategy_used=CompressionStrategy.TRUNCATE,
        )


class WindowCompressor(BaseCompressor):
    """Compressor using smart windowing: summarize middle, keep ends."""

    def __init__(self, token_counter: TokenCounter):
        self.token_counter = token_counter
        self.summarize_compressor = SummarizeCompressor(token_counter)
        self.truncate_compressor = TruncateCompressor(token_counter)

    def compress(
        self,
        messages: List[BaseMessage],
        target_tokens: int,
        keep_recent: int = 4,
    ) -> CompressionResult:
        """Apply windowing: keep system, summarize middle, keep recent."""
        original_count = self.token_counter.count_messages_tokens(messages)

        if original_count <= target_tokens:
            return CompressionResult(
                messages=messages,
                original_token_count=original_count,
                compressed_token_count=original_count,
                compression_ratio=1.0,
                strategy_used=CompressionStrategy.WINDOW,
            )

        # Split messages
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        non_system = [m for m in messages if not isinstance(m, SystemMessage)]

        if len(non_system) <= keep_recent:
            # Not enough messages to window, use truncate
            return self.truncate_compressor.compress(messages, target_tokens, keep_recent)

        # Split into older and recent
        older = non_system[:-keep_recent]
        recent = non_system[-keep_recent:]

        # Summarize older messages
        summary_result = self.summarize_compressor.compress(
            older, target_tokens // 2, keep_recent=0
        )

        # Combine: system + summary of older + recent
        compressed = system_messages + summary_result.messages + recent
        compressed_count = self.token_counter.count_messages_tokens(compressed)

        return CompressionResult(
            messages=compressed,
            original_token_count=original_count,
            compressed_token_count=compressed_count,
            compression_ratio=compressed_count / original_count if original_count > 0 else 1.0,
            strategy_used=CompressionStrategy.WINDOW,
        )


class MessageCompressor:
    """Main compressor class that manages context compression.

    Automatically compresses conversation history when approaching token limits
    using configurable compression strategies.

    Example:
        compressor = MessageCompressor(model="gpt-4", max_tokens=8000)
        result = compressor.compress_if_needed(messages)
        if result.compression_ratio < 1.0:
            print(f"Compressed by {(1 - result.compression_ratio) * 100:.1f}%")
    """

    def __init__(
        self,
        model: str = "gpt-4",
        max_tokens: int = 8000,
        compression_threshold: float = 0.8,
        keep_recent_messages: int = 4,
        strategy: CompressionStrategy = CompressionStrategy.WINDOW,
    ):
        """Initialize the message compressor.

        Args:
            model: The model name for token counting.
            max_tokens: Maximum tokens allowed before compression.
            compression_threshold: Fraction of max_tokens that triggers compression.
            keep_recent_messages: Number of recent messages to always preserve.
            strategy: Compression strategy to use.
        """
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold
        self.keep_recent_messages = keep_recent_messages
        self.strategy = strategy

        self.token_counter = TokenCounter(model)
        self._init_compressor()

    def _init_compressor(self):
        """Initialize the appropriate compressor based on strategy."""
        compressors = {
            CompressionStrategy.SUMMARIZE: SummarizeCompressor,
            CompressionStrategy.TRUNCATE: TruncateCompressor,
            CompressionStrategy.WINDOW: WindowCompressor,
        }
        compressor_class = compressors.get(self.strategy, WindowCompressor)
        self._compressor = compressor_class(self.token_counter)

    def should_compress(self, messages: List[BaseMessage]) -> bool:
        """Check if messages should be compressed.

        Args:
            messages: The list of messages to check.

        Returns:
            True if compression is needed, False otherwise.
        """
        token_count = self.token_counter.count_messages_tokens(messages)
        threshold = int(self.max_tokens * self.compression_threshold)
        return token_count > threshold

    def compress_if_needed(
        self,
        messages: List[BaseMessage],
        state: Optional["AgentState"] = None,
    ) -> CompressionResult:
        """Compress messages only if they exceed the threshold.

        Args:
            messages: The list of messages to potentially compress.
            state: Optional agent state for context-aware compression.

        Returns:
            CompressionResult with (possibly) compressed messages.
        """
        token_count = self.token_counter.count_messages_tokens(messages)
        threshold = int(self.max_tokens * self.compression_threshold)

        if token_count <= threshold:
            return CompressionResult(
                messages=list(messages),
                original_token_count=token_count,
                compressed_token_count=token_count,
                compression_ratio=1.0,
                strategy_used=self.strategy,
            )

        target_tokens = int(self.max_tokens * 0.9)  # Target 90% of max
        return self._compressor.compress(
            messages, target_tokens, self.keep_recent_messages
        )

    def force_compress(
        self,
        messages: List[BaseMessage],
        target_tokens: Optional[int] = None,
    ) -> CompressionResult:
        """Force compression regardless of threshold.

        Args:
            messages: The list of messages to compress.
            target_tokens: Optional target token count (defaults to max_tokens * 0.9).

        Returns:
            CompressionResult with compressed messages.
        """
        if target_tokens is None:
            target_tokens = int(self.max_tokens * 0.9)

        return self._compressor.compress(
            messages, target_tokens, self.keep_recent_messages
        )

    def get_token_count(self, messages: List[BaseMessage]) -> int:
        """Get the current token count for messages.

        Args:
            messages: The list of messages to count.

        Returns:
            Total token count.
        """
        return self.token_counter.count_messages_tokens(messages)
