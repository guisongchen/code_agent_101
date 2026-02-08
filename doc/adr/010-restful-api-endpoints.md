# ADR 010: RESTful API Endpoints

## Status

Accepted

## Context

With the database layer (Epic 7), Pydantic schemas (Epic 8), and CRUD service layer (Epic 9) in place, we needed to expose these capabilities through a RESTful API. The API needed to:

1. **Follow Kubernetes-style conventions**: Resource-based URLs with namespace support
2. **Support all CRD types**: Ghost, Model, Shell, Bot, Team, Skill resources
3. **Implement standard HTTP methods**: POST (create), GET (list/retrieve), DELETE (remove)
4. **Return proper HTTP status codes**: 201 Created, 200 OK, 404 Not Found, 409 Conflict, 204 No Content
5. **Handle namespace isolation**: Filter resources by namespace
6. **Validate references**: Bot and Team resources validate referenced resources exist
7. **Use async operations**: Non-blocking database operations with SQLAlchemy async sessions

Key requirements included:
- FastAPI for high performance and automatic OpenAPI documentation
- Type-safe request/response models using Pydantic schemas
- Dependency injection for database sessions
- Consistent error handling with meaningful HTTP status codes

## Decision

We implemented a RESTful API using FastAPI with a Kubernetes-style resource hierarchy.

### 1. FastAPI Framework

**Decision:** Use FastAPI as the web framework for the REST API.

**Rationale:**
- Native async support for non-blocking database operations
- Automatic OpenAPI/Swagger documentation generation
- Pydantic integration for request/response validation
- Dependency injection system for clean code organization
- High performance (on par with Node.js and Go)

**Implementation:**
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

app = FastAPI(
    title="Wegent Backend API",
    description="Kubernetes-style RESTful API for CRD resources",
    version="1.0.0",
    lifespan=lifespan,
)
```

**Location:** `backend/main.py`

### 2. API Router Structure

**Decision:** Organize endpoints using FastAPI routers with a `/api/v1` prefix.

**Rationale:**
- Clean separation of API versions
- Modular organization by resource type
- Easy to extend with new resource types
- Clear URL hierarchy following REST conventions

**Implementation:**
```python
# backend/api/router.py
api_router = APIRouter()
api_router.include_router(kinds.router, prefix="/v1", tags=["kinds"])

# backend/api/v1/kinds.py
@router.post("/kinds/ghosts", response_model=GhostResponse, status_code=201)
async def create_ghost(request: GhostCreateRequest, ...): ...

@router.get("/kinds/ghosts", response_model=List[GhostResponse])
async def list_ghosts(namespace: Optional[str] = "default", ...): ...

@router.get("/kinds/ghosts/{name}", response_model=GhostResponse)
async def get_ghost(name: str, namespace: str = "default", ...): ...

@router.delete("/kinds/ghosts/{name}", status_code=204)
async def delete_ghost(name: str, namespace: str = "default", ...): ...
```

**Location:** `backend/api/router.py`, `backend/api/v1/kinds.py`

### 3. Request/Response Schemas

**Decision:** Use separate CreateRequest schemas for API input and Response schemas for output.

**Rationale:**
- Clear separation between API contract and internal models
- Response schemas include database-generated fields (id, timestamps)
- Consistent camelCase JSON with snake_case Python fields via Pydantic aliases
- Type safety throughout the API layer

**Implementation:**
```python
class GhostCreateRequest(BaseModel):
    metadata: Metadata
    spec: GhostSpec

class GhostResponse(BaseModel):
    id: UUID
    api_version: str = Field(alias="apiVersion")
    kind: str = "ghost"
    metadata: Metadata
    spec: GhostSpec
```

**Location:** All schema files in `backend/schemas/`

### 4. Database Session Dependency

**Decision:** Use FastAPI dependency injection to provide database sessions.

**Rationale:**
- Clean separation of concerns
- Automatic session lifecycle management
- Easy to override for testing
- Transaction handling (commit on success, rollback on exception)

**Implementation:**
```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

@router.post("/kinds/ghosts")
async def create_ghost(
    request: GhostCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> GhostResponse:
    service = GhostService(session)
    ...
```

**Location:** `backend/database/engine.py`, `backend/api/v1/kinds.py`

### 5. HTTP Status Codes

**Decision:** Return appropriate HTTP status codes for different scenarios.

**Rationale:**
- 201 Created: Resource successfully created
- 200 OK: Resource retrieved or list returned
- 204 No Content: Resource successfully deleted
- 404 Not Found: Resource doesn't exist
- 409 Conflict: Resource already exists (duplicate)
- 400 Bad Request: Invalid references or validation errors

**Implementation:**
```python
@router.post("/kinds/ghosts", status_code=status.HTTP_201_CREATED)
async def create_ghost(...) -> GhostResponse:
    try:
        result = await service.create(ghost_crd)
        return result
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))

@router.get("/kinds/ghosts/{name}")
async def get_ghost(name: str, ...) -> GhostResponse:
    ghost = await service.get(name, namespace)
    if not ghost:
        raise HTTPException(status_code=404, detail=f"Ghost '{name}' not found")
    return ghost

