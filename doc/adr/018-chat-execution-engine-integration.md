# ADR 018: Chat Execution Engine Integration

## Status

Accepted

## Context

With Task management (Epic 12), chat_shell integration (Epic 13), WebSocket endpoints (Epic 14-17) in place, the system needs a unified component that orchestrates the complete task execution flow. Key requirements:

1. **End-to-end flow**: Task creation → execution → completion with chat_shell
2. **Error handling**: Retry logic for transient failures
3. **State persistence**: Track execution progress in database
4. **Event broadcasting**: Notify clients of execution progress
5. **Background processing**: Queue for handling multiple concurrent tasks
6. **Message storage**: Persist chat messages during execution

Challenges:
- How to coordinate multiple services (Task, Chat, Message, Events)?
- How to handle failures gracefully with retry?
- How to broadcast events during execution?
- How to queue tasks for background processing?

## Decision

### 1. TaskExecutor Service

**Decision:** Create a TaskExecutor service that orchestrates the complete execution flow

**Rationale:**
- Encapsulates execution logic in a single component
- Coordinates multiple services (Task, Chat, Message, Events)
- Implements retry logic for resilience
- Provides clean API for task execution

**Execution Flow:**
```
1. Validate task and bot configuration
2. Start task (update status to RUNNING)
3. Store user input as message
4. Execute chat with AI agent
5. Store assistant response as message
6. Complete/fail task based on result
7. Broadcast events at each step
```

**Implementation:**
```python
class TaskExecutor:
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    async def execute_task(self, task_id, bot_name=None, namespace="default"):
        # Validate
        validation = await self.chat_service.validate_bot_configuration(...)

        # Start task
        task = await self.task_service.start(task_id)
        await self._broadcast_task_started(task)

        # Execute with retry
        for attempt in range(self.MAX_RETRIES):
            try:
                return await self._execute_with_chat(...)
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * attempt)
                else:
                    raise
```

**Location:** `backend/services/task_executor.py`

### 2. TaskQueue for Background Processing

**Decision:** Implement an in-memory TaskQueue for background task processing

**Rationale:**
- Enables asynchronous task execution
- Prevents blocking API requests
- Tracks running tasks
- Simple implementation for current needs (can be replaced with Celery/RQ later)

**Implementation:**
```python
class TaskQueue:
    def __init__(self):
        self._queue: asyncio.Queue[UUID] = asyncio.Queue()
        self._running: set[UUID] = set()

    async def enqueue(self, task_id: UUID) -> None
    async def _worker_loop(self, session_factory) -> None
```

**Location:** `backend/services/task_executor.py` (TaskQueue class)

### 3. Bot Name Extraction

**Decision:** Extract bot name from task spec with fallback to "default"

**Rationale:**
- Tasks store bot reference in spec
- Supports multiple bot references (bot_name, botRef)
- Default bot for simple use cases

**Extraction Logic:**
```python
def _extract_bot_name(self, task: TaskResponse) -> str:
    spec = task.spec or {}
    if "bot_name" in spec:
        return spec["bot_name"]
    if "botRef" in spec:
        return spec["botRef"].get("name", "default")
    return "default"
```

### 4. Message Persistence During Execution

**Decision:** Store both user input and AI response as messages during execution

**Rationale:**
- Maintains complete conversation history
- Enables message history retrieval via API
- Links messages to task for context

**Flow:**
```python
# Store user input
await self.message_service.create_user_message(
    task_id=task_id,
    content=task.input,
    thread_id=str(task_id),
)

# Execute chat and store response
await self.message_service.create_assistant_message(
    task_id=task_id,
    content=content,
    thread_id=str(task_id),
    metadata={"tool_calls": tool_calls},
)
```

### 5. Event Broadcasting Integration

**Decision:** Integrate with TaskEventBroadcaster to notify clients of progress

**Rationale:**
- Real-time updates for connected clients
- Separate from execution logic (decoupled)
- Graceful handling of broadcast failures

**Events Broadcast:**
- `task:started` - When execution begins
- `task:completed` - When execution succeeds
- `task:failed` - When execution fails

### 6. Task Execute API Endpoint

**Decision:** Add POST `/api/v1/tasks/{id}/execute` endpoint

**Rationale:**
- Explicit endpoint for task execution
- Supports both sync and async execution patterns
- Returns completed task or error

**Location:** `backend/api/v1/tasks.py`

## Consequences

### Positive

- **Complete flow**: Single component orchestrates entire execution
- **Resilience**: Retry logic handles transient failures
- **Observability**: Events broadcast at each step
- **Persistence**: Messages stored for history
- **Scalability**: Queue enables background processing

### Negative

- **Complexity**: Executor coordinates many services
- **Memory queue**: In-memory queue lost on restart (can be replaced later)
- **No persistence**: Queue state not persisted (acceptable for MVP)

## Alternatives Considered

### Alternative 1: Celery/RQ for Task Queue

**Description:** Use Celery or RQ for distributed task processing

**Rejected:**
- Adds infrastructure dependency (Redis)
- Overkill for current scale
- Can be added later when needed

### Alternative 2: Execute in WebSocket Handler

**Description:** Execute tasks directly in WebSocket chat handler

**Rejected:**
- Ties execution to WebSocket connection
- No support for API-only execution
- Harder to manage lifecycle

### Alternative 3: Separate Task Worker Process

**Description:** Run task execution in separate worker process

**Rejected:**
- Adds deployment complexity
- Requires inter-process communication
- Can be added later for scaling

## Implementation Notes

### API Endpoints

```python
# Execute task
POST /api/v1/tasks/{task_id}/execute
  Query params:
    - bot_name: Optional bot name
    - namespace: Namespace for bot lookup
  Returns: TaskResponse
```

### Execution Metrics

Future enhancement: Track execution metrics
- Execution duration
- Retry count
- Success/failure rates
- Token usage

### Testing Strategy

```bash
# Run task executor tests
pytest tests/unit/crd_backend/services/test_task_executor.py -v

# Run all backend tests
pytest tests/unit/crd_backend/ -v
```

**Test Coverage:** 18 tests covering:
- Task execution flow
- Error handling and retry
- Bot name extraction
- Event broadcasting
- Queue management

## Future Considerations

### Persistent Queue

Replace in-memory queue with Redis/RabbitMQ for:
- Queue persistence across restarts
- Multi-instance support
- Better scalability

### Task Workers

Add dedicated worker processes for:
- CPU-intensive task isolation
- Horizontal scaling
- Resource management

### Execution Scheduling

Add scheduling capabilities for:
- Delayed task execution
- Recurring tasks
- Cron-like scheduling

## References

- [Epic 18 Specification](../epic/backend_phase_2_chat_execution.md)
- [Task Management ADR](012-task-management-api.md)
- [Chat Shell Integration ADR](013-chat-shell-integration.md)
- [Event Broadcasting ADR](017-real-time-event-broadcasting.md)
