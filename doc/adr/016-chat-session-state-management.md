# ADR 016: Chat Session State Management

## Status

Accepted

## Context

The WebSocket chat endpoint (Epic 14) enables real-time bidirectional communication between clients and AI agents. However, several challenges arise when managing long-lived connections:

1. **Connection instability**: Clients may disconnect due to network issues, browser refreshes, or mobile app backgrounding
2. **Concurrent usage**: Users may have multiple tabs or devices connected simultaneously
3. **Resource management**: Sessions consume server resources and need lifecycle management
4. **State recovery**: Users expect to resume conversations after disconnection
5. **Security**: Sessions need expiration and limits to prevent abuse

Requirements:
- Session creation on first WebSocket connection
- Recovery mechanism for reconnecting clients
- 2-hour session timeout with configurable expiration
- Maximum 5 concurrent sessions per user
- Graceful cleanup on disconnect
- Session metrics for monitoring

## Decision

### 1. Session Model Design

**Decision:** Create a `ChatSession` SQLAlchemy model with lifecycle state machine

**Rationale:**
- Database persistence enables recovery across server restarts
- State machine (ACTIVE, EXPIRED, CLOSED, RECOVERED) provides clear lifecycle
- Recovery tokens enable secure session resumption
- Connection counting tracks active WebSocket associations

**Schema:**
```python
class SessionStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"
    RECOVERED = "recovered"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(unique=True, index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    task_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tasks.id"))
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus))
    connection_count: Mapped[int] = mapped_column(default=1)
    recovery_token: Mapped[str] = mapped_column(unique=True, index=True)
    expires_at: Mapped[datetime]
    recovered_from_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("chat_sessions.id"))
```

**Location:** `backend/models/session.py`

### 2. Session Service Layer

**Decision:** Implement `SessionService` for CRUD operations and lifecycle management

**Rationale:**
- Centralized business logic for session operations
- Concurrent session limit enforcement
- Recovery token validation
- Metrics aggregation

**Key Methods:**
```python
class SessionService:
    MAX_SESSIONS_PER_USER = 5
    DEFAULT_EXPIRY_HOURS = 2

    async def create(self, request: SessionCreateRequest) -> SessionResponse
    async def recover_session(self, request: SessionRecoveryRequest) -> SessionRecoveryResponse
    async def increment_connections(self, session_id: str) -> Optional[SessionResponse]
    async def decrement_connections(self, session_id: str) -> Optional[SessionResponse]
    async def cleanup_expired_sessions(self) -> int
    async def get_metrics(self) -> SessionMetrics
```

**Location:** `backend/services/session.py`

### 3. In-Memory Session Tracking

**Decision:** Create `SessionManager` for WebSocket association tracking

**Rationale:**
- Fast in-memory lookups for WebSocket routing
- Tracks connection count per session
- Enables broadcasting to all connections of a session
- Background cleanup task for expired sessions

**Implementation:**
```python
class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._user_sessions: Dict[int, Set[str]] = {}
        self._websocket_sessions: Dict[str, str] = {}

    async def create_session(self, session_id: str, user_id: int, ...) -> SessionState
    async def associate_websocket(self, session_id: str, websocket_id: str)
    async def disassociate_websocket(self, websocket_id: str)
```

**Location:** `backend/websocket/session_manager.py`

### 4. WebSocket Integration

**Decision:** Integrate session management into WebSocket endpoint lifecycle

**Rationale:**
- Session created on WebSocket connection accept
- Recovery token sent to client for reconnection
- Connection count incremented/decremented on join/leave
- Session closed when last connection disconnects

**Flow:**
```python
# On connect
session = await session_service.create(session_request)
await session_manager.create_session(session_id=session.session_id, ...)
await websocket.send_json({
    "type": "session:state",
    "session_id": session_id,
    "recovery_token": session.recovery_token,
})

# On disconnect
await session_manager.disassociate_websocket(websocket_id)
await session_service.decrement_connections(session_id)
```

**Location:** `backend/api/v1/chat_ws.py`

### 5. Recovery Mechanism

**Decision:** Implement session recovery using opaque recovery tokens

**Rationale:**
- Tokens are cryptographically random (secrets.token_urlsafe)
- Old session marked as RECOVERED, new session created
- Maintains audit trail via `recovered_from_id` relationship
- Prevents replay attacks (token valid only once)

**Recovery Flow:**
1. Client sends `session:recover` event with token
2. Server validates token and checks old session status
3. Old session marked as RECOVERED
4. New session created with link to old session
5. New recovery token returned to client

**Location:** `backend/services/session.py:recover_session()`

## Consequences

### Positive

- **Resilient connections**: Clients can recover sessions after network interruptions
- **Resource protection**: Session limits prevent abuse and resource exhaustion
- **Clear lifecycle**: State machine makes session behavior predictable
- **Auditability**: Recovery chain tracks session lineage
- **Monitoring**: Metrics enable operational visibility

### Negative

- **Database overhead**: Session state persisted to database on every connection change
- **Token management**: Recovery tokens must be stored securely by clients
- **Complexity**: Two-layer tracking (DB + in-memory) adds implementation complexity
- **Cleanup responsibility**: Expired sessions require periodic cleanup jobs

## Alternatives Considered

### Alternative 1: Pure Redis Session Storage

**Description:** Store all session state in Redis with TTL

**Rejected:**
- Session history would be lost on Redis restart
- Harder to implement session recovery audit trail
- Requires Redis infrastructure (additional dependency)
- Current approach keeps Redis as future optimization

### Alternative 2: JWT-Based Sessions

**Description:** Encode session state in JWT tokens

**Rejected:**
- Cannot revoke sessions immediately (must wait for expiration)
- Difficult to enforce concurrent session limits
- Token size grows with session metadata
- Recovery mechanism would be complex

### Alternative 3: Connection-Only Tracking

**Description:** Track only WebSocket connections without persistent sessions

**Rejected:**
- No ability to recover interrupted conversations
- Cannot implement session timeouts
- No session metrics for monitoring
- Poor user experience on reconnection

## Implementation Notes

### API Endpoints

```python
# REST endpoints for session management
GET    /api/v1/sessions           # List user sessions
POST   /api/v1/sessions           # Create session (for testing)
GET    /api/v1/sessions/{id}      # Get session details
PATCH  /api/v1/sessions/{id}      # Update session
DELETE /api/v1/sessions/{id}      # Close session
POST   /api/v1/sessions/recover   # Recover session
GET    /api/v1/sessions/metrics    # Session metrics
```

**Location:** `backend/api/v1/sessions.py`

### WebSocket Events

```python
# Client -> Server
EVENT_SESSION_RECOVER = "session:recover"

# Server -> Client
EVENT_SESSION_STATE = "session:state"
EVENT_SESSION_RECOVERED = "session:recovered"
```

### Testing Strategy

```bash
# Run session service tests
pytest tests/unit/crd_backend/services/test_session_service.py -v

# Run all backend tests
pytest tests/unit/crd_backend/ -v --cov=backend
```

**Test Coverage:** 21 tests covering:
- Session creation and retrieval
- Session recovery
- Connection count management
- Session lifecycle (close, expire)
- Concurrent session limits
- Metrics aggregation

## References

- [Epic 16 Specification](../epic/backend_phase_2_chat_execution.md)
- [WebSocket Chat ADR](014-websocket-chat-endpoint.md)
- [Message History ADR](015-message-history-management.md)
- FastAPI WebSocket Documentation: https://fastapi.tiangolo.com/advanced/websockets/
