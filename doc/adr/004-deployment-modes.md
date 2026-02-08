# ADR 004: Three Deployment Modes

## Status

Accepted

## Context

With the core agent system (Epic 1), multi-model support (Epic 2), and tools system (Epic 3) in place, the system needed flexible deployment options to serve different use cases:

1. **HTTP Mode**: For integration with backend services, web applications, and multi-user scenarios
2. **Package Mode**: For embedding as a Python library in other applications
3. **Enhanced CLI Mode**: For direct command-line usage with persistent storage

Key requirements included:
- HTTP API with streaming responses (SSE)
- Python library interface without HTTP overhead
- SQLite storage for local persistence
- Remote storage for backend integration
- Multiple CLI commands (serve, query, history, config)

## Decision

We implemented three distinct deployment modes with shared core logic but different interfaces and storage backends.

### 1. HTTP Mode (FastAPI)

**Decision:** Use FastAPI with Server-Sent Events (SSE) for streaming HTTP API.

**Rationale:**
- FastAPI provides automatic OpenAPI documentation and request validation
- SSE enables real-time streaming without WebSocket complexity
- Pydantic models ensure type safety across API boundaries
- Uvicorn provides high-performance async server
- Native async support aligns with agent architecture

**API Architecture:**
```
┌──────────────┐      POST /v1/response       ┌──────────────┐
│   Client     │ ────────────────────────────▶ │              │
│              │     (ChatRequest JSON)       │   FastAPI    │
│              │                              │   Server     │
│              │ ◄─────────────────────────── │              │
│              │     SSE stream (ChatEvent)   │              │
└──────────────┘                              └──────┬───────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │  ChatAgent   │
                                              │  (shared)    │
                                              └──────────────┘
```

**Endpoints:**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /v1/response | Start chat session (SSE streaming) |
| GET | /v1/response/{subtask_id} | Get session status |
| DELETE | /v1/response/{subtask_id} | Cancel session |
| GET | /v1/health | Health check |
| GET | /v1/sessions/{id}/history | Get session history |

**Schema Design:**
```python
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str]
    model: Optional[str]
    temperature: float = 0.7
    stream: bool = True

class ChatEvent(BaseModel):
    event_type: Literal["content", "tool_call", "tool_result", "thinking", "error", "complete"]
    data: Dict[str, Any]
    timestamp: datetime
```

**Streaming Implementation:**
```python
async def event_generator():
    async for event in stream_chat_events(agent, messages, session_id):
        yield {
            "event": event.event_type,
            "data": event.model_dump(),
        }

return EventSourceResponse(event_generator())
```

**Location:** `chat_shell_101/api/{app.py,routes.py,schemas.py,sse.py,dependencies.py}`

### 2. Package Mode (Python Library)

**Decision:** Create abstract `ChatInterface` with `DirectChatInterface` implementation.

**Rationale:**
- Abstract interface allows different implementations (in-memory, persistent, remote)
- Direct implementation bypasses HTTP/serialization overhead
- In-memory session storage for stateful conversations
- Both streaming and non-streaming APIs
- Clean separation from HTTP concerns

**Interface Design:**
```python
class ChatInterface(ABC):
    @abstractmethod
    async def chat(self, input_data: Union[str, ChatInput]) -> ChatOutput:
        """Non-streaming chat."""
        pass

    @abstractmethod
    async def stream_chat(self, input_data) -> AsyncGenerator[StreamingChatOutput, None]:
        """Streaming chat."""
        pass

    @abstractmethod
    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get session history."""
        pass
```

**Usage Pattern:**
```python
from chat_shell_101.package import DirectChatInterface, InterfaceConfig

config = InterfaceConfig(model="gpt-4", temperature=0.7)
interface = DirectChatInterface(config)

await interface.initialize()

# Non-streaming
result = await interface.chat("Hello!")
print(result.content)

# Streaming
async for chunk in interface.stream_chat("Tell me a story"):
    print(chunk.chunk, end="")

await interface.shutdown()
```

**Key Design Points:**
- Session management without external storage (in-memory dict)
- Message context building from session history or explicit context
- Automatic session ID generation (UUID)
- Tool calls tracked in response metadata

**Location:** `chat_shell_101/package/{__init__.py,interface.py}`

### 3. Enhanced CLI Mode

**Decision:** Extend CLI with multiple subcommands and SQLite storage.

**Rationale:**
- Single CLI entry point for all operations
- SQLite provides local persistence without server setup
- Rich command set for different use cases
- Consistent with modern CLI tools (git, docker, etc.)

**Command Structure:**
```
chat-shell
├── chat [options]          # Interactive session (existing)
├── serve [options]         # Start HTTP server
├── query [options] <msg>   # Single query
├── history [options]       # View history
└── config
    ├── show                # Display config
    ├── set <key> <val>     # Set config value
    └── init [path]         # Initialize config directory
```

**Storage Integration:**
```python
# CLI now supports SQLite
chat-shell chat --storage sqlite

# History command uses SQLite by default
chat-shell history --storage sqlite --limit 20
```

**SQLite Storage Features:**
- Sessions table for metadata
- Messages table with foreign key constraints
- Indexed for fast retrieval by session
- Ordered by timestamp for chronological history
- List sessions capability (not in base interface)

