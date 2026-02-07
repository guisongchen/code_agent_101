"""
In-memory storage implementation.
"""

from typing import List, Dict
from .interfaces import Message, HistoryStorage, StorageProvider


class MemoryHistoryStorage(HistoryStorage):
    """In-memory history storage."""

    def __init__(self):
        self.sessions: Dict[str, List[Message]] = {}

    async def get_history(self, session_id: str) -> List[Message]:
        """Get all messages for a session."""
        return self.sessions.get(session_id, [])

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        """Append messages to a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].extend(messages)

    async def clear_history(self, session_id: str) -> None:
        """Clear history for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]


class MemoryStorage(StorageProvider):
    """In-memory storage provider."""

    def __init__(self):
        self._history_storage = MemoryHistoryStorage()

    async def initialize(self) -> None:
        """Initialize the storage provider."""
        # Nothing to initialize for memory storage
        pass

    async def close(self) -> None:
        """Close the storage provider."""
        # Nothing to close for memory storage
        pass

    @property
    def history(self) -> HistoryStorage:
        """Get the history storage."""
        return self._history_storage