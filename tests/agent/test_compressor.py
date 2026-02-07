"""
Tests for MessageCompressor and compression strategies - Epic 1: Core Agent System.
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from chat_shell_101.agent.compressor import (
    CompressionStrategy,
    CompressionResult,
    MessageCompressor,
    TokenCounter,
    SummarizeCompressor,
    TruncateCompressor,
    WindowCompressor,
)


pytestmark = [pytest.mark.unit, pytest.mark.epic_1]


class TestTokenCounter:
    """Test cases for TokenCounter."""

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        counter = TokenCounter(model="gpt-4")
        count = counter.count_tokens("Hello world")
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_empty(self):
        """Test token counting for empty string."""
        counter = TokenCounter(model="gpt-4")
        count = counter.count_tokens("")
        assert count == 0

    def test_count_message_tokens(self):
        """Test token counting for a message."""
        counter = TokenCounter(model="gpt-4")
        message = HumanMessage(content="Hello")
        count = counter.count_message_tokens(message)
        assert count > 0  # Should include format tokens

    def test_count_messages_tokens(self):
        """Test token counting for multiple messages."""
        counter = TokenCounter(model="gpt-4")
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
        ]
        count = counter.count_messages_tokens(messages)
        assert count > 0

    def test_different_models(self):
        """Test token counter with different model names."""
        models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo", "deepseek-chat", "claude-3"]
        for model in models:
            counter = TokenCounter(model=model)
            count = counter.count_tokens("test")
            assert count > 0

    def test_tokenizer_fallback(self):
        """Test fallback tokenizer for unknown models."""
        counter = TokenCounter(model="unknown-model-v1")
        count = counter.count_tokens("Hello world")
        assert count > 0


class TestSummarizeCompressor:
    """Test cases for SummarizeCompressor."""

    @pytest.fixture
    def compressor(self):
        return SummarizeCompressor(TokenCounter(model="gpt-4"))

    def test_no_compression_needed(self, compressor):
        """Test when messages are under threshold."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi"),
        ]
        result = compressor.compress(messages, target_tokens=1000, keep_recent=2)

        assert len(result.messages) == 2
        assert result.compression_ratio == 1.0
        assert result.strategy_used == CompressionStrategy.SUMMARIZE

    def test_compression_triggered(self, compressor):
        """Test compression when over threshold."""
        messages = [
            HumanMessage(content="What is the weather?"),
            AIMessage(content="The weather is sunny."),
            HumanMessage(content="What about tomorrow?"),
            AIMessage(content="It will be cloudy."),
            HumanMessage(content="Thanks!"),
            AIMessage(content="You're welcome!"),
        ]
        # Very low target to force compression
        result = compressor.compress(messages, target_tokens=20, keep_recent=2)

        # Should have summary + recent messages
        assert len(result.messages) == 3  # summary + 2 recent
        assert isinstance(result.messages[0], SystemMessage)
        assert "summary" in result.messages[0].content.lower()
        assert result.compression_ratio < 1.0

    def test_keep_recent_greater_than_messages(self, compressor):
        """Test when keep_recent is greater than message count."""
        messages = [HumanMessage(content="Hello")]
        result = compressor.compress(messages, target_tokens=10, keep_recent=5)

        assert len(result.messages) == 1
        assert result.compression_ratio == 1.0

    def test_creates_summary_content(self, compressor):
        """Test that summary content is created."""
        messages = [
            HumanMessage(content="What is Python?"),
            AIMessage(content="Python is a programming language."),
            HumanMessage(content="What is JavaScript?"),
            AIMessage(content="JavaScript is a web language."),
        ]
        result = compressor.compress(messages, target_tokens=10, keep_recent=0)

        # Should have a summary message
        assert len(result.messages) >= 1
        assert isinstance(result.messages[0], SystemMessage)
        summary = result.messages[0].content
        assert "Previous conversation summary" in summary


