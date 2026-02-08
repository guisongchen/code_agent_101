# ADR 009: CRUD Service Layer

## Status

Accepted

## Context

With the database layer (Epic 7) and Pydantic schemas (Epic 8) in place, we needed a service layer to orchestrate CRUD operations for CRD resources. The service layer needed to:

1. **Provide Generic CRUD Operations**: Common create, read, update, delete operations across all resource types
2. **Enforce Business Rules**: Reference validation (e.g., Bot must reference existing Ghost, Model, Shell)
3. **Handle Soft Deletes**: Mark resources as deleted without removing them from the database
4. **Support Multi-tenancy**: Filter resources by namespace
5. **Manage Task Lifecycle**: Handle task state transitions (PENDING → RUNNING → COMPLETED/FAILED/CANCELLED)
6. **Integrate with Async Database Sessions**: Work with SQLAlchemy async sessions for non-blocking operations

Key requirements included:
- Type-safe service classes using generics
- Consistent API across all resource types
- Reference validation at the service layer
- Soft delete support
- Namespace isolation

## Decision

We implemented a service layer with a generic base class and resource-specific subclasses.

### 1. Generic CRDService Base Class

**Decision:** Create a generic `CRDService[T]` base class that provides common CRUD operations for all CRD resources.

**Rationale:**
- DRY principle - common operations defined once
- Type safety with generics
- Consistent interface across all resource types
- Easy to extend with resource-specific logic

**Implementation:**
```python
from typing import Generic, TypeVar

T = TypeVar("T", bound=BaseModel)

class CRDService(Generic[T]):
    kind_type: KindType = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, name: str, namespace: str = "default") -> Optional[T]:
        result = await self.session.execute(
            select(Kind).where(
                Kind.kind == self.kind_type,
                Kind.name == name,
                Kind.namespace == namespace,
                Kind.deleted_at.is_(None)
            )
        )
        kind = result.scalar_one_or_none()
        return self._convert_to_schema(kind) if kind else None

    async def list(self, namespace: Optional[str] = "default") -> List[T]:
        # ... implementation

    async def create(self, schema: T, created_by: Optional[str] = None) -> T:
        # Check for duplicates
        existing = await self.get(schema.metadata.name, schema.metadata.namespace)
        if existing:
            raise ValueError(f"Resource already exists")

        db_data = schema.to_db_dict()
        kind = Kind(**db_data)
        self.session.add(kind)
        await self.session.flush()
        await self.session.refresh(kind)
        return self._convert_to_schema(kind)

    async def delete(self, name: str, namespace: str = "default") -> bool:
        # Soft delete implementation
        kind.soft_delete()
        return True
```

**Location:** `backend/services/base.py`

### 2. Resource-Specific Services

**Decision:** Create separate service classes for each CRD type that extend the base class.

**Rationale:**
- Resource-specific query methods (e.g., find_by_provider for Models)
- Reference validation for Bot and Team resources
- Clear separation of concerns

**Implementation:**
```python
class GhostService(CRDService[GhostResponse]):
    kind_type = KindType.GHOST

    def _convert_to_schema(self, kind: Kind) -> GhostResponse:
        return GhostResponse.from_db_model(kind)

    async def find_by_system_prompt(self, substring: str) -> List[GhostResponse]:
        # Ghost-specific search

class BotService(CRDService[BotResponse]):
    kind_type = KindType.BOT

    async def create(self, schema: BotCRD, created_by: str = None) -> BotResponse:
        # Validate references before creating
        await self._validate_reference(schema.spec.ghost_ref)
        await self._validate_reference(schema.spec.model_ref)
        await self._validate_reference(schema.spec.shell_ref)
        return await super().create(schema, created_by)
```

**Location:**
- `backend/services/ghost.py`
- `backend/services/model.py`
- `backend/services/shell.py`
- `backend/services/bot.py`
- `backend/services/team.py`
- `backend/services/skill.py`

### 3. Response Schema Return Types

**Decision:** Services return Response schemas (with `id` field) instead of CRD schemas.

**Rationale:**
- Response schemas include database-generated fields (id, timestamps)
- Consistent with API response format
- Clearer type signatures

**Implementation:**
```python
# CRD schema for input (no id)
class GhostCRD(BaseCRD):
    metadata: Metadata
    spec: GhostSpec

# Response schema for output (with id)
class GhostResponse(BaseModel):
    id: UUID
    metadata: Metadata
    spec: GhostSpec

# Service returns Response
class GhostService(CRDService[GhostResponse]):
    def _convert_to_schema(self, kind: Kind) -> GhostResponse:
        return GhostResponse.from_db_model(kind)
```

### 4. Reference Validation

**Decision:** Implement reference validation in BotService and TeamService to ensure referenced resources exist.

**Rationale:**
- Data integrity at the service layer
- Clear error messages for API consumers
- Prevents orphaned references

