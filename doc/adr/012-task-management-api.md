# ADR 012: Task Management API

## Status

Accepted

## Context

After implementing the CRD resources (Ghost, Model, Shell, Bot, Team, Skill) in Phase 1, we needed to implement Task management for Phase 2 (Chat Execution Engine). Tasks represent execution units with a lifecycle distinct from static CRD configurations. The requirements included:

1. **Separate lifecycle**: Tasks progress through states (PENDING → RUNNING → COMPLETED/FAILED/CANCELLED) unlike static CRD resources
2. **Team association**: Tasks reference a Team (which is a CRD resource) to determine which bots execute the task
3. **Execution tracking**: Tasks need to track input, output, errors, and timing information
4. **Query flexibility**: Tasks need filtering by status, team, and namespace for monitoring and management
5. **Soft deletion**: Tasks should be soft-deleted to preserve execution history

Key questions to resolve:
- Should Tasks use the generic CRD table (kinds) or a separate table?
- Should Tasks use UUID or name+namespace for lookup?
- How should status transitions be validated and exposed via API?
- Should Tasks follow the same CRD-style schema (metadata/spec) or a flatter structure?

## Decision

We implemented Tasks as a separate resource type with dedicated database table, UUID-based lookup, and lifecycle-aware API endpoints.

### 1. Separate Table Design

**Decision:** Use a dedicated `tasks` table instead of the generic `kinds` table used for CRD resources.

**Rationale:**
- Tasks have a fundamentally different lifecycle (stateful) vs CRDs (stateless configuration)
- Tasks require additional columns (status, started_at, completed_at, input, output, error) not needed by CRDs
- Tasks need database-level constraints and indexes specific to execution tracking
- Foreign key relationships (team_id → kinds.id) are cleaner with separate tables

**Schema:**
```python
class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, default="default")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("kinds.id", ondelete="SET NULL"))
    input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spec: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
```

**Location:** `backend/models/tasks.py`

### 2. UUID-Based Lookup

**Decision:** Use UUID primary keys for Task lookup instead of name+namespace composite key.

**Rationale:**
- Tasks are created dynamically during execution (unlike CRDs which are manually configured)
- UUIDs prevent naming collisions in high-throughput scenarios
- UUIDs are easier to generate client-side when needed
- More natural for Task-to-Task relationships (parent/child tasks in future)
- Consistent with typical workflow/execution engine patterns

**Implementation:**
```python
@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, ...) -> TaskResponse:
    service = TaskService(session)
    task = await service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task
```

**Location:** `backend/api/v1/tasks.py`

### 3. Lifecycle Status Management

**Decision:** Implement explicit status transition methods with validation in the model layer.

**Rationale:**
- Prevents invalid state transitions (e.g., COMPLETED → RUNNING)
- Centralizes state change logic in the domain model
- Automatically manages timestamps (started_at, completed_at)
- Clear separation between business logic and API layer

**Implementation:**
```python
class Task(Base, ...):
    def start(self) -> None:
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {self.status} state")
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, output: Optional[str] = None) -> None:
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in {self.status} state")
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        if output:
            self.output = output

    def fail(self, error: str) -> None:
        if self.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise ValueError(f"Cannot fail task in {self.status} state")
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def cancel(self) -> None:
        if self.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise ValueError(f"Cannot cancel task in {self.status} state")
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
```

**Location:** `backend/models/tasks.py`

### 4. PATCH /status Endpoint

**Decision:** Use a dedicated `PATCH /tasks/{id}/status` endpoint for status transitions instead of a generic PUT/PATCH.

**Rationale:**
- Status transitions are actions, not just attribute updates
- Clear API semantics: PATCH /status means "perform a state transition"
- Allows different request body (TaskStatusUpdate) vs full Task update
- Easier to document and understand for API consumers
- Can add transition-specific parameters (output for complete, error for fail)

**Implementation:**
```python
@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID,
    update: TaskStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    service = TaskService(session)
    try:
        if update.status == TaskStatus.RUNNING:
            return await service.start(task_id)
        elif update.status == TaskStatus.COMPLETED:
            return await service.complete(task_id, output=update.output)
        elif update.status == TaskStatus.FAILED:
            return await service.fail(task_id, error=update.error or "Unknown error")
        elif update.status == TaskStatus.CANCELLED:
            return await service.cancel(task_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
```

**Location:** `backend/api/v1/tasks.py`

### 5. Direct Field Schema (Non-CRD Style)

**Decision:** Use a flat schema with direct fields instead of CRD-style (apiVersion/kind/metadata/spec).

**Rationale:**
- Tasks are not Kubernetes-style resources
- Flatter structure is more intuitive for workflow/execution resources
- Direct field access is cleaner in code (task.status vs task.metadata.name)
- Still supports flexible configuration via `spec` JSON field
- Consistent with typical task/workflow API patterns