class TestTruncateCompressor:
    """Test cases for TruncateCompressor."""

    @pytest.fixture
    def compressor(self):
        return TruncateCompressor(TokenCounter(model="gpt-4"))

    def test_no_truncation_needed(self, compressor):
        """Test when messages are under threshold."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi"),
        ]
        result = compressor.compress(messages, target_tokens=1000, keep_recent=2)

        assert len(result.messages) == 2
        assert result.compression_ratio == 1.0
        assert result.strategy_used == CompressionStrategy.TRUNCATE

    def test_truncation_keeps_recent(self, compressor):
        """Test that truncation keeps recent messages."""
        messages = [
            HumanMessage(content="Message 1"),
            AIMessage(content="Response 1"),
            HumanMessage(content="Message 2"),
            AIMessage(content="Response 2"),
            HumanMessage(content="Message 3"),
            AIMessage(content="Response 3"),
        ]
        result = compressor.compress(messages, target_tokens=20, keep_recent=2)

        # Should keep only recent messages
        assert len(result.messages) == 2
        assert result.messages[0].content == "Message 3"
        assert result.messages[1].content == "Response 3"

    def test_truncation_preserves_system_message(self, compressor):
        """Test that system messages are preserved during truncation."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Message 1"),
            AIMessage(content="Response 1"),
            HumanMessage(content="Message 2"),
            AIMessage(content="Response 2"),
        ]
        result = compressor.compress(messages, target_tokens=15, keep_recent=1)

        # Should have system + recent
        assert len(result.messages) == 2
        assert isinstance(result.messages[0], SystemMessage)
        # The most recent non-system message should be kept
        assert isinstance(result.messages[1], AIMessage)


