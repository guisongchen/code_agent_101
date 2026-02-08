# ADR 017: Real-time Event Broadcasting

## Status

Accepted

## Context

With the WebSocket chat endpoint (Epic 14) and session management (Epic 16) in place, the system needs a robust mechanism for broadcasting events to connected clients. Key requirements:

1. **Multi-user scenarios**: Multiple users may be connected to the same task
2. **Personal notifications**: Users need notifications about their tasks
3. **Event routing**: Events should reach the right clients efficiently
4. **Scalability**: Support for horizontal scaling (future)
5. **Task lifecycle visibility**: Real-time updates on task status changes

Challenges:
- How to route events to the right set of clients?
- How to handle users with multiple connected devices/tabs?
- How to broadcast task events to interested parties?
- How to support future multi-instance deployment?

## Decision

### 1. Dual Room Architecture

**Decision:** Implement separate room managers for task rooms and user rooms

**Rationale:**
- Task rooms group clients watching the same task chat
- User rooms group all connections belonging to the same user
- Clean separation of concerns enables targeted broadcasting
- Simplifies event routing logic

**Implementation:**
```python
# TaskRoomManager - existing, for task-based chat
class TaskRoomManager:
    async def join_task(task_id, websocket)
    async def broadcast_to_task(task_id, message)

# UserRoomManager - new, for personal notifications
class UserRoomManager:
    async def join_user(user_id, websocket)
    async def broadcast_to_user(user_id, message)
```

**Location:**
- `backend/websocket/manager.py` (TaskRoomManager)
- `backend/websocket/user_room_manager.py` (UserRoomManager)

### 2. Event Bus Pattern

**Decision:** Create an EventBus for pub/sub event distribution

**Rationale:**
- Decouples event producers from consumers
- Supports both local and distributed (Redis) broadcasting
- Enables subscription-based event handling
- Provides clean API for publishing events

**Implementation:**
```python
class EventBus:
    def subscribe(event_type, callback)
    async def publish(event_type, data, room_id=None)
    async def publish_to_task(task_id, event_type, data)
    async def publish_to_user(user_id, event_type, data)
```

**Location:** `backend/websocket/event_bus.py`

### 3. Task Event Broadcasting

**Decision:** Create TaskEventBroadcaster for task lifecycle events

**Rationale:**
- Encapsulates task event broadcasting logic
- Broadcasts to both task rooms and user rooms
- Provides semantic methods for each event type
- Integrates with Task API endpoints

**Event Types:**
```python
EVENT_TASK_CREATED = "task:created"
EVENT_TASK_STARTED = "task:started"
EVENT_TASK_COMPLETED = "task:completed"
EVENT_TASK_FAILED = "task:failed"
EVENT_TASK_CANCELLED = "task:cancelled"
EVENT_TASK_STATUS_CHANGED = "task:status"
EVENT_TASK_DELETED = "task:deleted"
```

**Location:** `backend/websocket/task_events.py`

### 4. WebSocket Integration

**Decision:** Integrate user rooms into WebSocket connection lifecycle

**Rationale:**
- Clients automatically join their user room on connection
- Clean disconnection handling removes from all rooms
- User room enables personal notifications

**Implementation:**
```python
# In chat WebSocket endpoint
await room_manager.join_task(task_id, websocket)
await user_room_manager.join_user(user.id, websocket)

# On disconnect
await room_manager.leave_task(task_id, websocket)
await user_room_manager.leave_user(user.id, websocket)
```

**Location:** `backend/api/v1/chat_ws.py`

### 5. User Notification WebSocket Endpoint

**Decision:** Create dedicated WebSocket endpoint for user notifications

**Rationale:**
- Clients can connect just for notifications without joining a task
- Lightweight connection for mobile apps and background tabs
- Separate from chat WebSocket for cleaner architecture

**Implementation:**
```python
@router.websocket("/user/notifications")
async def user_notifications_websocket(websocket, token):
    # Authenticate and join user room
    await user_room_manager.join_user(user.id, websocket)
    # Handle ping/pong and disconnection
```

**Location:** `backend/api/v1/user_ws.py`

## Consequences

### Positive

- **Targeted broadcasting**: Events reach only interested clients
- **Multi-device support**: User rooms enable notifications across all devices
- **Clean architecture**: Separation between task and user concerns
- **Extensibility**: EventBus pattern supports future Redis integration
- **Real-time updates**: Task status changes propagate immediately

### Negative

- **Memory usage**: Room managers maintain in-memory state
- **Complexity**: Multiple room types increase system complexity
- **No persistence**: Events not delivered to offline users (no message queue)
- **Single-instance**: Current implementation limited to single server

## Alternatives Considered

### Alternative 1: Single Room Manager

**Description:** Use one room manager with composite keys (e.g., `task:{id}`, `user:{id}`)

**Rejected:**
- Would complicate room lookup logic
- Less type-safe
- Harder to implement room-specific features

### Alternative 2: Redis-First Architecture

**Description:** Use Redis pub/sub as primary broadcasting mechanism

**Rejected:**
- Adds infrastructure dependency
- Higher latency for local broadcasts
- Can be added later as optimization

### Alternative 3: SSE (Server-Sent Events)

**Description:** Use SSE instead of WebSockets for one-way broadcasting

**Rejected:**
- WebSocket already established for chat
- SSE doesn't support binary data well
- WebSocket enables bidirectional communication

## Implementation Notes

### Room ID Format

```
task:{uuid}    # Task rooms for chat streaming
user:{int}     # User rooms for personal notifications
```

### Event Flow

```
Task API -> TaskEventBroadcaster -> EventBus -> Room Managers -> WebSockets
```

### Testing Strategy

```bash
# Run WebSocket tests
pytest tests/unit/crd_backend/websocket/ -v

# Run specific test files
pytest tests/unit/crd_backend/websocket/test_event_bus.py -v
pytest tests/unit/crd_backend/websocket/test_user_room_manager.py -v
```

**Test Coverage:** 26 tests covering:
- EventBus subscription and publishing
- User room management
- Task room broadcasting
- Multi-client scenarios

## Future Considerations

### Redis Integration

For horizontal scaling, the EventBus can be extended:

```python
class RedisEventBus(EventBus):
    async def publish(self, event_type, data, room_id=None):
        # Publish to Redis channel
        await self.redis.publish(f"room:{room_id}", json.dumps(event))
```

### Message Persistence

For offline user support, consider:
- Persisting notifications to database
- Delivering missed events on reconnection
- Implementing acknowledgment mechanism

## References

- [Epic 17 Specification](../epic/backend_phase_2_chat_execution.md)
- [WebSocket Chat ADR](014-websocket-chat-endpoint.md)
- [Session Management ADR](016-chat-session-state-management.md)
- FastAPI WebSocket Documentation: https://fastapi.tiangolo.com/advanced/websockets/
