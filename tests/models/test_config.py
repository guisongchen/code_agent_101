"""
Tests for ModelConfig and ProviderConfig - Epic 2: Multi-Model LLM Integration.
"""

import pytest
from chat_shell_101.models.config import ModelConfig, ProviderConfig


pytestmark = [pytest.mark.unit, pytest.mark.epic_2]


class TestProviderConfig:
    """Test cases for ProviderConfig."""

    def test_default_values(self):
        """Test default provider configuration values."""
        config = ProviderConfig()

        assert config.api_key is None
        assert config.base_url is None
        assert config.timeout == 60.0
        assert config.max_retries == 2
        assert config.extra_headers is None
        assert config.organization is None
        assert config.project is None

    def test_custom_values(self):
        """Test custom provider configuration values."""
        config = ProviderConfig(
            api_key="test-key",
            base_url="https://api.example.com",
            timeout=30.0,
            max_retries=5,
            extra_headers={"X-Custom": "header"},
            organization="org-123",
            project="proj-456",
        )

        assert config.api_key == "test-key"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 30.0
        assert config.max_retries == 5
        assert config.extra_headers == {"X-Custom": "header"}
        assert config.organization == "org-123"
        assert config.project == "proj-456"

    def test_timeout_validation(self):
        """Test timeout validation."""
        with pytest.raises(ValueError, match="timeout"):
            ProviderConfig(timeout=0.5)

        with pytest.raises(ValueError, match="timeout"):
            ProviderConfig(timeout=0)

    def test_max_retries_validation(self):
        """Test max_retries validation."""
        with pytest.raises(ValueError, match="max_retries"):
            ProviderConfig(max_retries=-1)

        # Zero retries should be valid
        config = ProviderConfig(max_retries=0)
        assert config.max_retries == 0


class TestModelConfig:
    """Test cases for ModelConfig."""

    def test_default_values(self):
        """Test default model configuration values."""
        config = ModelConfig()

        assert config.provider is None
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.top_p is None
        assert config.frequency_penalty is None
        assert config.presence_penalty is None
        assert config.streaming is True
        assert config.timeout == 60.0
        assert isinstance(config.provider_config, ProviderConfig)
        assert config.fallback_models == []
        assert config.fallback_providers == []

    def test_custom_values(self):
        """Test custom model configuration values."""
        config = ModelConfig(
            provider="anthropic",
            model="claude-3-opus-20240229",
            temperature=0.5,
            max_tokens=2048,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            streaming=False,
            timeout=120.0,
            fallback_models=["claude-3-sonnet-20240229"],
            fallback_providers=["openai"],
        )

        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus-20240229"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.5
        assert config.presence_penalty == 0.3
        assert config.streaming is False
        assert config.timeout == 120.0
        assert config.fallback_models == ["claude-3-sonnet-20240229"]
        assert config.fallback_providers == ["openai"]

    def test_model_required(self):
        """Test that model is required."""
        with pytest.raises(ValueError, match="model"):
            ModelConfig(model="")

    def test_temperature_validation(self):
        """Test temperature range validation."""
        # Valid temperatures
        ModelConfig(temperature=0.0)
        ModelConfig(temperature=2.0)
        ModelConfig(temperature=1.5)

        # Invalid temperatures
        with pytest.raises(ValueError, match="temperature"):
            ModelConfig(temperature=-0.1)

        with pytest.raises(ValueError, match="temperature"):
            ModelConfig(temperature=2.1)

    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        with pytest.raises(ValueError, match="max_tokens"):
            ModelConfig(max_tokens=0)

        with pytest.raises(ValueError, match="max_tokens"):
            ModelConfig(max_tokens=-1)

    def test_top_p_validation(self):
        """Test top_p range validation."""
        # Valid values
        ModelConfig(top_p=0.0)
        ModelConfig(top_p=1.0)
        ModelConfig(top_p=0.5)
        ModelConfig(top_p=None)

        # Invalid values
        with pytest.raises(ValueError, match="top_p"):
            ModelConfig(top_p=-0.1)

        with pytest.raises(ValueError, match="top_p"):
            ModelConfig(top_p=1.1)

    def test_frequency_penalty_validation(self):
        """Test frequency_penalty range validation."""
        # Valid values
        ModelConfig(frequency_penalty=-2.0)
        ModelConfig(frequency_penalty=2.0)
        ModelConfig(frequency_penalty=0.0)
        ModelConfig(frequency_penalty=None)

        # Invalid values
        with pytest.raises(ValueError, match="frequency_penalty"):
            ModelConfig(frequency_penalty=-2.1)

        with pytest.raises(ValueError, match="frequency_penalty"):
            ModelConfig(frequency_penalty=2.1)

    def test_presence_penalty_validation(self):
        """Test presence_penalty range validation."""
        # Valid values
        ModelConfig(presence_penalty=-2.0)
        ModelConfig(presence_penalty=2.0)
        ModelConfig(presence_penalty=0.0)
        ModelConfig(presence_penalty=None)

        # Invalid values
        with pytest.raises(ValueError, match="presence_penalty"):
            ModelConfig(presence_penalty=-2.1)

        with pytest.raises(ValueError, match="presence_penalty"):
            ModelConfig(presence_penalty=2.1)

    def test_to_invocation_kwargs(self):
        """Test conversion to invocation kwargs."""
        config = ModelConfig(temperature=0.5, max_tokens=2048)
        kwargs = config.to_invocation_kwargs()

        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 2048
        assert "top_p" not in kwargs

    def test_to_invocation_kwargs_with_optional(self):
        """Test conversion with optional parameters."""
        config = ModelConfig(
            temperature=0.5,
            max_tokens=2048,
            top_p=0.9,
            frequency_penalty=0.5,
        )
        kwargs = config.to_invocation_kwargs()

        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 2048
        assert kwargs["top_p"] == 0.9
        assert kwargs["frequency_penalty"] == 0.5
        assert "presence_penalty" not in kwargs

    def test_with_fallback(self):
        """Test with_fallback method."""
        config = ModelConfig()
        result = config.with_fallback("gpt-3.5-turbo", "claude-3-haiku-20240307")

        # Should return self
        assert result is config
        # Should have added fallbacks
        assert "gpt-3.5-turbo" in config.fallback_models
        assert "claude-3-haiku-20240307" in config.fallback_models

    def test_copy_with(self):
        """Test copy_with method."""
        original = ModelConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.7,
        )

        copy = original.copy_with(model="gpt-3.5-turbo", temperature=0.5)

        # Copy should have new values
        assert copy.model == "gpt-3.5-turbo"
        assert copy.temperature == 0.5
        # Copy should preserve original values
        assert copy.provider == "openai"

        # Original should be unchanged
        assert original.model == "gpt-4"
        assert original.temperature == 0.7

    def test_copy_with_provider_config(self):
        """Test copy_with with provider config updates."""
        original = ModelConfig(
            provider_config=ProviderConfig(api_key="original-key"),
        )

        # Create a new provider config and copy
        new_provider_config = ProviderConfig(api_key="new-key")
        copy = original.copy_with(provider_config=new_provider_config)

        assert copy.provider_config.api_key == "new-key"
        assert original.provider_config.api_key == "original-key"
