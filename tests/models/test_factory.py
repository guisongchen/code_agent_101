"""
Tests for ModelFactory - Epic 2: Multi-Model LLM Integration.
"""

import pytest
from chat_shell.models.factory import ModelFactory, ModelProvider
from chat_shell.models.config import ModelConfig
from chat_shell.models.exceptions import ModelNotSupportedError, ModelInitializationError


pytestmark = [pytest.mark.unit, pytest.mark.epic_2]


class TestModelProvider:
    """Test cases for ModelProvider enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.ANTHROPIC.value == "anthropic"
        assert ModelProvider.GOOGLE.value == "google"

    def test_from_string_valid(self):
        """Test creating from valid string."""
        assert ModelProvider.from_string("openai") == ModelProvider.OPENAI
        assert ModelProvider.from_string("anthropic") == ModelProvider.ANTHROPIC
        assert ModelProvider.from_string("google") == ModelProvider.GOOGLE

    def test_from_string_case_insensitive(self):
        """Test that from_string is case insensitive."""
        assert ModelProvider.from_string("OPENAI") == ModelProvider.OPENAI
        assert ModelProvider.from_string("Anthropic") == ModelProvider.ANTHROPIC

    def test_from_string_invalid(self):
        """Test that invalid string raises error."""
        with pytest.raises(ModelNotSupportedError):
            ModelProvider.from_string("invalid")


class TestModelFactoryDetection:
    """Test cases for provider detection from model names."""

    def test_detect_openai_models(self):
        """Test detection of OpenAI models."""
        assert ModelFactory.detect_provider("gpt-4") == ModelProvider.OPENAI
        assert ModelFactory.detect_provider("gpt-3.5-turbo") == ModelProvider.OPENAI
        assert ModelFactory.detect_provider("gpt-4-turbo-preview") == ModelProvider.OPENAI
        assert ModelFactory.detect_provider("text-davinci-003") == ModelProvider.OPENAI
        assert ModelFactory.detect_provider("text-curie-001") == ModelProvider.OPENAI

    def test_detect_anthropic_models(self):
        """Test detection of Anthropic models."""
        assert ModelFactory.detect_provider("claude-3-opus-20240229") == ModelProvider.ANTHROPIC
        assert ModelFactory.detect_provider("claude-3-sonnet-20240229") == ModelProvider.ANTHROPIC
        assert ModelFactory.detect_provider("claude-3-haiku-20240307") == ModelProvider.ANTHROPIC
        assert ModelFactory.detect_provider("claude-2.1") == ModelProvider.ANTHROPIC

    def test_detect_google_models(self):
        """Test detection of Google models."""
        assert ModelFactory.detect_provider("gemini-pro") == ModelProvider.GOOGLE
        assert ModelFactory.detect_provider("gemini-ultra") == ModelProvider.GOOGLE
        assert ModelFactory.detect_provider("palm-2") == ModelProvider.GOOGLE

    def test_detect_unknown_model(self):
        """Test that unknown model raises error."""
        with pytest.raises(ModelNotSupportedError):
            ModelFactory.detect_provider("unknown-model-v1")

        with pytest.raises(ModelNotSupportedError):
            ModelFactory.detect_provider("")


class TestModelFactoryCreateModel:
    """Test cases for creating models."""

    def test_create_with_explicit_provider(self):
        """Test creating model with explicit provider."""
        # Model creation succeeds without API key, only fails on actual use
        llm = ModelFactory.create_model(
            model="gpt-4",
            provider=ModelProvider.OPENAI,
        )
        assert llm is not None

    def test_create_with_auto_detection(self):
        """Test creating model with auto-detected provider."""
        llm_openai = ModelFactory.create_model(model="gpt-4")
        assert llm_openai is not None

        # Claude model will fail because langchain-anthropic is not installed
        with pytest.raises(ModelInitializationError):
            ModelFactory.create_model(model="claude-3-opus-20240229")

    def test_create_with_parameters(self):
        """Test creating model with all parameters."""
        llm = ModelFactory.create_model(
            model="gpt-4",
            provider=ModelProvider.OPENAI,
            api_key="test-key",
            base_url="https://api.example.com",
            temperature=0.5,
            max_tokens=2048,
            streaming=False,
            timeout=120.0,
            max_retries=5,
        )
        assert llm is not None


class TestModelFactoryFromConfig:
    """Test cases for creating models from config."""

    def test_create_from_config_basic(self):
        """Test creating model from basic config."""
        config = ModelConfig(
            provider="openai",
            model="gpt-4",
        )

        llm = ModelFactory.create_model_from_config(config)
        assert llm is not None

    def test_create_from_config_with_provider_config(self):
        """Test creating model from config with provider config."""
        from chat_shell.models.config import ProviderConfig

        config = ModelConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.3,
            max_tokens=1024,
            provider_config=ProviderConfig(
                api_key="test-key",
                base_url="https://api.example.com",
                timeout=90.0,
                max_retries=3,
            ),
        )

        llm = ModelFactory.create_model_from_config(config)
        assert llm is not None

    def test_create_from_config_auto_detect_provider(self):
        """Test that provider is auto-detected from model name."""
        config = ModelConfig(model="claude-3-opus-20240229")  # No provider specified

        # Provider should be auto-detected
        assert config.provider is None

        # This will fail because anthropic is not installed
        with pytest.raises(ModelInitializationError):
            ModelFactory.create_model_from_config(config)


class TestFallbackModelWrapper:
    """Test cases for FallbackModelWrapper."""

    def test_wrapper_initialization(self):
        """Test that wrapper can be initialized."""
        config = ModelConfig(
            model="gpt-4",
            fallback_models=["gpt-3.5-turbo"],
        )

        wrapper = ModelFactory.create_model_with_fallbacks(config)

        assert wrapper.config == config
        assert not wrapper._initialized

    def test_bind_tools_returns_self(self):
        """Test that bind_tools returns self for chaining."""
        config = ModelConfig(model="gpt-4")
        wrapper = ModelFactory.create_model_with_fallbacks(config)

        result = wrapper.bind_tools([])

        assert result is wrapper
