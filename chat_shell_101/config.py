"""
Configuration management for Chat Shell 101.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = Field(default_factory=lambda: os.getenv("CHAT_SHELL_DEFAULT_MODEL", "gpt-4"))
    base_url: Optional[str] = Field(default_factory=lambda: os.getenv("BASE_URL") or None)
    temperature: float = 0.7
    max_tokens: int = 4096


class StorageConfig(BaseModel):
    """Storage configuration."""
    type: str = "json"
    path: Path = Field(default_factory=lambda: Path(
        os.getenv("CHAT_SHELL_STORAGE_PATH", "~/.chat_shell_101")
    ).expanduser())


class Config(BaseModel):
    """Main configuration."""
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    show_thinking: bool = Field(
        default_factory=lambda: os.getenv("CHAT_SHELL_SHOW_THINKING", "false").lower() == "true"
    )

    def validate_api_key(self) -> bool:
        """Validate that OpenAI API key is set."""
        if not self.openai.api_key:
            return False
        # Basic validation - key should start with 'sk-'
        return self.openai.api_key.startswith("sk-")

    def get_storage_path(self) -> Path:
        """Get the storage path, creating it if it doesn't exist."""
        path = self.storage.path
        path.mkdir(parents=True, exist_ok=True)
        return path


def load_config() -> Config:
    """Load and validate configuration."""
    config = Config()

    if not config.validate_api_key():
        print("Warning: OpenAI API key not set or invalid.")
        print("Please set OPENAI_API_KEY environment variable.")

    return config


# Global config instance
config = load_config()