**Implementation:**
```python
class BotService(CRDService[BotResponse]):
    async def _validate_reference(self, ref: ResourceRef) -> None:
        result = await self.session.execute(
            select(Kind).where(
                Kind.kind == ref.kind,
                Kind.name == ref.name,
                Kind.namespace == ref.namespace,
                Kind.deleted_at.is_(None)
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError(
                f"Referenced resource not found: {ref.kind.value}/{ref.namespace}/{ref.name}"
            )
```

**Location:** `backend/services/bot.py`, `backend/services/team.py`

### 5. TaskService with Lifecycle Management

**Decision:** Create a separate TaskService (not extending CRDService) with lifecycle state management.

**Rationale:**
- Tasks have a different lifecycle from CRD resources
- State transitions need validation (can't complete from PENDING)
- Separate operations: start(), complete(), fail(), cancel()

**Implementation:**
```python
class TaskService:
    async def start(self, task_id: UUID) -> TaskResponse:
        task = await self._get_task_or_raise(task_id)
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {task.status.value} state")
        task.start()
        await self.session.flush()
        await self.session.refresh(task)
        return TaskResponse.from_db_model(task)

    async def complete(self, task_id: UUID, output: str) -> TaskResponse:
        task = await self._get_task_or_raise(task_id)
        if task.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in {task.status.value} state")
        task.complete(output)
        await self.session.flush()
        await self.session.refresh(task)
        return TaskResponse.from_db_model(task)
```

**Location:** `backend/services/task.py`

### 6. Async Session Management

**Decision:** Use SQLAlchemy async sessions with proper flush/refresh patterns.

**Rationale:**
- Non-blocking database operations
- Proper handling of auto-generated fields (id, timestamps)
- Refresh after flush to get updated values

**Implementation:**
```python
async def create(self, schema: T, created_by: str = None) -> T:
    kind = Kind(**db_data)
    self.session.add(kind)
    await self.session.flush()      # Get the ID
    await self.session.refresh(kind)  # Refresh to get timestamps
    return self._convert_to_schema(kind)
```

## Consequences

### Positive

- **Type Safety**: Generic base class provides compile-time type checking
- **Code Reuse**: Common CRUD logic in one place
- **Consistency**: All services follow the same patterns
- **Testability**: Easy to mock services for API layer tests
- **Reference Integrity**: Validation prevents broken references
- **Soft Deletes**: Resources can be recovered after deletion
- **Clear Separation**: Service layer between API and database

### Negative

- **Boilerplate**: Each service needs `_convert_to_schema` method
- **Inheritance Complexity**: Generic types can be confusing
- **Async Overhead**: More complex than sync code
- **Session Management**: Careful handling needed for lazy loading
- **Duplicate Validation**: Some validation exists in both schemas and services

## Alternatives Considered

### Alternative 1: Repository Pattern

Use a separate repository layer for database access.

**Rejected:**
- Adds unnecessary abstraction for this project size
- Service layer already provides good separation
- More boilerplate code

### Alternative 2: Active Record Pattern

Put CRUD methods directly on the models.

**Rejected:**
- Tight coupling between models and database operations
- Harder to test in isolation
- Doesn't work well with async sessions

### Alternative 3: No Generic Base Class

Implement CRUD operations in each service separately.

**Rejected:**
- Code duplication across services
- Inconsistent interfaces
- More maintenance overhead

### Alternative 4: Sync Services

Use synchronous database sessions in services.

**Rejected:**
- Would block the event loop
- Inconsistent with async database layer
- Poor performance under load

## Implementation Notes

### Dependencies

```toml
[project.dependencies]
sqlalchemy[asyncio]>=2.0.0    # Async ORM support
aiosqlite>=0.19.0             # Async SQLite for testing
```

### Testing Strategy

```bash
# Run all service tests
pytest tests/unit/crd_backend/services/ -v

# Run by service type
pytest tests/unit/crd_backend/services/test_bot_service.py -v
pytest tests/unit/crd_backend/services/test_task_service.py -v

# Run by epic marker
pytest tests/ -m epic_9 -v

# Run with coverage
pytest tests/unit/crd_backend/services/ --cov=backend.services --cov-report=term-missing
```

**Test Categories:**
- Base service operations (6 tests per service)
- Reference validation (Bot, Team services)
- Soft delete functionality
- Task lifecycle state transitions
- **Total: 48 tests**

### Performance Considerations

- Use `session.flush()` instead of `session.commit()` to let caller control transactions
- `session.refresh()` after flush to get auto-generated fields
- Query filtering at database level where possible
- Fallback to Python filtering for SQLite JSON queries

### Security Considerations

- Namespace filtering enforced at service layer
- Soft delete prevents data loss
- Reference validation prevents orphaned records
- `created_by` tracking for audit trail

## References

- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Python Generics](https://docs.python.org/3/library/typing.html#generics)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
