# ADR 014: WebSocket Chat Endpoint

## Status

Accepted

## Context

With the ChatService implemented (Epic 13) providing chat execution capabilities, we needed to enable real-time bidirectional communication for chat interactions (Epic 14). The requirements included:

1. **Real-time streaming**: AI responses should stream to clients as they're generated, not wait for completion
2. **Bidirectional communication**: Clients need to send messages and receive responses in the same connection
3. **Multi-client support**: Multiple users should be able to observe or participate in the same task chat
4. **Event-based protocol**: Clear event types for different chat lifecycle stages (start, chunk, done, error)
5. **Authentication**: WebSocket connections must be authenticated like REST API endpoints
6. **Cancellation support**: Users should be able to cancel ongoing AI generation

Key questions to resolve:
- Native FastAPI WebSocket vs Socket.IO - which to use?
- How to structure the event protocol?
- How to handle multiple clients in the same task room?
- How to bridge chat_shell's async generator to WebSocket?
- How to authenticate WebSocket connections?

## Decision

We implemented native FastAPI WebSockets with a room-based architecture for multi-client support.

### 1. Native FastAPI WebSocket (Not Socket.IO)

**Decision:** Use native FastAPI WebSocket instead of Socket.IO.

**Rationale:**
- Simpler implementation with fewer dependencies
- Direct integration with FastAPI's dependency injection
- Sufficient for current use case (no need for automatic reconnection yet)
- Easier to test with standard HTTP client libraries
- Can migrate to Socket.IO later if needed (Redis adapter for multi-worker)

**Implementation:**
```python
@router.websocket("/tasks/{task_id}/chat")
async def task_chat_websocket(
    websocket: WebSocket,
    task_id: UUID,
    token: Optional[str] = Query(None),
):
    await websocket.accept()
    # ... handle connection
```

**Location:** `backend/api/v1/chat_ws.py`

### 2. Room-Based Architecture

**Decision:** Implement TaskRoomManager for room-based message routing.

**Rationale:**
- Multiple clients can connect to the same task chat
- Broadcast messages to all observers
- Clean separation of connection management from business logic
- Thread-safe with asyncio locks

**Implementation:**
```python
class TaskRoomManager:
    def __init__(self):
        self._rooms: Dict[UUID, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def join_task(self, task_id: UUID, websocket: WebSocket):
        async with self._lock:
            if task_id not in self._rooms:
                self._rooms[task_id] = set()
            self._rooms[task_id].add(websocket)

    async def broadcast_to_task(
        self, task_id: UUID, message: Dict, exclude: Optional[WebSocket] = None
    ):
        for ws in self._rooms.get(task_id, set()):
            if ws != exclude:
                await ws.send_json(message)
```

**Location:** `backend/websocket/manager.py`

### 3. Event Protocol Design

**Decision:** Define clear event types for client→server and server→client communication.

**Rationale:**
- Explicit event types make the protocol self-documenting
- Easy to extend with new event types
- Matches chat_shell's event-based streaming model
- Separates concerns (chat events vs task events vs control events)

**Client → Server Events:**
| Event | Purpose |
|-------|---------|
| `chat:send` | Send a message to the AI |
| `chat:cancel` | Cancel ongoing generation |
| `task:join` | Join task room (implicit) |
| `task:leave` | Leave task room |
| `ping` | Keep-alive |

**Server → Client Events:**
| Event | Purpose |
|-------|---------|
| `chat:start` | AI started generating |
| `chat:chunk` | Streaming content chunk |
| `chat:done` | AI response completed |
| `chat:error` | Error occurred |
| `chat:cancelled` | Generation was cancelled |
| `chat:tool_start` | Tool execution started |
| `chat:tool_result` | Tool execution completed |
| `chat:thinking` | Agent thinking/thoughts |
| `task:status` | Task status update |
| `pong` | Keep-alive response |

**Implementation:**
```python
# Client sends
{"type": "chat:send", "message": "Hello!", "show_thinking": true}

# Server responds with sequence
{"type": "chat:start", "timestamp": "..."}
{"type": "chat:chunk", "data": {"text": "Hello"}}
{"type": "chat:chunk", "data": {"text": " there!"}}
{"type": "chat:done", "timestamp": "..."}
```

**Location:** `backend/schemas/websocket.py`

### 4. Async Generator Bridge

**Decision:** Bridge chat_shell's async generator to WebSocket by iterating and sending events.

**Rationale:**
- chat_shell already provides streaming via async generator
- WebSocket can send events as they arrive
- No need to buffer entire response
- Natural fit for both technologies

**Implementation:**
```python
async for event in chat_service.execute_chat(
    bot_name=bot_name,
    messages=messages,
    namespace=namespace,
    thread_id=thread_id,
):
    ws_event = _map_event_to_websocket(event)
    if ws_event:
        await room_manager.broadcast_to_task(task_id, ws_event)
```

**Event Mapping:**
```python
def _map_event_to_websocket(event: Dict) -> Optional[Dict]:
    event_type = event.get("type")
    if event_type == "content":
        return {"type": "chat:chunk", "data": {"text": event["data"]["text"]}}
    elif event_type == "tool_call":
        return {"type": "chat:tool_start", "data": {...}}
    # ... etc
```

**Location:** `backend/api/v1/chat_ws.py:270-320`

### 5. WebSocket Authentication

**Decision:** Authenticate WebSocket connections using JWT tokens passed via query parameter.

