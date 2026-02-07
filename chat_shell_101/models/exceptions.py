"""
Exceptions for multi-model LLM integration.
"""


class ModelError(Exception):
    """Base exception for model-related errors."""

    def __init__(self, message: str, provider: str = None, model: str = None):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.message = message

    def __str__(self):
        parts = [self.message]
        if self.provider:
            parts.append(f"provider={self.provider}")
        if self.model:
            parts.append(f"model={self.model}")
        return " | ".join(parts)


class ModelNotSupportedError(ModelError):
    """Raised when a model or provider is not supported."""

    def __init__(self, model: str = None, provider: str = None):
        message = "Model/provider not supported"
        if model:
            message = f"Model '{model}' is not supported"
        elif provider:
            message = f"Provider '{provider}' is not supported"
        super().__init__(message, provider=provider, model=model)


class ModelInitializationError(ModelError):
    """Raised when a model fails to initialize."""

    def __init__(self, message: str, provider: str = None, model: str = None, cause: Exception = None):
        super().__init__(message, provider=provider, model=model)
        self.cause = cause


class ModelAPIError(ModelError):
    """Raised when a model API call fails."""

    def __init__(
        self,
        message: str,
        provider: str = None,
        model: str = None,
        status_code: int = None,
        cause: Exception = None,
    ):
        super().__init__(message, provider=provider, model=model)
        self.status_code = status_code
        self.cause = cause


class FallbackError(ModelError):
    """Raised when all fallback models fail."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []

    def __str__(self):
        base = super().__str__()
        if self.errors:
            error_details = "\n".join(f"  - {e}" for e in self.errors)
            return f"{base}\nFallback errors:\n{error_details}"
        return base


class MessageConversionError(ModelError):
    """Raised when message format conversion fails."""

    def __init__(self, message: str, source_format: str = None, target_format: str = None):
        super().__init__(message)
        self.source_format = source_format
        self.target_format = target_format