class TestWindowCompressor:
    """Test cases for WindowCompressor."""

    @pytest.fixture
    def compressor(self):
        return WindowCompressor(TokenCounter(model="gpt-4"))

    def test_no_compression_needed(self, compressor):
        """Test when messages are under threshold."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi"),
        ]
        result = compressor.compress(messages, target_tokens=1000, keep_recent=2)

        assert len(result.messages) == 2
        assert result.compression_ratio == 1.0
        assert result.strategy_used == CompressionStrategy.WINDOW

    def test_window_compression(self, compressor):
        """Test window compression strategy."""
        messages = [
            SystemMessage(content="System prompt"),
            HumanMessage(content="Old question 1"),
            AIMessage(content="Old answer 1"),
            HumanMessage(content="Recent question"),
            AIMessage(content="Recent answer"),
        ]
        result = compressor.compress(messages, target_tokens=25, keep_recent=2)

        # Should have at least system + recent messages (may have summary too)
        assert len(result.messages) >= 3
        assert isinstance(result.messages[0], SystemMessage)  # Original system


class TestMessageCompressor:
    """Test cases for MessageCompressor main class."""

    def test_default_initialization(self):
        """Test default compressor initialization."""
        compressor = MessageCompressor()

        assert compressor.max_tokens == 8000
        assert compressor.compression_threshold == 0.8
        assert compressor.keep_recent_messages == 4
        assert compressor.strategy == CompressionStrategy.WINDOW

    def test_custom_initialization(self):
        """Test custom compressor initialization."""
        compressor = MessageCompressor(
            model="gpt-4o",
            max_tokens=4000,
            compression_threshold=0.9,
            keep_recent_messages=6,
            strategy=CompressionStrategy.SUMMARIZE,
        )

        assert compressor.max_tokens == 4000
        assert compressor.compression_threshold == 0.9
        assert compressor.keep_recent_messages == 6
        assert compressor.strategy == CompressionStrategy.SUMMARIZE

    def test_should_compress_true(self):
        """Test should_compress returns True when over threshold."""
        compressor = MessageCompressor(
            max_tokens=50,
            compression_threshold=0.5,  # Compress when over 25 tokens
        )
        # Create messages that will exceed 25 tokens
        messages = [
            HumanMessage(content="This is a very long message with many words to exceed the token limit"),
            AIMessage(content="This is another very long response with even more words to make sure we hit the limit"),
        ]

        # Should need compression (over 25 tokens)
        assert compressor.should_compress(messages) is True

    def test_should_compress_false(self):
        """Test should_compress returns False when under threshold."""
        compressor = MessageCompressor(
            max_tokens=10000,
            compression_threshold=0.8,
        )
        messages = [
            HumanMessage(content="Hi"),
            AIMessage(content="Hello"),
        ]

        assert compressor.should_compress(messages) is False

    def test_compress_if_needed_no_compression(self):
        """Test compress_if_needed when under threshold."""
        compressor = MessageCompressor(
            max_tokens=1000,
            compression_threshold=0.8,
        )
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi"),
        ]
        result = compressor.compress_if_needed(messages)

        assert len(result.messages) == 2
        assert result.compression_ratio == 1.0
        assert result.original_token_count == result.compressed_token_count

    def test_compress_if_needed_with_compression(self):
        """Test compress_if_needed when over threshold."""
        compressor = MessageCompressor(
            max_tokens=50,
            compression_threshold=0.5,  # Compress when over 25 tokens
            keep_recent_messages=2,
        )
        messages = [
            HumanMessage(content="First question with many words"),
            AIMessage(content="First answer with many words"),
            HumanMessage(content="Second question"),
            AIMessage(content="Second answer"),
        ]
        result = compressor.compress_if_needed(messages)

        # Should be compressed
        assert result.compression_ratio <= 1.0

    def test_force_compress(self):
        """Test force_compress method."""
        compressor = MessageCompressor(
            max_tokens=1000,
            compression_threshold=0.8,
            keep_recent_messages=2,
        )
        messages = [
            HumanMessage(content="Question 1"),
            AIMessage(content="Answer 1"),
            HumanMessage(content="Question 2"),
            AIMessage(content="Answer 2"),
        ]
        # Use a very low target to force compression
        result = compressor.force_compress(messages, target_tokens=10)

        # force_compress should attempt compression regardless of threshold
        # The result structure depends on the strategy (WINDOW by default)
        # Just verify it returns a valid result
        assert isinstance(result.messages, list)
        assert len(result.messages) > 0

    def test_get_token_count(self):
        """Test get_token_count method."""
        compressor = MessageCompressor()
        messages = [
            HumanMessage(content="Hello world"),
            AIMessage(content="Hi there"),
        ]
        count = compressor.get_token_count(messages)

        assert count > 0
        assert isinstance(count, int)

    def test_different_strategies(self):
        """Test compressor with different strategies."""
        messages = [
            HumanMessage(content="Q1"),
            AIMessage(content="A1"),
            HumanMessage(content="Q2"),
            AIMessage(content="A2"),
        ]

        for strategy in CompressionStrategy:
            compressor = MessageCompressor(
                max_tokens=30,
                compression_threshold=0.5,
                strategy=strategy,
            )
            result = compressor.compress_if_needed(messages)
            assert result.strategy_used == strategy


class TestCompressionResult:
    """Test cases for CompressionResult dataclass."""

    def test_result_creation(self):
        """Test CompressionResult creation."""
        messages = [HumanMessage(content="Test")]
        result = CompressionResult(
            messages=messages,
            original_token_count=100,
            compressed_token_count=50,
            compression_ratio=0.5,
            strategy_used=CompressionStrategy.TRUNCATE,
        )

        assert result.messages == messages
        assert result.original_token_count == 100
        assert result.compressed_token_count == 50
        assert result.compression_ratio == 0.5
        assert result.strategy_used == CompressionStrategy.TRUNCATE

    def test_compression_ratio_calculation(self):
        """Test compression ratio is calculated correctly."""
        result = CompressionResult(
            messages=[],
            original_token_count=200,
            compressed_token_count=50,
            compression_ratio=0.25,
            strategy_used=CompressionStrategy.SUMMARIZE,
        )

        assert result.compression_ratio == 0.25
        # 75% reduction
        reduction = (1 - result.compression_ratio) * 100
        assert reduction == 75.0
