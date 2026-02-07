"""
JSON file storage implementation.
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .interfaces import Message, HistoryStorage, StorageProvider
from ..config import config


class JSONHistoryStorage(HistoryStorage):
    """JSON file-based history storage."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.sessions_path = storage_path / "sessions"
        self.sessions_path.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        """Get the session file path."""
        return self.sessions_path / f"{session_id}.json"

    async def get_history(self, session_id: str) -> List[Message]:
        """Get all messages for a session."""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []

        try:
            # Use asyncio to read file asynchronously
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, session_file.read_text)
            data = json.loads(content)

            messages = []
            for msg_data in data.get("messages", []):
                # Parse timestamp if present
                timestamp = None
                if "timestamp" in msg_data:
                    timestamp = datetime.fromisoformat(msg_data["timestamp"])

                messages.append(Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=timestamp
                ))
            return messages
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading session file {session_file}: {e}")
            return []

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        """Append messages to a session."""
        session_file = self._get_session_file(session_id)

        # Get existing messages
        existing_messages = await self.get_history(session_id)
        all_messages = existing_messages + messages

        # Convert to serializable format
        serializable_messages = []
        for msg in all_messages:
            msg_dict = {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            }
            serializable_messages.append(msg_dict)

        data = {
            "session_id": session_id,
            "updated_at": datetime.now().isoformat(),
            "messages": serializable_messages
        }

        try:
            # Use asyncio to write file asynchronously
            loop = asyncio.get_event_loop()
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            await loop.run_in_executor(None, session_file.write_text, json_data)
        except IOError as e:
            print(f"Error writing session file {session_file}: {e}")

    async def clear_history(self, session_id: str) -> None:
        """Clear history for a session."""
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, session_file.unlink)
            except IOError as e:
                print(f"Error deleting session file {session_file}: {e}")


class JSONStorage(StorageProvider):
    """JSON file storage provider."""

    def __init__(self, storage_path: Path = None):
        if storage_path is None:
            storage_path = config.get_storage_path()
        self.storage_path = storage_path
        self._history_storage = None

    async def initialize(self) -> None:
        """Initialize the storage provider."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._history_storage = JSONHistoryStorage(self.storage_path)

    async def close(self) -> None:
        """Close the storage provider."""
        # Nothing to close for file-based storage
        pass

    @property
    def history(self) -> HistoryStorage:
        """Get the history storage."""
        if self._history_storage is None:
            raise RuntimeError("Storage provider not initialized. Call initialize() first.")
        return self._history_storage