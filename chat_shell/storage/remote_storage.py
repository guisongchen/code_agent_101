"""
Remote storage implementation for HTTP mode backend integration.
"""

import asyncio
import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional

from .interfaces import Message, HistoryStorage, StorageProvider


class RemoteHistoryStorage(HistoryStorage):
    """Remote API-based history storage."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=self.timeout,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_history(self, session_id: str) -> List[Message]:
        """Get messages from remote API."""
        if not self._client:
            raise RuntimeError("Storage not initialized")

        response = await self._client.get(f"/api/v1/sessions/{session_id}/messages")
        response.raise_for_status()

        data = response.json()
        messages = []
        for msg_data in data.get("messages", []):
            timestamp = None
            if msg_data.get("timestamp"):
                timestamp = datetime.fromisoformat(msg_data["timestamp"])
            messages.append(
                Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=timestamp,
                )
            )
        return messages

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        """Append messages via remote API."""
        if not self._client:
            raise RuntimeError("Storage not initialized")

        payload = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in messages
            ]
        }

        response = await self._client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json=payload,
        )
        response.raise_for_status()

    async def clear_history(self, session_id: str) -> None:
        """Clear history via remote API."""
        if not self._client:
            raise RuntimeError("Storage not initialized")

        response = await self._client.delete(
            f"/api/v1/sessions/{session_id}/messages"
        )
        response.raise_for_status()


class RemoteStorage(StorageProvider):
    """Remote storage provider for backend integration."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._history_storage: Optional[RemoteHistoryStorage] = None

    async def initialize(self) -> None:
        """Initialize the storage provider."""
        self._history_storage = RemoteHistoryStorage(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )
        await self._history_storage.initialize()

    async def close(self) -> None:
        """Close the storage provider."""
        if self._history_storage:
            await self._history_storage.close()

    @property
    def history(self) -> HistoryStorage:
        """Get the history storage."""
        if self._history_storage is None:
            raise RuntimeError(
                "Storage provider not initialized. Call initialize() first."
            )
        return self._history_storage