**Rationale:**
- WebSocket headers are limited and not all clients support custom headers
- Query parameter is widely supported by WebSocket clients
- Reuses existing JWT authentication from REST API
- Token can be refreshed without reconnecting (future enhancement)

**Implementation:**
```python
async def authenticate_ws_token(token: Optional[str]) -> Optional[CurrentUser]:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    # ... lookup user
    return CurrentUser(...)

# In WebSocket endpoint
user = await authenticate_websocket(websocket, token)
if not user:
    await websocket.close(code=4001, reason="Unauthorized")
    return
```

**Alternative considered:** Cookie-based authentication - rejected because it requires same-origin and complicates cross-domain deployments.

**Location:** `backend/websocket/auth.py`

### 6. Cancellation Support

**Decision:** Support cancellation of ongoing AI generation via asyncio.Task cancellation.

**Rationale:**
- Users should be able to stop long-running generations
- chat_shell supports cancellation via asyncio
- Clean up resources properly on cancellation
- Notify all connected clients of cancellation

**Implementation:**
```python
# Track active generation
active_generation: Optional[asyncio.Task] = None

# On chat:send, start new generation
active_generation = asyncio.create_task(
    _handle_chat_send(...)
)

# On chat:cancel, cancel it
if active_generation and not active_generation.done():
    active_generation.cancel()
    await room_manager.broadcast_to_task(
        task_id,
        {"type": "chat:cancelled", "data": {"reason": "User cancelled"}}
    )
```

**Location:** `backend/api/v1/chat_ws.py:120-140`

## Consequences

### Positive

- **Real-time streaming**: AI responses stream immediately without buffering
- **Multi-client support**: Multiple users can observe the same chat session
- **Clean protocol**: Explicit event types make debugging easier
- **Authentication**: Secure connections with JWT tokens
- **Cancellation**: Users can stop unwanted generations
- **Scalable architecture**: Room manager can be extended with Redis for multi-worker
- **Testable**: Room manager is easily unit tested

### Negative

- **No automatic reconnection**: Native WebSocket doesn't handle reconnection (can add Socket.IO later)
- **No built-in presence**: Need to track client presence manually
- **Single-server rooms**: Room manager is in-memory; multi-worker requires Redis
- **Connection limits**: Need to handle max connections per task (not implemented yet)
- **Message history**: WebSocket only handles real-time; history is separate concern

## Alternatives Considered

### Alternative 1: Socket.IO

Use python-socketio with Redis adapter for multi-worker support.

**Rejected:**
- Adds complexity (additional dependency, event handlers)
- Not needed for initial implementation
- Can migrate later if multi-worker broadcasting needed
- Native WebSocket sufficient for current requirements

### Alternative 2: SSE (Server-Sent Events)

Use SSE for server→client and HTTP POST for client→server.

**Rejected:**
- Requires two connections (SSE + HTTP)
- More complex client logic
- WebSocket provides cleaner bidirectional abstraction
- SSE has connection limits in some browsers

### Alternative 3: GraphQL Subscriptions

Use GraphQL with subscriptions for real-time updates.

**Rejected:**
- Overkill for simple chat protocol
- Adds GraphQL complexity
- Not aligned with existing REST API architecture
- Would require significant client changes

### Alternative 4: gRPC Streaming

Use gRPC with bidirectional streaming.

**Rejected:**
- HTTP/2 requirement complicates deployment
- Not browser-friendly without proxy
- Overkill for simple chat use case
- Would require protobuf definitions

## Implementation Notes

### Dependencies

No new dependencies - uses FastAPI's built-in WebSocket support:
```toml
[project.dependencies]
fastapi>=0.100.0  # Already included
```

Optional future dependency:
```toml
python-socketio[asyncio]>=5.9.0  # For future Socket.IO migration
```

### Testing Strategy

```bash
# Run WebSocket tests
pytest tests/unit/crd_backend/websocket/ -v

# Run by epic marker
pytest tests/ -m epic_14 -v

# Total: 11 room management tests
```

**Test Categories:**
- Room creation and joining (3 tests)
- Room leaving and cleanup (2 tests)
- Broadcasting messages (2 tests)
- Client counting (2 tests)
- Room info queries (2 tests)

### WebSocket URL

```
ws://localhost:8000/api/v1/tasks/{task_id}/chat?token=JWT_TOKEN
```

### Connection Flow

```
1. Client connects to WebSocket with JWT token
2. Server authenticates token
3. Server verifies task exists
4. Client joins task room
5. Client sends chat:send event
6. Server broadcasts chat:start
7. Server streams chat:chunk events
8. Server broadcasts chat:done
9. Client can send chat:cancel to interrupt
10. Client disconnects or sends task:leave
```

### Migration Path to Socket.IO

If multi-worker broadcasting becomes needed:

1. Add `python-socketio` dependency
2. Create Socket.IO server alongside FastAPI
3. Replace TaskRoomManager with Socket.IO rooms
4. Add Redis adapter for cross-worker communication
5. Keep same event protocol for client compatibility

```python
# Future Socket.IO implementation
import socketio

sio = socketio.AsyncServer(async_mode='asgi')

@sio.on('chat:send')
async def handle_chat_send(sid, data):
    # Same logic, different transport
    await sio.emit('chat:start', room=data['task_id'])
```

## References

- [Epic 14: WebSocket Chat Endpoint](/doc/epic/backend_phase_2_chat_execution.md)
- [ADR 013: Chat Shell Integration](/doc/adr/013-chat-shell-integration.md)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Socket.IO Documentation](https://socket.io/docs/v4/)