**Implementation:**
```python
class TaskResponse(BaseModel):
    id: UUID
    name: str
    namespace: str
    status: TaskStatus
    team_id: Optional[UUID] = Field(alias="teamId")
    input: Optional[str]
    output: Optional[str]
    error: Optional[str]
    spec: Optional[Dict[str, Any]]
    started_at: Optional[datetime] = Field(alias="startedAt")
    completed_at: Optional[datetime] = Field(alias="completedAt")
    created_by: Optional[str] = Field(alias="createdBy")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
```

**Location:** `backend/schemas/task.py`

### 6. Team Reference via Foreign Key

**Decision:** Reference Teams via `team_id` foreign key with `SET NULL` on delete.

**Rationale:**
- Tasks can exist without a team (standalone execution)
- Database-level referential integrity
- Soft-deleted teams don't cascade delete tasks (preserves history)
- Easy to query tasks by team for team-specific dashboards

**Implementation:**
```python
team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("kinds.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)

team: Mapped[Optional["Kind"]] = relationship(
    "Kind",
    back_populates="tasks",
    foreign_keys=[team_id],
)
```

**Location:** `backend/models/tasks.py`, `backend/models/kinds.py`

## Consequences

### Positive

- **Clear Lifecycle**: Explicit state machine prevents invalid transitions
- **Query Performance**: Dedicated table with appropriate indexes for task queries
- **Flexible Configuration**: JSON spec field allows task-specific parameters without schema changes
- **History Preservation**: Soft deletion maintains execution history
- **Team Integration**: Clean association between tasks and team configurations
- **API Clarity**: Separate endpoints for different operations (create vs status update)
- **Type Safety**: Full Pydantic schemas with proper field types and validation

### Negative

- **Two Patterns**: Codebase now has two resource patterns (CRD vs Task) to understand
- **No Generic CRUD**: TaskService doesn't extend CRDService, some code duplication
- **UUID URLs**: Less human-readable URLs compared to name-based CRD endpoints
- **Migration Complexity**: Future schema changes require Alembic migrations
- **Query Complexity**: Cross-table queries needed when joining tasks with team configurations

## Alternatives Considered

### Alternative 1: CRD-Style Tasks

Store Tasks in the generic `kinds` table with `kind='task'`.

**Rejected:**
- Would require adding task-specific columns (status, started_at, etc.) to all CRD records
- Status transitions would be harder to enforce at the database level
- Mixing configuration (CRDs) and execution state (Tasks) in same table
- Would need complex spec serialization for task-specific fields

### Alternative 2: Name+Namespace Lookup

Use composite key (name, namespace) for Task lookup like CRD resources.

**Rejected:**
- Naming collisions in high-throughput scenarios
- Harder to generate unique names client-side
- UUIDs are standard for workflow/task systems
- Would require unique constraint on (name, namespace) affecting performance

### Alternative 3: Generic PUT for Status Updates

Use standard PUT /tasks/{id} with full task body for status changes.

**Rejected:**
- Less clear API semantics
- Clients would need to fetch current state before updating
- Risk of race conditions in concurrent updates
- Harder to add transition-specific validation

### Alternative 4: Event-Sourced Tasks

Store task state as a series of events rather than current state.

**Rejected:**
- Overkill for current requirements
- More complex to implement and query
- Would require event store infrastructure
- Can be added later if audit trail requirements grow

## Implementation Notes

### Dependencies

No new dependencies required. Uses existing:
```toml
fastapi>=0.100.0
sqlalchemy[asyncio]>=2.0.0
pydantic>=2.0.0
```

### Testing Strategy

```bash
# Run Task API tests
pytest tests/unit/crd_backend/api/test_tasks.py -v

# Run Task service tests
pytest tests/unit/crd_backend/services/test_task_service.py -v

# Run all Epic 12 tests
pytest tests/ -m epic_12 -v

# Total: 23 tests (13 API + 10 service)
```

**Test Categories:**
- Task creation tests (3 tests)
- Task listing tests (2 tests)
- Task retrieval tests (2 tests)
- Status transition tests (4 tests)
- Task deletion tests (2 tests)
- Service layer tests (10 tests)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tasks` | Create Task |
| GET | `/api/v1/tasks` | List Tasks (with filters) |
| GET | `/api/v1/tasks/{id}` | Get Task by ID |
| PATCH | `/api/v1/tasks/{id}/status` | Update Task Status |
| DELETE | `/api/v1/tasks/{id}` | Delete Task |

### Query Parameters

**List Tasks:**
- `namespace` - Filter by namespace (default: "default")
- `status` - Filter by status (pending, running, completed, failed, cancelled)
- `team_id` - Filter by team ID

### Status Transitions

```
PENDING → RUNNING → COMPLETED
                ↘ FAILED
                ↘ CANCELLED

PENDING → CANCELLED (direct)
```

Terminal states (COMPLETED, FAILED, CANCELLED) cannot transition to other states.

## References

- [Epic 12: Task Management API](/doc/epic/backend_phase_2_chat_execution.md)
- [SQLAlchemy Async ORM](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [Workflow Engine Patterns](https://microservices.io/patterns/data/event-sourcing.html)
