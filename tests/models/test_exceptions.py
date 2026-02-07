"""
Tests for model exceptions - Epic 2: Multi-Model LLM Integration.
"""

import pytest
from chat_shell_101.models.exceptions import (
    ModelError,
    ModelNotSupportedError,
    ModelInitializationError,
    ModelAPIError,
    FallbackError,
    MessageConversionError,
)


pytestmark = [pytest.mark.unit, pytest.mark.epic_2]


class TestModelError:
    """Test cases for ModelError base class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = ModelError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.provider is None
        assert error.model is None

    def test_error_with_provider_and_model(self):
        """Test error with provider and model info."""
        error = ModelError(
            "API call failed",
            provider="openai",
            model="gpt-4"
        )
        assert "API call failed" in str(error)
        assert "provider=openai" in str(error)
        assert "model=gpt-4" in str(error)


class TestModelNotSupportedError:
    """Test cases for ModelNotSupportedError."""

    def test_with_model(self):
        """Test error for unsupported model."""
        error = ModelNotSupportedError(model="unknown-model")
        assert "unknown-model" in str(error)
        assert "not supported" in str(error).lower()

    def test_with_provider(self):
        """Test error for unsupported provider."""
        error = ModelNotSupportedError(provider="fake-provider")
        assert "fake-provider" in str(error)
        assert "not supported" in str(error).lower()

    def test_generic_message(self):
        """Test generic error message."""
        error = ModelNotSupportedError()
        assert "not supported" in str(error).lower()


class TestModelInitializationError:
    """Test cases for ModelInitializationError."""

    def test_with_cause(self):
        """Test error with underlying cause."""
        cause = ValueError("Invalid API key")
        error = ModelInitializationError(
            "Failed to initialize",
            provider="openai",
            model="gpt-4",
            cause=cause
        )
        assert "Failed to initialize" in str(error)
        assert error.cause is cause


class TestModelAPIError:
    """Test cases for ModelAPIError."""

    def test_with_status_code(self):
        """Test error with HTTP status code."""
        error = ModelAPIError(
            "Rate limit exceeded",
            provider="openai",
            model="gpt-4",
            status_code=429
        )
        assert "Rate limit exceeded" in str(error)
        assert error.status_code == 429

    def test_with_cause(self):
        """Test error with underlying cause."""
        cause = Exception("Connection timeout")
        error = ModelAPIError(
            "API request failed",
            cause=cause
        )
        assert error.cause is cause


class TestFallbackError:
    """Test cases for FallbackError."""

    def test_basic_error(self):
        """Test basic fallback error."""
        error = FallbackError("All models failed")
        assert str(error) == "All models failed"

    def test_with_errors(self):
        """Test error with list of errors."""
        errors = [
            "Primary (gpt-4): Rate limit",
            "Fallback (gpt-3.5): Timeout"
        ]
        error = FallbackError("All models failed", errors=errors)
        assert "All models failed" in str(error)
        assert "Primary (gpt-4)" in str(error)
        assert "Fallback (gpt-3.5)" in str(error)


class TestMessageConversionError:
    """Test cases for MessageConversionError."""

    def test_basic_error(self):
        """Test basic conversion error."""
        error = MessageConversionError("Invalid message format")
        assert str(error) == "Invalid message format"

    def test_with_formats(self):
        """Test error with format information."""
        error = MessageConversionError(
            "Conversion failed",
            source_format="anthropic",
            target_format="openai"
        )
        assert error.source_format == "anthropic"
        assert error.target_format == "openai"
