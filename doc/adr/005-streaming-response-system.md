# ADR 005: Streaming Response System

## Status

Accepted

## Context

With the deployment modes (Epic 4) in place, the system needed a robust streaming infrastructure to deliver real-time LLM responses to clients. The existing SSE implementation in the API layer was tightly coupled to FastAPI and lacked several critical features needed for production use:

1. **Multi-client stream sharing**: Multiple clients connecting to the same stream (e.g., user has multiple tabs open)
2. **Stream recovery**: Reconnect and resume from where the client left off after network issues
3. **Event ordering**: Guaranteed in-order delivery of events with monotonic offsets
4. **Event buffering**: Temporary storage of events for late-joining clients and recovery
5. **Lifecycle management**: Proper handling of stream creation, completion, cancellation, and errors
6. **Resource cleanup**: Prevention of memory leaks from abandoned streams and client connections

Key requirements included:
- Token-level streaming from LLM to client with minimal latency
- Support for different event types (content, tool calls, thinking, errors, completion)
- Client disconnection without affecting other clients on the same stream
- Configurable buffering with size and age limits
- Cooperative cancellation that allows generators to clean up resources

## Decision

We implemented a dedicated streaming subsystem with clear separation of concerns across multiple components.

### 1. Event Model (Frozen Pydantic Models)

**Decision:** Use frozen Pydantic models for all stream events.

**Rationale:**
- Immutability ensures thread safety and prevents accidental mutation
- Pydantic provides validation, serialization, and JSON conversion
- Frozen models can be safely shared across async boundaries
- Type hints enable IDE autocomplete and static analysis
- `model_copy(update={...})` allows controlled modification when needed

**Event Hierarchy:**
```
BaseStreamEvent (abstract)
├── ChunkEvent          # Text content chunks
├── ToolStartEvent      # Tool execution start
├── ToolResultEvent     # Tool execution result
├── ThinkingEvent       # LLM thinking/reasoning
├── StreamOffsetEvent   # Offset checkpoint for recovery
├── ErrorEvent          # Stream error
├── CompleteEvent       # Stream completion
└── CancelledEvent      # Stream cancellation
```

**Key Design Points:**
```python
class BaseStreamEvent(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable
    offset: int                              # Monotonic sequence number
    session_id: str                          # Parent session
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChunkEvent(BaseStreamEvent):
    event_type: EventType = EventType.CHUNK
    text: str

# Usage with offset assignment
offset = context.session.get_next_offset()
event = event.model_copy(update={"offset": offset, "session_id": context.session_id})
```

**Location:** `chat_shell_101/streaming/events.py`

### 2. Stream State Management

**Decision:** Separate state tracking into `StreamingState` and `StreamSession` classes.

**Rationale:**
- Centralized state enables monitoring and debugging
- Session tracks offsets, status, and client associations
- State is separate from buffering (different concerns)
- Enables stats collection and health checks

**State Hierarchy:**
```
StreamingState (singleton per core)
├── stream_id -> StreamSession
│   ├── status: pending | running | completed | cancelled | error
│   ├── current_offset: int
│   ├── client_ids: Set[str]
│   ├── created_at: datetime
│   └── updated_at: datetime
└── client_id -> {stream_id, start_offset}
```

**Status Transitions:**
```
PENDING → RUNNING → COMPLETED
   ↓        ↓
   └────→ CANCELLED
   ↓        ↓
   └────→ ERROR
```

**Location:** `chat_shell_101/streaming/state.py`

### 3. Event Buffering

**Decision:** Implement per-stream ring buffer with configurable size and age limits.

**Rationale:**
- Ring buffer prevents unbounded memory growth
- Buffering enables late-joining clients to catch up
- Age-based eviction handles long-running streams
- Coverage tracking tells clients if recovery is possible

**Buffer Design:**
```python
class EventBuffer:
    def __init__(self, max_size: int = 10000, max_age_seconds: float = 3600):
        self._buffer: deque[BufferedEvent] = deque(maxlen=max_size)

    async def append(self, event: BaseStreamEvent):
        """Add event with automatic eviction of old events."""
        self._buffer.append(BufferedEvent(event=event, timestamp=now()))

    async def get_from_offset(self, offset: int) -> List[BaseStreamEvent]:
        """Get events from specific offset (for recovery)."""
        return [e.event for e in self._buffer if e.event.offset >= offset]

    async def get_buffer_coverage(self, offset: int) -> Dict[str, Any]:
        """Check if offset is recoverable from buffer."""
        # Returns can_recover, earliest_offset, latest_offset, etc.
```

**Buffer Coverage:**
```python
# Client wants to recover from offset 50
coverage = await buffer.get_buffer_coverage(50)
# Returns:
# {
#     "can_recover": True,
#     "requested_offset": 50,
#     "earliest_available": 45,
#     "latest_available": 100,
#     "events_available": 56
# }
```

