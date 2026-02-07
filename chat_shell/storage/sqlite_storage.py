"""
SQLite storage implementation for CLI mode.
"""

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .interfaces import Message, HistoryStorage, StorageProvider


class SQLiteHistoryStorage(HistoryStorage):
    """SQLite-based history storage."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    async def initialize(self) -> None:
        """Initialize database schema."""

        def _init():
            conn = self._get_connection()
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                    )
                """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id, timestamp)
                """
                )
                conn.commit()
            finally:
                conn.close()

        await asyncio.to_thread(_init)

    async def get_history(self, session_id: str) -> List[Message]:
        """Get all messages for a session."""

        def _get():
            conn = self._get_connection()
            try:
                # Ensure session exists
                cursor = conn.execute(
                    "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
                )
                if not cursor.fetchone():
                    return []

                # Get messages
                cursor = conn.execute(
                    """
                    SELECT role, content, timestamp
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY timestamp ASC, id ASC
                    """,
                    (session_id,),
                )
                rows = cursor.fetchall()

                messages = []
                for row in rows:
                    timestamp = None
                    if row["timestamp"]:
                        timestamp = datetime.fromisoformat(row["timestamp"])
                    messages.append(
                        Message(role=row["role"], content=row["content"], timestamp=timestamp)
                    )
                return messages
            finally:
                conn.close()

        return await asyncio.to_thread(_get)

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        """Append messages to a session."""

        def _append():
            conn = self._get_connection()
            try:
                # Insert or update session
                conn.execute(
                    """
                    INSERT INTO sessions (session_id, updated_at)
                    VALUES (?, CURRENT_TIMESTAMP)
                    ON CONFLICT(session_id) DO UPDATE SET
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id,),
                )

                # Insert messages
                for msg in messages:
                    conn.execute(
                        """
                        INSERT INTO messages (session_id, role, content, timestamp)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            msg.role,
                            msg.content,
                            msg.timestamp.isoformat()
                            if msg.timestamp
                            else datetime.now().isoformat(),
                        ),
                    )

                conn.commit()
            finally:
                conn.close()

        await asyncio.to_thread(_append)

    async def clear_history(self, session_id: str) -> None:
        """Clear history for a session."""

        def _clear():
            conn = self._get_connection()
            try:
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
            finally:
                conn.close()

        await asyncio.to_thread(_clear)

    async def list_sessions(self) -> List[str]:
        """List all session IDs."""

        def _list():
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    "SELECT session_id FROM sessions ORDER BY updated_at DESC"
                )
                return [row["session_id"] for row in cursor.fetchall()]
            finally:
                conn.close()

        return await asyncio.to_thread(_list)


class SQLiteStorage(StorageProvider):
    """SQLite storage provider."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            from ..config import config

            db_path = config.get_storage_path() / "history.db"
        self.db_path = db_path
        self._history_storage: Optional[SQLiteHistoryStorage] = None

    async def initialize(self) -> None:
        """Initialize the storage provider."""
        self._history_storage = SQLiteHistoryStorage(self.db_path)
        await self._history_storage.initialize()

    async def close(self) -> None:
        """Close the storage provider."""
        # SQLite connections are per-operation, nothing to close
        pass

    @property
    def history(self) -> HistoryStorage:
        """Get the history storage."""
        if self._history_storage is None:
            raise RuntimeError(
                "Storage provider not initialized. Call initialize() first."
            )
        return self._history_storage
