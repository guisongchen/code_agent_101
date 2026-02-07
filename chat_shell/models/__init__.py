"""
Multi-model LLM integration for Chat Shell 101.

This module provides a unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)

Example:
    from chat_shell_101.models import ModelFactory

    # Create model by provider name
    llm = ModelFactory.create_model(
        provider="openai",
        model="gpt-4",
        api_key="...",
        temperature=0.7
    )

    # Or use auto-detection from model name
    llm = ModelFactory.create_model(
        model="claude-3-opus-20240229",
        api_key="..."
    )
"""

from .factory import ModelFactory, ModelProvider
from .config import ModelConfig, ProviderConfig
from .exceptions import ModelError, ModelNotSupportedError, FallbackError

__all__ = [
    "ModelFactory",
    "ModelProvider",
    "ModelConfig",
    "ProviderConfig",
    "ModelError",
    "ModelNotSupportedError",
    "FallbackError",
]
