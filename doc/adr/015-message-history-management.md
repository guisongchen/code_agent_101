# ADR 015: Message History Management

## Status

Accepted

## Context

With the WebSocket chat endpoint implemented (Epic 14), we needed to persist chat messages for history retrieval and session resumption (Epic 15). The requirements included:

1. **Message persistence**: Store both user messages and AI responses in the database
2. **Thread-based organization**: Support multiple conversation threads within a task
3. **Pagination**: Handle large message histories efficiently
4. **Session resumption**: Allow clients to retrieve history when reconnecting
5. **Metadata tracking**: Store token usage, model info, and tool call details
6. **WebSocket integration**: Support `history:sync` event for real-time history retrieval
7. **Ordering**: Maintain message sequence within threads

Key questions to resolve:
- How to structure the message schema for flexibility?
- What pagination strategy to use (offset vs cursor)?
- How to handle message ordering across threads?
- How to integrate with WebSocket for history sync?

## Decision

We implemented a comprehensive message history system with SQLAlchemy models, async service layer, and WebSocket integration.

### 1. Message Model Design

**Decision:** Create a dedicated `Message` model with thread-based organization.

**Rationale:**
- Separate table from tasks allows efficient querying and pagination
- Thread ID supports multiple conversations within a task
- Sequence numbers provide reliable ordering
- JSON metadata field allows flexible extension

**Schema:**
```python
class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole))  # user, assistant, system, tool
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType))  # text, tool_call, etc.
    content: Mapped[str] = mapped_column(Text)
    thread_id: Mapped[str] = mapped_column(String(255), default="default")
    sequence: Mapped[int] = mapped_column(nullable=False, default=0)

    # Token usage tracking
    tokens_used: Mapped[Optional[int]]
    prompt_tokens: Mapped[Optional[int]]
    completion_tokens: Mapped[Optional[int]]

    # Model and tool metadata
    model: Mapped[Optional[str]]
    tool_name: Mapped[Optional[str]]
    tool_call_id: Mapped[Optional[str]]

    # Flexible metadata (renamed to 'meta' to avoid SQLAlchemy reserved name)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    generated_at: Mapped[Optional[datetime]]
```

**Location:** `backend/models/messages.py`

### 2. Sequence-Based Ordering

**Decision:** Use integer sequence numbers per thread for message ordering.

**Rationale:**
- Simpler than cursor-based pagination for our use case
- Allows efficient range queries (before/after sequence)
- Auto-increment within thread boundaries
- Easy to implement and understand

**Implementation:**
```python
async def _get_next_sequence(self, task_id: UUID, thread_id: str) -> int:
    result = await self.session.execute(
        select(func.max(Message.sequence))
        .where(
            Message.task_id == task_id,
            Message.thread_id == thread_id,
        )
    )
    max_sequence = result.scalar()
    return (max_sequence + 1) if max_sequence is not None else 0
```

**Location:** `backend/services/message.py:372-393`

### 3. Offset-Based Pagination

**Decision:** Use offset-based pagination for message history.

**Rationale:**
- Sufficient for chat history use case (not high-throughput)
- Simpler client implementation than cursor-based
- Works well with sequence-based ordering
- Supports both forward and backward pagination

**Request Schema:**
```python
class MessageHistoryRequest(BaseModel):
    thread_id: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    before_sequence: Optional[int] = None
    after_sequence: Optional[int] = None
```

**Location:** `backend/schemas/message.py:207-240`

### 4. WebSocket History Sync

**Decision:** Implement `history:request` and `history:sync` events for WebSocket.

**Rationale:**
- Clients can request history on connection/reconnection
- Reduces need for separate REST API calls
- Consistent with existing WebSocket event protocol
- Supports partial sync for large histories

**Client -> Server:**
```json
{"type": "history:request", "threadId": "default", "limit": 50, "offset": 0}
```

**Server -> Client:**
```json
{
  "type": "history:sync",
  "task_id": "...",
  "thread_id": "default",
  "messages": [...],
  "total": 100,
  "has_more": true
}
```

**Location:** `backend/api/v1/chat_ws.py:430-490`

### 5. Message Storage in Chat Handler

**Decision:** Store user messages immediately and accumulate AI responses during streaming.