**Location:** `chat_shell_101/streaming/buffer.py`

### 4. SSE Emitter

**Decision:** Dedicated `SSEEmitter` class handles all SSE formatting and client queues.

**Rationale:**
- Separation from core logic enables different transport protocols later
- Per-client queues isolate slow clients from fast ones
- Global sequence numbers enable debugging and ordering verification
- Heartbeat mechanism keeps connections alive through proxies

**Emitter Architecture:**
```
SSEEmitter
├── _clients: Dict[client_id, ClientConnection]
├── _stream_clients: Dict[stream_id, Set[client_id]]
├── _heartbeat_tasks: Dict[client_id, Task]
└── _global_sequence: int

ClientConnection
├── client_id: str
├── stream_id: str
├── queue: asyncio.Queue (maxsize=1000)
├── state: connecting | connected | disconnecting | disconnected | error
├── connected_at: datetime
├── last_activity: datetime
└── _disconnect_event: asyncio.Event
```

**SSE Format:**
```python
class SSEMessage:
    event: str      # Event type (chunk, tool_start, etc.)
    data: str       # JSON payload
    id: str         # Sequence number
    retry: int      # Reconnection hint (optional)

    def to_sse_format(self) -> str:
        return f"event: {self.event}\ndata: {self.data}\nid: {self.id}\n\n"
```

**Location:** `chat_shell_101/streaming/emitter.py`

### 5. Streaming Core (Central Coordinator)

**Decision:** `StreamingCore` orchestrates all components with explicit lifecycle management.

**Rationale:**
- Single entry point for all streaming operations
- Coordinates between state, buffer, and emitter
- Handles stream lifecycle (create → start → complete/cancel/error → cleanup)
- Provides recovery capabilities for disconnected clients

**Core Responsibilities:**
```python
class StreamingCore:
    # Lifecycle
    async def create_stream(...) -> StreamContext
    async def start_stream(stream_id, event_generator)
    async def cancel_stream(stream_id, reason)

    # Client management
    async def connect_client(stream_id, client_id, resume_from_offset) -> ClientConnection
    async def disconnect_client(client_id, stream_id)
    async def get_event_generator(client_id) -> AsyncGenerator[str, None]

    # Recovery
    async def get_recovery_info(stream_id, offset) -> Dict[str, Any]

    # Monitoring
    async def get_stream_status(stream_id) -> Dict[str, Any]
    async def get_stats() -> Dict[str, Any]
```

**Stream Processing:**
```python
async def _process_stream(self, context, event_generator):
    try:
        async for event in event_generator(context):
            # Check for cancellation
            if context.cancel_event.is_set():
                raise StreamCancelledError(...)

            # Assign offset (events are immutable)
            offset = context.session.get_next_offset()
            event = event.model_copy(update={"offset": offset, ...})

            # Buffer and emit
            await context.buffer.append(event)
            await self._emit_to_stream(stream_id, event)

        await self._complete_stream(stream_id)

    except StreamCancelledError:
        await self._cancel_stream(stream_id)
    except asyncio.CancelledError:
        await self._cancel_stream(stream_id)
    except Exception as e:
        await self._error_stream(stream_id, str(e))
```

**Location:** `chat_shell_101/streaming/core.py`

### 6. Cooperative Cancellation

**Decision:** Use `asyncio.Event` for cooperative cancellation with proper exception handling.

**Rationale:**
- `task.cancel()` raises `CancelledError` at next await point
- Generators can check `cancel_event.is_set()` to exit cleanly
- Distinguishes between external cancellation and internal errors
- Allows cleanup code to run before stream terminates

**Cancellation Flow:**
```python
# Client requests cancellation
await core.cancel_stream("stream-1", reason="User disconnected")

# Core sets event and cancels task
context.cancel_event.set()
task.cancel()

# Generator sees cancellation
async for event in event_generator(context):
    if context.cancel_event.is_set():
        raise StreamCancelledError(...)

# Core emits cancellation event to all clients
await self._emit_to_stream(stream_id, CancelledEvent(...))
```

**Location:** `chat_shell_101/streaming/core.py`, `chat_shell_101/streaming/exceptions.py`

### 7. Integration with Agent and API

**Decision:** Streaming core integrates with existing agent via adapter pattern.

**Rationale:**
- Agent remains unchanged (uses `astream()` for token-level streaming)
- Adapter converts agent output to streaming events
- API layer uses `get_event_generator()` for SSE response
- Clean separation between streaming infrastructure and business logic

**Integration Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI     │────▶│ StreamingCore│────▶│   Agent     │
│             │◄────│  /chat       │◄────│              │◄────│             │
└─────────────┘ SSE └──────────────┘     └──────────────┘     └─────────────┘
                           │                                           │
                           │                                           ▼
                           │                                    ┌─────────────┐
                           │                                    │    LLM      │
                           │                                    │  (streaming)│
                           │                                    └─────────────┘
                           ▼
                    ┌──────────────┐
                    │ Event Buffer │ (for recovery)
                    └──────────────┘
