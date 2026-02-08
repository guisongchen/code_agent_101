# ADR 006: Storage Layer

## Status

Accepted

## Context

With the deployment modes (Epic 4) in place, the system needed a flexible storage abstraction to support different persistence requirements across CLI, HTTP, and Package modes. Each deployment mode has distinct storage needs:

1. **CLI Mode**: Local persistence with fast querying and session management
2. **HTTP Mode**: Remote storage backend for distributed deployments
3. **Package Mode**: In-memory storage for embedded library usage

Key requirements included:
- Common interface across all storage backends
- Async-first design matching the agent architecture
- Support for multiple backends (memory, JSON files, SQLite, HTTP API)
- Session-based message history with timestamps
- Easy switching between backends via configuration
- Clean separation between storage logic and business logic

## Decision

We implemented a storage layer using abstract interfaces with multiple concrete implementations, following the Strategy and Abstract Factory patterns.

### 1. Abstract Interfaces

**Decision:** Define `StorageProvider` and `HistoryStorage` abstract base classes with a `Message` data transfer object.

**Rationale:**
- Abstract interfaces enable swapping backends without changing business logic
- Separation between provider lifecycle (initialize/close) and data operations
- `Message` dataclass provides structured data transfer with type safety
- Async methods align with the agent's async architecture

**Interface Design:**
```python
@dataclass
class Message:
    """A chat message."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

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
```

**Key Design Points:**
- `StorageProvider` manages lifecycle (initialize/close)
- `HistoryStorage` handles data operations (get/append/clear)
- `Message` uses dataclass for clean serialization
- Session-based organization with string session IDs

**Location:** `chat_shell_101/storage/interfaces.py`

### 2. MemoryStorage

**Decision:** Implement in-memory storage using Python dictionaries for testing and Package mode.

**Rationale:**
- Zero external dependencies
- Fastest performance for temporary storage
- Ideal for unit tests and embedded library usage
- Data is lost on process termination (by design)

**Implementation:**
```python
class MemoryHistoryStorage(HistoryStorage):
    """In-memory history storage."""

    def __init__(self):
        self.sessions: Dict[str, List[Message]] = {}

    async def get_history(self, session_id: str) -> List[Message]:
        return self.sessions.get(session_id, [])

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].extend(messages)

    async def clear_history(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
```

**Use Cases:**
- Unit testing (fast, isolated)
- Package mode embedded usage
- Development and debugging

**Location:** `chat_shell_101/storage/memory_storage.py`

### 3. JSONStorage

**Decision:** Implement file-based JSON storage for simple persistence without database setup.

**Rationale:**
- Human-readable format for debugging
- No database server required
- Easy backup and migration
- Suitable for single-user CLI deployments

**Implementation:**
```python
class JSONHistoryStorage(HistoryStorage):
    """JSON file-based history storage."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.sessions_path = storage_path / "sessions"
        self.sessions_path.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        return self.sessions_path / f"{session_id}.json"

    async def get_history(self, session_id: str) -> List[Message]:
        # Read and parse JSON file asynchronously
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []
        # ... parse JSON to Message objects

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        # Read existing, append, write back
        existing_messages = await self.get_history(session_id)
        all_messages = existing_messages + messages
        # ... serialize to JSON and write
```

**Storage Format:**
```json
{
  "session_id": "uuid-here",
  "updated_at": "2024-01-15T10:30:00",
  "messages": [
    {"role": "user", "content": "Hello", "timestamp": "2024-01-15T10:30:00"},
    {"role": "assistant", "content": "Hi!", "timestamp": "2024-01-15T10:30:01"}
  ]
}
```

**Use Cases:**
- Single-user CLI deployments
- Simple persistence without database
- Easy data inspection and backup

**Location:** `chat_shell_101/storage/json_storage.py`

### 4. SQLiteStorage

**Decision:** Implement SQLite storage for local CLI mode with ACID compliance and session management.

**Rationale:**
- ACID compliance for data integrity
- Better query performance than JSON for large histories
- Sessions table enables listing and metadata
- Standard library support (no extra dependencies)
- Indexed for fast retrieval

**Schema Design:**
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_session ON messages(session_id, timestamp);
```

**Implementation:**
```python
class SQLiteHistoryStorage(HistoryStorage):
    """SQLite-based history storage."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def initialize(self) -> None:
        # Create tables and indexes using asyncio.to_thread

    async def get_history(self, session_id: str) -> List[Message]:
        # Query with ORDER BY timestamp ASC, id ASC

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        # UPSERT session, INSERT messages in transaction

    async def clear_history(self, session_id: str) -> None:
        # DELETE with CASCADE

    async def list_sessions(self) -> List[str]:
        """List all session IDs (SQLite-specific extension)."""
```

**Async Pattern:**
```python
async def get_history(self, session_id: str) -> List[Message]:
    return await asyncio.to_thread(self._get_history_sync, session_id)
```

**Use Cases:**
- CLI mode default storage
- Multi-session management with `list_sessions()`
- Production local deployments

**Location:** `chat_shell_101/storage/sqlite_storage.py`

### 5. RemoteStorage

**Decision:** Implement HTTP API client storage for HTTP mode backend integration.

**Rationale:**
- Enables stateless HTTP servers
- Centralized storage for multi-instance deployments
- Standard REST API pattern
- Authentication support via API keys

**Implementation:**
```python
class RemoteHistoryStorage(HistoryStorage):
    """Remote API-based history storage."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=self.timeout,
        )

    async def get_history(self, session_id: str) -> List[Message]:
        response = await self._client.get(f"/api/v1/sessions/{session_id}/messages")
        response.raise_for_status()
        data = response.json()
        # ... parse to Message objects

    async def append_messages(self, session_id: str, messages: List[Message]) -> None:
        payload = {"messages": [...]}
        response = await self._client.post(
            f"/api/v1/sessions/{session_id}/messages", json=payload
        )
        response.raise_for_status()
