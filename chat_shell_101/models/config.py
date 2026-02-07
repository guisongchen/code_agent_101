"""
Configuration classes for multi-model LLM integration.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider.

    Attributes:
        api_key: API key for the provider
        base_url: Optional custom base URL for the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries for failed requests
        extra_headers: Additional headers to include in API requests
        organization: Organization ID (for OpenAI)
        project: Project ID (for OpenAI)
    """

    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 2
    extra_headers: Optional[Dict[str, str]] = None
    organization: Optional[str] = None
    project: Optional[str] = None

    def __post_init__(self):
        if self.timeout < 1:
            raise ValueError("timeout must be at least 1 second")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


@dataclass
class ModelConfig:
    """Configuration for a language model.

    This class encapsulates all settings needed to create and use an LLM,
    including provider configuration, model parameters, and fallback options.

    Attributes:
        provider: The LLM provider (openai, anthropic, google)
        model: The model identifier (e.g., "gpt-4", "claude-3-opus-20240229")
        temperature: Sampling temperature (0.0 to 2.0)
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling parameter
        frequency_penalty: Frequency penalty (-2.0 to 2.0)
        presence_penalty: Presence penalty (-2.0 to 2.0)
        streaming: Whether to enable streaming responses
        timeout: Request timeout in seconds
        provider_config: Provider-specific configuration
        fallback_models: List of fallback model names to try on failure
        fallback_providers: List of fallback providers to try on failure
    """

    # Model identification
    provider: Optional[str] = None  # auto-detected from model if not specified
    model: str = "gpt-4"

    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    streaming: bool = True
    timeout: float = 60.0

    # Provider configuration
    provider_config: ProviderConfig = field(default_factory=ProviderConfig)

    # Fallback configuration
    fallback_models: List[str] = field(default_factory=list)
    fallback_providers: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration."""
        if not self.model:
            raise ValueError("model must be specified")

        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")

        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")

        if self.top_p is not None and (self.top_p < 0 or self.top_p > 1):
            raise ValueError("top_p must be between 0 and 1")

        if self.frequency_penalty is not None and (
            self.frequency_penalty < -2 or self.frequency_penalty > 2
        ):
            raise ValueError("frequency_penalty must be between -2 and 2")

        if self.presence_penalty is not None and (
            self.presence_penalty < -2 or self.presence_penalty > 2
        ):
            raise ValueError("presence_penalty must be between -2 and 2")

    def to_invocation_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs for model invocation.

        Returns a dictionary of parameters suitable for passing to
        the model's bind or invoke methods.
        """
        kwargs = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            kwargs["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            kwargs["presence_penalty"] = self.presence_penalty

        return kwargs

    def with_fallback(self, *models: str) -> "ModelConfig":
        """Add fallback models and return self for chaining.

        Args:
            *models: Model names to use as fallbacks

        Returns:
            Self for method chaining
        """
        self.fallback_models.extend(models)
        return self

    def copy_with(self, **kwargs) -> "ModelConfig":
        """Create a copy with modified attributes.

        Args:
            **kwargs: Attributes to override

        Returns:
            A new ModelConfig with the specified modifications
        """
        # Get current values as dict
        current = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "streaming": self.streaming,
            "timeout": self.timeout,
            "provider_config": self.provider_config,
            "fallback_models": list(self.fallback_models),
            "fallback_providers": list(self.fallback_providers),
        }

        # Apply overrides
        current.update(kwargs)

        # Handle nested provider_config updates
        if "provider_config" in kwargs:
            # Use the new provider_config directly
            pass
        elif any(k.startswith("provider_") for k in kwargs):
            # Update individual provider config fields
            provider_updates = {
                k.replace("provider_", ""): v
                for k, v in kwargs.items()
                if k.startswith("provider_")
            }
            current["provider_config"] = ProviderConfig(
                **{
                    **{
                        "api_key": self.provider_config.api_key,
                        "base_url": self.provider_config.base_url,
                        "timeout": self.provider_config.timeout,
                        "max_retries": self.provider_config.max_retries,
                        "extra_headers": self.provider_config.extra_headers,
                    },
                    **provider_updates,
                }
            )
            # Remove provider_ prefixed keys
            for k in list(current.keys()):
                if k.startswith("provider_"):
                    del current[k]

        return ModelConfig(**current)