```

**Location:** `chat_shell_101/api/sse.py`, `chat_shell_101/agent/agent.py`

## Consequences

### Positive

- **True Token-Level Streaming**: LLM tokens flow directly to client with minimal buffering
- **Multi-Client Support**: Multiple clients can share the same stream efficiently
- **Stream Recovery**: Clients can reconnect and resume from where they left off
- **Event Ordering**: Monotonic offsets guarantee in-order delivery
- **Resource Safety**: Bounded buffers and periodic cleanup prevent memory leaks
- **Clean Cancellation**: Cooperative cancellation allows proper resource cleanup
- **Immutability**: Frozen event models prevent bugs from accidental mutation
- **Separation of Concerns**: Each component has a single, well-defined responsibility
- **Testability**: Components can be tested in isolation with mocked dependencies

### Negative

- **Memory Overhead**: Per-stream buffers consume memory (configurable limits)
- **Complexity**: Multiple components increase cognitive load
- **Latency**: Buffering adds slight latency for recovery capability
- **Offset Management**: Developers must understand offset assignment
- **Lock Contention**: Async locks may become bottleneck under extreme load
- **Debugging**: Distributed state across components harder to debug

## Alternatives Considered

### Alternative 1: WebSockets Instead of SSE

Use WebSockets for bidirectional streaming.

**Rejected:**
- SSE is simpler for server-to-client streaming
- WebSockets require more complex client handling
- SSE works better with HTTP infrastructure (load balancers, proxies)
- No need for client-to-server streaming in our use case
- SSE has automatic reconnection support

### Alternative 2: No Buffering (Direct Passthrough)

Stream directly from agent to client without buffering.

**Rejected:**
- No recovery capability for disconnected clients
- Late-joining clients would miss earlier events
- Harder to implement multi-client sharing
- Buffering overhead is minimal with configurable limits

### Alternative 3: Global Event Bus (Pub/Sub)

Use a pub/sub pattern with channels instead of direct emission.

**Rejected:**
- Adds complexity for single-server deployment
- Redis or message broker required for multi-instance
- Direct emission is simpler and lower latency
- Can be extended to pub/sub later if needed

### Alternative 4: Mutable Events with Locks

Use mutable events with locks for thread safety.

**Rejected:**
- Locks are error-prone (deadlocks, forgotten unlocks)
- Frozen models enforce safety at the type level
- `model_copy()` is explicit about creating new versions
- Easier to reason about immutable data flow

### Alternative 5: Per-Client Buffering

Each client has their own buffer instead of per-stream.

**Rejected:**
- Memory overhead scales with clients, not streams
- Duplicates same events across multiple buffers
- Per-stream buffering is more memory efficient
- Recovery is about stream position, not client state

## Implementation Notes

### Dependencies

```toml
# Core dependencies for Epic 5 (already in project)
pydantic>=2.0.0           # Frozen models and validation
sse-starlette>=1.6.5      # SSE support (from Epic 4)
```

### Configuration

```python
@dataclass
class StreamConfig:
    buffer_size: int = 10000              # Max events per stream
    buffer_age_seconds: float = 3600      # Max age of buffered events
    enable_recovery: bool = True          # Support stream recovery
    emit_checkpoints: bool = True         # Emit offset checkpoints
    checkpoint_interval: int = 100        # Events between checkpoints
    heartbeat_interval: float = 30.0      # Seconds between heartbeats
    max_concurrent_clients: int = 100     # Max clients per stream
```

### Testing Strategy

```bash
# Run Epic 5 specific tests
pytest tests/ -m "epic_5"

# Run streaming tests only
pytest tests/streaming/

# Run with coverage
pytest tests/streaming/ --cov=chat_shell_101.streaming
```

**Test Categories:**
- Unit tests for each component (events, state, buffer, emitter, core)
- Integration tests for full stream lifecycle
- Recovery tests for reconnection scenarios
- Cancellation tests for proper cleanup
- Multi-client tests for concurrent access

### Performance Considerations

- **Buffer Size**: Default 10,000 events ≈ 10-50MB per stream (depending on content)
- **Offset Assignment**: Single atomic increment per event (fast)
- **Event Emission**: Async queue put (non-blocking with backpressure)
- **Cleanup**: Background task runs every 60 seconds

### Security Considerations

- Buffer limits prevent memory exhaustion attacks
- Client authentication should happen before stream connection
- Stream IDs should be unguessable (UUID recommended)
- Sensitive data in buffers should have TTL

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Streaming Response](https://fastapi.tiangolo.com/advanced/custom-response/)