**Implementation:**
```python
class SQLiteHistoryStorage(HistoryStorage):
    async def list_sessions(self) -> List[str]:
        """List all session IDs ordered by updated_at."""
        # Uses asyncio.to_thread for sync sqlite3
```

**Location:** `chat_shell_101/cli.py`, `chat_shell_101/storage/sqlite_storage.py`

### 4. Storage Abstraction

**Decision:** Implement storage provider pattern with multiple backends.

**Rationale:**
- Different deployment modes need different storage
- Common interface enables switching backends
- Async interface matches agent architecture
- SQLite for local, Remote for HTTP mode, Memory for testing

**Storage Hierarchy:**
```
StorageProvider (abstract)
├── MemoryStorage       # In-memory, for testing
├── JSONStorage         # File-based JSON
├── SQLiteStorage       # Local SQLite database
└── RemoteStorage       # HTTP API backend

HistoryStorage (abstract)
├── MemoryHistoryStorage
├── JSONHistoryStorage
├── SQLiteHistoryStorage    # + list_sessions()
└── RemoteHistoryStorage
```

**SQLite Schema:**
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Async Pattern:**
```python
# Uses standard library sqlite3 with asyncio.to_thread
def _get_connection(self) -> sqlite3.Connection:
    conn = sqlite3.connect(str(self.db_path))
    conn.row_factory = sqlite3.Row
    return conn

async def get_history(self, session_id: str) -> List[Message]:
    return await asyncio.to_thread(self._get_history_sync, session_id)
```

**Location:** `chat_shell_101/storage/{sqlite_storage.py,remote_storage.py}`

### 5. Deployment Mode Configuration

**Decision:** Use dependencies and imports to differentiate modes, not runtime configuration.

**Rationale:**
- Each mode has distinct dependencies (FastAPI only needed for HTTP)
- Clear separation of concerns
- No runtime overhead from unused modes
- Type safety and IDE support

**Mode Selection:**
| Mode | Entry Point | Key Dependencies |
|------|-------------|------------------|
| HTTP | `chat-shell serve` or `uvicorn` | fastapi, uvicorn, sse-starlette |
| Package | `from chat_shell_101.package import ...` | (core only) |
| CLI | `chat-shell chat|query|history|config` | click, sqlite3 |

## Consequences

### Positive

- **Flexibility**: Three modes serve different use cases effectively
- **Shared Core**: All modes use the same ChatAgent, tools, and models
- **Performance**: Package mode has no HTTP/serialization overhead
- **Persistence**: SQLite provides durable local storage
- **Scalability**: HTTP mode can serve multiple clients
- **Testing**: Memory storage enables fast unit tests
- **Standards**: FastAPI provides OpenAPI docs, SSE is standard HTTP

### Negative

- **Dependency Bloat**: FastAPI/uvicorn only needed for HTTP mode but in main dependencies
- **Code Duplication**: Some overlap between CLI and Package interfaces
- **Testing Complexity**: Three modes require three test suites
- **Documentation**: More complex to document three different usage patterns
- **Storage Limitations**: SQLite doesn't work well for multi-instance deployments

## Alternatives Considered

### Alternative 1: Single HTTP Mode Only

Only provide HTTP API, use it for CLI via local requests.

**Rejected:**
- HTTP overhead unnecessary for local CLI usage
- Requires server running for CLI
- More complex setup for simple use cases
- SQLite wouldn't be possible for storage

### Alternative 2: No Package Mode

Only CLI and HTTP, no direct Python API.

**Rejected:**
- Embedding in applications requires HTTP client
- Python users expect library interface
- Harder to extend/customize
- Testing requires HTTP mocking

### Alternative 3: Asyncio TCP Server Instead of HTTP

Custom TCP protocol with asyncio for streaming.

**Rejected:**
- No automatic documentation like OpenAPI
- Harder to integrate with web apps
- Need custom client libraries
- Less standard than HTTP/SSE

### Alternative 4: SQLAlchemy for Database

Use SQLAlchemy ORM for database abstraction.

**Rejected:**
- Heavy dependency for simple use case
- SQLite3 in stdlib is sufficient
- SQLAlchemy async adds complexity
- Current needs don't require ORM features

## Implementation Notes

### Dependencies

```toml
# Core dependencies for Epic 4
fastapi>=0.104.0           # HTTP API framework
uvicorn[standard]>=0.24.0  # ASGI server
sse-starlette>=1.6.5       # Server-Sent Events

# Note: sqlite3 is in standard library
```

### Testing Strategy

- Unit tests for each storage backend
- API schema validation tests
- Package interface mocking tests
- CLI command tests (optional due to click testing complexity)

```bash
# Run Epic 4 specific tests
pytest tests/ -m "epic_4"

# Run storage tests
pytest tests/storage/

# Run API tests
pytest tests/api/

# Run package tests
pytest tests/package/
```

### Security Considerations

- HTTP mode needs authentication for production
- File paths in storage should be sandboxed
- SQLite databases should have proper permissions
- Remote storage needs TLS and API key management

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Click Documentation](https://click.palletsprojects.com/)
- [SQLite3 Documentation](https://docs.python.org/3/library/sqlite3.html)