**Rationale:**
- User messages are available immediately for other clients
- AI responses accumulated during streaming to avoid partial storage
- Tool calls and thinking stored as metadata
- Supports cancellation with partial content storage

**Implementation:**
```python
# Store user message
await message_service.create_user_message(
    task_id=task_id,
    content=content,
    thread_id=thread_id,
    meta={"user_id": user.id, "username": user.username},
)

# Accumulate assistant response during streaming
assistant_content_parts = []
async for event in chat_service.execute_chat(...):
    # Broadcast and accumulate...
    if event_type == "content":
        assistant_content_parts.append(event_data.get("text", ""))

# Store complete response
await message_service.create_assistant_message(
    task_id=task_id,
    content="".join(assistant_content_parts),
    thread_id=thread_id,
    meta=assistant_metadata,
)
```

**Location:** `backend/api/v1/chat_ws.py:267-330`

### 6. REST API Endpoints

**Decision:** Provide REST endpoints for message history management.

**Rationale:**
- WebSocket not always available (e.g., initial page load)
- REST provides simpler access for non-real-time use cases
- Supports admin operations (delete history)

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tasks/{task_id}/messages` | Get paginated messages |
| GET | `/api/v1/tasks/{task_id}/messages/{message_id}` | Get specific message |
| GET | `/api/v1/tasks/{task_id}/threads/{thread_id}/messages` | Get thread messages |
| DELETE | `/api/v1/tasks/{task_id}/messages` | Delete all task messages |

**Location:** `backend/api/v1/messages.py`

## Consequences

### Positive

- **Complete message history**: All chat interactions persist for future reference
- **Session resumption**: Clients can retrieve history on reconnection
- **Multi-thread support**: Tasks can have multiple conversation threads
- **Efficient pagination**: Offset-based pagination handles large histories
- **Rich metadata**: Token usage and model info available for analytics
- **Flexible storage**: JSON metadata allows future extensions
- **Cascading deletes**: Task deletion automatically cleans up messages

### Negative

- **Storage growth**: Message history can grow large over time (may need archiving)
- **Query performance**: Large threads may need index optimization
- **No soft delete**: Messages are hard-deleted (no recovery)
- **Single database**: No sharding support for massive scale

## Alternatives Considered

### Alternative 1: Cursor-Based Pagination

Use cursor pagination (after_message_id) instead of offset.

**Rejected:**
- More complex client implementation
- Offset-based is sufficient for chat history
- Sequence numbers already provide ordering

### Alternative 2: Separate Thread Table

Create a dedicated `Thread` table with foreign keys.

**Rejected:**
- Overkill for current requirements
- Thread ID as string is sufficient
- Adds complexity without clear benefit

### Alternative 3: Time-Based Ordering

Use timestamps instead of sequence numbers for ordering.

**Rejected:**
- Timestamps may not be unique
- Clock skew issues in distributed systems
- Sequence numbers are deterministic

### Alternative 4: External Message Store

Use Redis or Elasticsearch for message storage.

**Rejected:**
- Adds operational complexity
- PostgreSQL/SQLite sufficient for current scale
- Can migrate later if needed

## Implementation Notes

### Dependencies

No new dependencies - uses existing SQLAlchemy and FastAPI:
```toml
[project.dependencies]
sqlalchemy>=2.0.0  # Already included
```

### Testing Strategy

```bash
# Run message service tests
pytest tests/unit/crd_backend/services/test_message_service.py -v

# Run by epic marker
pytest tests/ -m epic_15 -v

# Total: 18 tests passing
```

**Test Categories:**
- Message creation (4 tests)
- Message retrieval (2 tests)
- Sequence management (2 tests)
- History pagination (6 tests)
- Message deletion (4 tests)

### Database Migration

The Message table is created automatically via `init_db()`:
```python
from backend.database.engine import init_db
await init_db()  # Creates all tables including messages
```

### API Usage Examples

**Get message history:**
```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}/messages?limit=50&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

**WebSocket history sync:**
```javascript
ws.send(JSON.stringify({
  type: "history:request",
  threadId: "default",
  limit: 50
}));
```

## References

- [Epic 15: Message History Management](/doc/epic/backend_phase_2_chat_execution.md)
- [ADR 014: WebSocket Chat Endpoint](/doc/adr/014-websocket-chat-endpoint.md)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
