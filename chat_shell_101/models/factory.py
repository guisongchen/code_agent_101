"""
Model factory for creating LLM instances from different providers.
"""

import os
from enum import Enum
from typing import Optional, Type, Dict, Any, List
import logging

from langchain_core.language_models.chat_models import BaseChatModel

from .config import ModelConfig, ProviderConfig
from .exceptions import ModelNotSupportedError, ModelInitializationError, FallbackError

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

    @classmethod
    def from_string(cls, value: str) -> "ModelProvider":
        """Get provider from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ModelNotSupportedError(provider=value)


class ModelFactory:
    """Factory for creating LLM instances from various providers.

    This factory provides a unified interface for creating LLM instances
    from OpenAI, Anthropic, Google, and other providers. It supports
    automatic provider detection from model names and fallback mechanisms.

    Example:
        # Create by explicit provider
        llm = ModelFactory.create_model(
            provider=ModelProvider.OPENAI,
            model="gpt-4",
            api_key="..."
        )

        # Auto-detect provider from model name
        llm = ModelFactory.create_model(model="claude-3-opus-20240229")

        # With fallbacks
        llm = ModelFactory.create_model_with_fallbacks(
            ModelConfig(
                model="gpt-4",
                fallback_models=["gpt-3.5-turbo"]
            )
        )
    """

    # Model name patterns for auto-detection
    _PROVIDER_PATTERNS = {
        ModelProvider.OPENAI: [
            "gpt-",
            "text-davinci",
            "text-curie",
            "text-babbage",
            "text-ada",
        ],
        ModelProvider.ANTHROPIC: [
            "claude",
            "anthropic",
        ],
        ModelProvider.GOOGLE: [
            "gemini",
            "palm",
            "bison",
        ],
    }

    # Environment variable names for API keys
    _API_KEY_ENV_VARS = {
        ModelProvider.OPENAI: "OPENAI_API_KEY",
        ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        ModelProvider.GOOGLE: "GOOGLE_API_KEY",
    }

    @classmethod
    def detect_provider(cls, model_name: str) -> ModelProvider:
        """Detect the provider from a model name.

        Args:
            model_name: The model identifier

        Returns:
            The detected ModelProvider

        Raises:
            ModelNotSupportedError: If provider cannot be detected
        """
        model_lower = model_name.lower()

        for provider, patterns in cls._PROVIDER_PATTERNS.items():
            for pattern in patterns:
                if pattern in model_lower:
                    return provider

        raise ModelNotSupportedError(model=model_name)

    @classmethod
    def create_model(
        cls,
        model: str,
        provider: Optional[ModelProvider] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        streaming: bool = True,
        timeout: float = 60.0,
        max_retries: int = 2,
        **kwargs,
    ) -> BaseChatModel:
        """Create an LLM instance.

        Args:
            model: The model identifier
            provider: The provider (auto-detected if not specified)
            api_key: API key (read from env var if not specified)
            base_url: Optional custom base URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            streaming: Enable streaming responses
            timeout: Request timeout
            max_retries: Maximum retries for failed requests
            **kwargs: Additional provider-specific parameters

        Returns:
            A LangChain BaseChatModel instance

        Raises:
            ModelNotSupportedError: If provider is not supported
            ModelInitializationError: If model fails to initialize
        """
        # Auto-detect provider if not specified
        if provider is None:
            try:
                provider = cls.detect_provider(model)
            except ModelNotSupportedError:
                # Default to OpenAI if can't detect
                provider = ModelProvider.OPENAI
                logger.warning(
                    f"Could not detect provider for model '{model}', defaulting to OpenAI"
                )

        # Get API key from environment if not provided
        if api_key is None:
            env_var = cls._API_KEY_ENV_VARS.get(provider)
            if env_var:
                api_key = os.getenv(env_var)

        # Create provider config
        provider_config = ProviderConfig(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Create model config
        config = ModelConfig(
            provider=provider.value,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            provider_config=provider_config,
        )

        return cls._create_model_internal(config)

    @classmethod
    def create_model_from_config(cls, config: ModelConfig) -> BaseChatModel:
        """Create an LLM instance from a ModelConfig.

        Args:
            config: The model configuration

        Returns:
            A LangChain BaseChatModel instance
        """
        # Auto-detect provider if not specified
        if config.provider is None:
            try:
                provider = cls.detect_provider(config.model)
                config.provider = provider.value
            except ModelNotSupportedError:
                config.provider = ModelProvider.OPENAI.value

        # Get API key from environment if not provided
        if config.provider_config.api_key is None:
            env_var = cls._API_KEY_ENV_VARS.get(ModelProvider(config.provider))
            if env_var:
                config.provider_config.api_key = os.getenv(env_var)

        return cls._create_model_internal(config)

    @classmethod
    def create_model_with_fallbacks(
        cls, config: ModelConfig
    ) -> "FallbackModelWrapper":
        """Create an LLM instance with fallback support.

        Args:
            config: The model configuration with fallback options

        Returns:
            A FallbackModelWrapper that handles fallback on failures
        """
        return FallbackModelWrapper(config)

    @classmethod
    def _create_model_internal(cls, config: ModelConfig) -> BaseChatModel:
        """Internal method to create a model instance.

        Args:
            config: The model configuration

        Returns:
            A LangChain BaseChatModel instance
        """
        provider = ModelProvider(config.provider)

        if provider == ModelProvider.OPENAI:
            return cls._create_openai_model(config)
        elif provider == ModelProvider.ANTHROPIC:
            return cls._create_anthropic_model(config)
        elif provider == ModelProvider.GOOGLE:
            return cls._create_google_model(config)
        else:
            raise ModelNotSupportedError(provider=config.provider)

    @classmethod
    def _create_openai_model(cls, config: ModelConfig) -> BaseChatModel:
        """Create an OpenAI model instance."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ModelInitializationError(
                "langchain-openai is not installed. "
                "Install with: pip install langchain-openai",
                provider="openai",
                model=config.model,
            )

        kwargs = {
            "model": config.model,
            "api_key": config.provider_config.api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "streaming": config.streaming,
            "timeout": config.provider_config.timeout,
            "max_retries": config.provider_config.max_retries,
        }

        if config.provider_config.base_url:
            kwargs["base_url"] = config.provider_config.base_url

        if config.provider_config.organization:
            kwargs["organization"] = config.provider_config.organization

        if config.provider_config.extra_headers:
            kwargs["default_headers"] = config.provider_config.extra_headers

        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        try:
            return ChatOpenAI(**kwargs)
        except Exception as e:
            raise ModelInitializationError(
                f"Failed to initialize OpenAI model: {e}",
                provider="openai",
                model=config.model,
                cause=e,
            )

    @classmethod
    def _create_anthropic_model(cls, config: ModelConfig) -> BaseChatModel:
        """Create an Anthropic Claude model instance."""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ModelInitializationError(
                "langchain-anthropic is not installed. "
                "Install with: pip install langchain-anthropic",
                provider="anthropic",
                model=config.model,
            )

        kwargs = {
            "model": config.model,
            "api_key": config.provider_config.api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "streaming": config.streaming,
            "timeout": config.provider_config.timeout,
            "max_retries": config.provider_config.max_retries,
        }

        if config.provider_config.base_url:
            kwargs["base_url"] = config.provider_config.base_url

        if config.provider_config.extra_headers:
            kwargs["default_headers"] = config.provider_config.extra_headers

        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        try:
            return ChatAnthropic(**kwargs)
        except Exception as e:
            raise ModelInitializationError(
                f"Failed to initialize Anthropic model: {e}",
                provider="anthropic",
                model=config.model,
                cause=e,
            )

    @classmethod
    def _create_google_model(cls, config: ModelConfig) -> BaseChatModel:
        """Create a Google Gemini model instance."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ModelInitializationError(
                "langchain-google-genai is not installed. "
                "Install with: pip install langchain-google-genai",
                provider="google",
                model=config.model,
            )

        kwargs = {
            "model": config.model,
            "api_key": config.provider_config.api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "streaming": config.streaming,
            "timeout": config.provider_config.timeout,
        }

        # Google uses transport options for retries
        if config.provider_config.max_retries > 0:
            kwargs["transport"] = "rest"
            kwargs["client_options"] = {
                "api_endpoint": config.provider_config.base_url
            } if config.provider_config.base_url else None

        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        try:
            return ChatGoogleGenerativeAI(**kwargs)
        except Exception as e:
            raise ModelInitializationError(
                f"Failed to initialize Google model: {e}",
                provider="google",
                model=config.model,
                cause=e,
            )


class FallbackModelWrapper:
    """Wrapper that provides fallback support for model failures.

    This wrapper attempts to use the primary model first, and if that fails,
    it falls back to the configured fallback models in order.

    Example:
        wrapper = FallbackModelWrapper(ModelConfig(
            model="gpt-4",
            fallback_models=["gpt-3.5-turbo", "claude-3-haiku-20240307"]
        ))

        # This will try gpt-4 first, then fall back on failure
        response = await wrapper.ainvoke(messages)
    """

    def __init__(self, config: ModelConfig):
        """Initialize with model configuration.

        Args:
            config: Model configuration with fallback options
        """
        self.config = config
        self._primary_model: Optional[BaseChatModel] = None
        self._fallback_models: Dict[str, BaseChatModel] = {}
        self._initialized = False

    async def _ensure_initialized(self):
        """Lazy initialization of models."""
        if self._initialized:
            return

        # Create primary model
        self._primary_model = ModelFactory.create_model_from_config(self.config)

        # Create fallback models
        for fallback_model in self.config.fallback_models:
            try:
                fallback_config = self.config.copy_with(
                    model=fallback_model,
                    fallback_models=[],  # Prevent nested fallbacks
                )
                self._fallback_models[fallback_model] = (
                    ModelFactory.create_model_from_config(fallback_config)
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize fallback model {fallback_model}: {e}"
                )

        self._initialized = True

    async def ainvoke(self, messages: List[Any], **kwargs) -> Any:
        """Invoke the model with fallback support.

        Args:
            messages: The messages to send
            **kwargs: Additional arguments for the model

        Returns:
            The model response

        Raises:
            FallbackError: If all models fail
        """
        await self._ensure_initialized()

        errors = []

        # Try primary model
        try:
            return await self._primary_model.ainvoke(messages, **kwargs)
        except Exception as e:
            logger.warning(f"Primary model failed: {e}")
            errors.append(f"Primary ({self.config.model}): {e}")

        # Try fallbacks
        for model_name, model in self._fallback_models.items():
            try:
                logger.info(f"Trying fallback model: {model_name}")
                return await model.ainvoke(messages, **kwargs)
            except Exception as e:
                logger.warning(f"Fallback model {model_name} failed: {e}")
                errors.append(f"Fallback ({model_name}): {e}")

        raise FallbackError("All models failed", errors=errors)

    def invoke(self, messages: List[Any], **kwargs) -> Any:
        """Synchronous invoke with fallback support.

        Args:
            messages: The messages to send
            **kwargs: Additional arguments for the model

        Returns:
            The model response

        Raises:
            FallbackError: If all models fail
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, use run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(
                    self.ainvoke(messages, **kwargs), loop
                )
                return future.result()
            else:
                return loop.run_until_complete(self.ainvoke(messages, **kwargs))
        except RuntimeError:
            # No event loop running, create one
            return asyncio.run(self.ainvoke(messages, **kwargs))

    async def astream(self, messages: List[Any], **kwargs):
        """Stream responses with fallback support.

        Args:
            messages: The messages to send
            **kwargs: Additional arguments for the model

        Yields:
            Response chunks from the model
        """
        await self._ensure_initialized()

        errors = []

        # Try primary model
        try:
            async for chunk in self._primary_model.astream(messages, **kwargs):
                yield chunk
            return
        except Exception as e:
            logger.warning(f"Primary model failed during streaming: {e}")
            errors.append(f"Primary ({self.config.model}): {e}")

        # Try fallbacks
        for model_name, model in self._fallback_models.items():
            try:
                logger.info(f"Trying fallback model for streaming: {model_name}")
                async for chunk in model.astream(messages, **kwargs):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Fallback model {model_name} failed: {e}")
                errors.append(f"Fallback ({model_name}): {e}")

        raise FallbackError("All models failed during streaming", errors=errors)

    def bind_tools(self, tools: List[Any], **kwargs):
        """Bind tools to all models (primary and fallbacks).

        Args:
            tools: The tools to bind
            **kwargs: Additional binding arguments

        Returns:
            Self for chaining
        """
        # This is a bit tricky - we need to bind tools to all models
        # but we can't do it lazily. We'll store the tools and bind them
        # during initialization.
        self._tools_to_bind = tools
        self._bind_kwargs = kwargs
        return self

    async def _ensure_initialized(self):
        """Override to bind tools after initialization."""
        await super(FallbackModelWrapper, self)._ensure_initialized()

        # Bind tools if specified
        if hasattr(self, "_tools_to_bind") and self._tools_to_bind:
            self._primary_model = self._primary_model.bind_tools(
                self._tools_to_bind, **self._bind_kwargs
            )
            for name, model in self._fallback_models.items():
                self._fallback_models[name] = model.bind_tools(
                    self._tools_to_bind, **self._bind_kwargs
                )