@router.delete("/kinds/ghosts/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ghost(name: str, ...) -> None:
    deleted = await service.delete(name, namespace)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Ghost '{name}' not found")
```

**Location:** `backend/api/v1/kinds.py`

### 6. Namespace Support

**Decision:** Support namespace isolation via query parameters.

**Rationale:**
- Kubernetes-style resource organization
- Multi-tenancy support
- Default namespace for simple use cases
- All-namespaces listing with `namespace=null`

**Implementation:**
```python
@router.get("/kinds/ghosts")
async def list_ghosts(
    namespace: Optional[str] = Query(default="default"),
    session: AsyncSession = Depends(get_db_session),
) -> List[GhostResponse]:
    service = GhostService(session)
    if namespace is None:
        return await service.list(include_all_namespaces=True)
    return await service.list(namespace=namespace)
```

**Location:** `backend/api/v1/kinds.py`

### 7. Reference Validation

**Decision:** Validate resource references at the service layer and return 400 for invalid references.

**Rationale:**
- Data integrity for Bot and Team resources
- Clear error messages for API consumers
- Consistent with service layer validation

**Implementation:**
```python
async def create_bot(request: BotCreateRequest, ...) -> BotResponse:
    try:
        result = await service.create(bot_crd)
        return result
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
```

**Location:** `backend/api/v1/kinds.py`

## Consequences

### Positive

- **Type Safety**: Full type hints with Pydantic and FastAPI
- **Auto Documentation**: OpenAPI/Swagger docs generated automatically at `/docs`
- **Performance**: Async operations prevent blocking the event loop
- **Testability**: Easy to test with httpx AsyncClient and dependency overrides
- **Consistency**: All endpoints follow the same patterns and conventions
- **Namespace Isolation**: Resources properly isolated by namespace
- **Clear Errors**: Meaningful HTTP status codes and error messages

### Negative

- **Async Complexity**: More complex than synchronous code
- **Session Management**: Careful handling needed for async SQLAlchemy sessions
- **Fixture Overhead**: API tests require more setup (database, app instance)
- **Learning Curve**: Team must understand FastAPI and async patterns

## Alternatives Considered

### Alternative 1: Flask with Flask-RESTful

Use Flask instead of FastAPI.

**Rejected:**
- No native async support (would require threading)
- Manual OpenAPI documentation
- No built-in Pydantic integration
- Lower performance

### Alternative 2: Django REST Framework

Use Django with DRF for the API.

**Rejected:**
- Heavyweight for this use case
- No native async support
- ORM tied to Django models (would conflict with SQLAlchemy)
- More complex than needed

### Alternative 3: GraphQL

Use GraphQL instead of REST.

**Rejected:**
- Steeper learning curve
- More complex client requirements
- Kubernetes-style API is naturally RESTful
- Overkill for CRUD operations

### Alternative 4: No API Versioning

Use `/api/kinds/ghosts` without version prefix.

**Rejected:**
- Harder to evolve API in the future
- Versioning is standard practice
- Easy to add with FastAPI prefixes

## Implementation Notes

### Dependencies

```toml
[project.dependencies]
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
httpx>=0.24.0  # For testing

[project.optional-dependencies]
dev = [
    "aiosqlite>=0.19.0",  # For async SQLite testing
]
```

### Testing Strategy

```bash
# Run all API tests
pytest tests/unit/crd_backend/api/ -v

# Run by epic marker
pytest tests/ -m epic_10 -v

# Run with coverage
pytest tests/unit/crd_backend/api/ --cov=backend.api --cov-report=term-missing
```

**Test Categories:**
- Ghost API tests (7 tests)
- Model API tests (7 tests)
- Shell API tests (7 tests)
- Bot API tests (7 tests)
- Team API tests (7 tests)
- Skill API tests (7 tests)
- HTTP status code tests (5 tests)
- **Total: 47 tests**

### Running the API

```bash
# Development server
uvicorn backend.main:app --reload

# Production
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/kinds/ghosts` | Create Ghost |
| GET | `/api/v1/kinds/ghosts` | List Ghosts |
| GET | `/api/v1/kinds/ghosts/{name}` | Get Ghost |
| DELETE | `/api/v1/kinds/ghosts/{name}` | Delete Ghost |
| POST | `/api/v1/kinds/models` | Create Model |
| GET | `/api/v1/kinds/models` | List Models |
| GET | `/api/v1/kinds/models/{name}` | Get Model |
| DELETE | `/api/v1/kinds/models/{name}` | Delete Model |
| POST | `/api/v1/kinds/shells` | Create Shell |
| GET | `/api/v1/kinds/shells` | List Shells |
| GET | `/api/v1/kinds/shells/{name}` | Get Shell |
| DELETE | `/api/v1/kinds/shells/{name}` | Delete Shell |
| POST | `/api/v1/kinds/bots` | Create Bot |
| GET | `/api/v1/kinds/bots` | List Bots |
| GET | `/api/v1/kinds/bots/{name}` | Get Bot |
| DELETE | `/api/v1/kinds/bots/{name}` | Delete Bot |
| POST | `/api/v1/kinds/teams` | Create Team |
| GET | `/api/v1/kinds/teams` | List Teams |
| GET | `/api/v1/kinds/teams/{name}` | Get Team |
| DELETE | `/api/v1/kinds/teams/{name}` | Delete Team |
| POST | `/api/v1/kinds/skills` | Create Skill |
| GET | `/api/v1/kinds/skills` | List Skills |
| GET | `/api/v1/kinds/skills/{name}` | Get Skill |
| DELETE | `/api/v1/kinds/skills/{name}` | Delete Skill |

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Async SQLAlchemy](https://fastapi.tiangolo.com/advanced/async-sql-databases/)
- [Kubernetes API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
- [REST API Design Best Practices](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design)
