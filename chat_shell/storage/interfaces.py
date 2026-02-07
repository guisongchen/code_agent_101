"""
Storage interfaces for chat history.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Literal
from pathlib import Path


@dataclass
class Message:
    """A chat message."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class HistoryStorage(ABC):
    """Abstract base class for history storage."""

    @abstractmethod
    async def get_history(self, session_id: str) -> List[Message]:
        """Get all messages for a session."""
        pass

    @abstractmethod
    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        """Append messages to a session."""
        pass

    @abstractmethod
    async def clear_history(self, session_id: str) -> None:
        """Clear history for a session."""
        pass


class StorageProvider(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage provider."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the storage provider."""
        pass

    @property
    @abstractmethod
    def history(self) -> HistoryStorage:
        """Get the history storage."""
        pass