```

**API Endpoints:**
- `GET /api/v1/sessions/{session_id}/messages` - Get messages
- `POST /api/v1/sessions/{session_id}/messages` - Append messages
- `DELETE /api/v1/sessions/{session_id}/messages` - Clear history

**Use Cases:**
- HTTP mode with external storage backend
- Multi-instance deployments
- Centralized history service

**Location:** `chat_shell_101/storage/remote_storage.py`

### 6. Deployment Mode Mapping

**Decision:** Map deployment modes to appropriate storage backends.

**Rationale:**
- Each mode has different persistence requirements
- Configuration-driven backend selection
- Easy to override for specific use cases

**Mapping:**
| Mode | Default Storage | Use Case |
|------|-----------------|----------|
| CLI | SQLite | Local persistence with session management |
| HTTP | Remote | Backend integration, stateless servers |
| Package | Memory | Embedded library, testing |

**Configuration:**
```python
# Environment variables
CHAT_SHELL_STORAGE_TYPE=json     # Select backend
CHAT_SHELL_STORAGE_PATH=~/.chat_shell_101  # Data directory

# CLI override
chat-shell chat --storage sqlite
chat-shell chat --storage json
chat-shell chat --storage memory
```

### 7. Module Organization

**Decision:** Organize storage code with clear separation of interfaces and implementations.

**Structure:**
```
chat_shell_101/storage/
├── __init__.py          # Public exports
├── interfaces.py        # Abstract base classes
├── memory_storage.py    # In-memory implementation
├── json_storage.py      # JSON file implementation
├── sqlite_storage.py    # SQLite implementation
└── remote_storage.py    # HTTP API client implementation
```

**Exports:**
```python
__all__ = [
    "Message",
    "HistoryStorage",
    "StorageProvider",
    "JSONStorage",
    "MemoryStorage",
    "SQLiteStorage",
    "RemoteStorage",
]
```

## Consequences

### Positive

- **Flexibility**: Four storage backends serve different deployment needs
- **Testability**: Memory storage enables fast, isolated unit tests
- **Consistency**: Common interface across all backends
- **Type Safety**: Abstract methods enforced at runtime, type hints for static analysis
- **Async-First**: All operations are async, matching agent architecture
- **No ORM Dependency**: SQLite uses stdlib, avoiding SQLAlchemy complexity
- **Clean Separation**: Storage logic isolated from business logic
- **Extensibility**: New backends implement the same interface

### Negative

- **Code Duplication**: Some serialization logic repeated across backends
- **Feature Divergence**: SQLite has `list_sessions()` not in base interface
- **Error Handling**: Different backends have different failure modes
- **Migration**: No built-in migration between storage formats
- **Remote Dependency**: RemoteStorage requires HTTP client (httpx)
- **Transaction Boundaries**: Each operation is independent (no multi-operation transactions)

## Alternatives Considered

### Alternative 1: SQLAlchemy ORM

Use SQLAlchemy with async support for database operations.

**Rejected:**
- Heavy dependency for simple use case
- SQLite3 in stdlib is sufficient
- SQLAlchemy async adds complexity
- Current needs don't require ORM features
- Would need to support sync fallback for some deployments

### Alternative 2: Single Storage Backend

Only implement SQLite storage for all modes.

**Rejected:**
- Memory storage needed for testing
- JSON storage useful for simple deployments
- Remote storage required for HTTP mode scalability
- Different use cases need different trade-offs

### Alternative 3: No Abstraction Layer

Each mode implements its own storage directly.

**Rejected:**
- Code duplication across modes
- Harder to test (no mock interface)
- Switching backends requires code changes
- Violates DRY principle

### Alternative 4: Sync-First with Async Wrapper

Implement sync storage with async wrappers.

**Rejected:**
- Async-first matches the agent architecture
- File I/O benefits from async (using `asyncio.to_thread`)
- HTTP client is naturally async
- Consistent async interface throughout codebase

## Implementation Notes

### Dependencies

```toml
# Core dependencies (already in project)
# No additional dependencies for Memory, JSON, SQLite

# Remote storage only
httpx>=0.25.0              # HTTP client for remote storage
```

### Testing Strategy

```bash
# Run storage tests
pytest tests/storage/

# Run specific backend tests
pytest tests/storage/test_memory.py
pytest tests/storage/test_json.py
pytest tests/storage/test_sqlite.py
pytest tests/storage/test_remote.py

# Run with coverage
pytest tests/storage/ --cov=chat_shell_101.storage
```

**Test Categories:**
- Interface compliance tests (all backends must pass)
- Backend-specific behavior tests
- Async operation tests
- Error handling tests
- Concurrency tests (where applicable)

### Performance Considerations

- **MemoryStorage**: O(1) access, no I/O overhead
- **JSONStorage**: O(n) read/write, good for small histories (<1000 messages)
- **SQLiteStorage**: Indexed queries, scales to large histories
- **RemoteStorage**: Network latency dominates, connection pooling recommended

### Security Considerations

- File permissions should restrict access to storage files
- Remote storage should use HTTPS and API key authentication
- Session IDs should be unguessable (UUID recommended)
- SQLite databases should have proper file permissions (0600)

## References

- [Python Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [SQLite3 Documentation](https://docs.python.org/3/library/sqlite3.html)
- [HTTPX Async Client](https://www.python-httpx.org/async/)
- [Strategy Pattern](https://en.wikipedia.org/wiki/Strategy_pattern)
