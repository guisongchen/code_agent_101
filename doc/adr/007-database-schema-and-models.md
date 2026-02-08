# ADR 007: Database Schema & Models

## Status

Accepted

## Context

With the Backend CRD (Custom Resource Definition) management system being implemented (Epics 7-11), we needed a robust database layer to store and manage resources like Ghost, Model, Shell, Bot, Team, and Skill. The system needed to support:

1. **Declarative API**: Kubernetes-style resource definitions with flexible schemas
2. **Multi-tenancy**: Namespace isolation for different users/organizations
3. **Soft Deletes**: Ability to recover deleted resources
4. **JSON Storage**: Flexible spec storage for varying resource types
5. **Task Lifecycle**: Separate lifecycle for execution tasks with status tracking
6. **Reference Validation**: Resources can reference other resources (e.g., Bot references Ghost, Shell, Model)

Key requirements included:
- SQLAlchemy 2.0 for modern Python ORM support with type hints
- PostgreSQL for production with SQLite for testing
- Alembic for database migrations
- Async support for non-blocking database operations
- Connection pooling for performance
- Unique constraints for resource identity (kind, name, namespace)

## Decision

We implemented a database layer using SQLAlchemy 2.0 with a generic CRD storage pattern, following the Kubernetes resource model.

### 1. Single Table Inheritance for Kinds

**Decision:** Use a single `kinds` table with a discriminator column to store all CRD types (Ghost, Model, Shell, Bot, Team, Skill).

**Rationale:**
- All CRD resources share common metadata (name, namespace, timestamps, created_by)
- Flexible JSON spec column allows varying schemas per kind
- Single table simplifies queries and foreign key relationships
- Unique constraint on (kind, name, namespace) ensures resource identity
- Soft delete support via deleted_at timestamp

**Schema Design:**
```sql
CREATE TABLE kinds (
    id UUID PRIMARY KEY,
    kind VARCHAR(20) NOT NULL,  -- discriminator: ghost, model, shell, bot, team, skill
    api_version VARCHAR(10) NOT NULL DEFAULT 'v1',
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL DEFAULT 'default',
    spec JSONB NOT NULL DEFAULT '{}',
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE (kind, name, namespace)
);

CREATE INDEX idx_kinds_kind ON kinds(kind);
CREATE INDEX idx_kinds_kind_namespace ON kinds(kind, namespace);
CREATE INDEX idx_kinds_created_by ON kinds(created_by);
CREATE INDEX idx_kinds_deleted_at ON kinds(deleted_at);
```

**SQLAlchemy Model:**
```python
class Kind(Base, TimestampMixin, SoftDeleteMixin):
    """Generic model for storing CRD resources."""

    __tablename__ = "kinds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[KindType] = mapped_column(Enum(KindType), nullable=False, index=True)
    api_version: Mapped[str] = mapped_column(String(10), nullable=False, default="v1")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, default="default")
    spec: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("kind", "name", "namespace", name="uix_kind_name_namespace"),
    )
```

**Location:** `backend/models/kinds.py`

### 2. Separate Tasks Table

**Decision:** Create a separate `tasks` table with its own lifecycle, referencing Team resources.

**Rationale:**
- Tasks have a different lifecycle than CRD resources (PENDING → RUNNING → COMPLETED/FAILED/CANCELLED)
- Tasks require additional fields (input, output, error, started_at, completed_at)
- Tasks are execution units, not declarative resources
- Foreign key to Team enables task-to-team relationships

**Schema Design:**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL DEFAULT 'default',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    team_id UUID REFERENCES kinds(id) ON DELETE SET NULL,
    input TEXT,
    output TEXT,
    error TEXT,
    spec JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_status_namespace ON tasks(status, namespace);
CREATE INDEX idx_tasks_team_id ON tasks(team_id);
```

**SQLAlchemy Model:**
```python
class Task(Base, TimestampMixin, SoftDeleteMixin):
    """Model for Task resources with separate lifecycle from Kinds."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, default="default")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("kinds.id", ondelete="SET NULL"), nullable=True)
    input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spec: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped[Optional["Kind"]] = relationship("Kind", back_populates="tasks", foreign_keys=[team_id])
```

**Location:** `backend/models/tasks.py`

### 3. Common Mixins

**Decision:** Create reusable mixins for common columns and behaviors.

**Rationale:**
- DRY principle - avoid repeating timestamp and soft delete columns
- Consistent behavior across models
- Type-safe with SQLAlchemy 2.0 Mapped types

**Mixins:**
```python
class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class SoftDeleteMixin:
    """Mixin that adds soft delete support via deleted_at timestamp."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now()

    def restore(self) -> None:
        self.deleted_at = None
```

**Location:** `backend/database/base.py`

### 4. Database Engine Configuration

**Decision:** Support both async (PostgreSQL) and sync (SQLite) engines with connection pooling.

**Rationale:**
- PostgreSQL with asyncpg for production performance
- SQLite for testing and development simplicity
- Connection pooling for production workloads
- Environment-driven configuration

**Configuration:**
```python
# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/wegent")
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")

# Async engine with connection pooling
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Sync engine for migrations
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
)
```

**Session Management:**
```python
@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session as a context manager."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

**Location:** `backend/database/engine.py`

### 5. Alembic Migrations

**Decision:** Use Alembic for database migrations with cross-database compatibility.

**Rationale:**
- Version-controlled schema changes
- Support for both PostgreSQL (production) and SQLite (testing)
- Automated migration generation from SQLAlchemy models
- Rollback capability

**Migration Structure:**
```
backend/database/migrations/
├── env.py              # Alembic environment configuration
├── script.py.mako      # Migration script template
└── versions/
    └── 001_initial_schema.py  # Initial schema migration
```

**Cross-Database Compatibility:**
```python
def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    # PostgreSQL-specific: Create enum types
    if dialect == "postgresql":
        # Create native ENUM types
        pass
    else:
        # SQLite fallback: Use String columns
        uuid_type = sa.String(36)
        kind_enum = sa.String(20)
```

**Location:** `backend/database/migrations/`

### 6. Model Validation

**Decision:** Implement name validation using SQLAlchemy validates decorator.

**Rationale:**
- Kubernetes-style naming convention (lowercase alphanumeric with hyphens)
- Database-level constraints for data integrity
- Clear error messages for invalid input

**Validation:**
```python
@validates("name")
def validate_name(self, key: str, name: str) -> str:
    """Validate resource name format."""
    if not name:
        raise ValueError("Name cannot be empty")
    if len(name) > 255:
        raise ValueError("Name cannot exceed 255 characters")
    if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", name):
        raise ValueError(
            "Name must consist of lowercase alphanumeric characters or '-', "
            "and must start and end with an alphanumeric character"
        )
    return name
```

### 7. Module Organization

**Decision:** Organize database code with clear separation of concerns.

**Structure:**
```
backend/
├── __init__.py
├── database/
│   ├── __init__.py
│   ├── base.py              # DeclarativeBase and mixins
│   ├── engine.py            # Engine and session management
│   └── migrations/          # Alembic migrations
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           └── 001_initial_schema.py
└── models/
    ├── __init__.py
    ├── kinds.py             # Kind model
    └── tasks.py             # Task model
```

## Consequences

### Positive

- **Flexibility**: JSON spec storage allows varying schemas per resource type without schema migrations
- **Multi-tenancy**: Namespace isolation enables secure multi-user deployments
- **Soft Deletes**: Resources can be recovered after deletion
- **Type Safety**: SQLAlchemy 2.0 with Mapped types provides static type checking
- **Async Support**: Non-blocking database operations for better performance
- **Cross-Database**: Works with both PostgreSQL (production) and SQLite (testing)
- **Kubernetes-Style**: Familiar resource model for DevOps users
- **Reference Validation**: Foreign keys ensure referential integrity
- **Connection Pooling**: Efficient database connection reuse

### Negative

- **JSON Limitations**: No database-level schema validation for spec fields
- **Query Complexity**: JSON queries are database-specific (PostgreSQL JSONB vs SQLite JSON)
- **Migration Complexity**: Cross-database migrations require conditional logic
- **No ORM Relationships**: JSON spec cannot have foreign key constraints
- **Testing Overhead**: Need to test against both PostgreSQL and SQLite
- **Enum Handling**: Database-specific enum implementation required

## Alternatives Considered

### Alternative 1: Separate Tables per Kind

Create individual tables for each CRD type (ghosts, models, shells, etc.).

**Rejected:**
- Would duplicate common columns (name, namespace, timestamps) across tables
- Harder to implement generic CRUD operations
- Foreign keys between resources would be more complex
- Querying across all resources would require UNION queries

### Alternative 2: Document Store (MongoDB)

Use MongoDB for flexible schema storage.

**Rejected:**
- Adds operational complexity (another database to manage)
- SQLAlchemy doesn't support MongoDB
- Would lose ACID transactions
- Team already familiar with PostgreSQL
- Relational data (tasks referencing teams) fits SQL better

### Alternative 3: Pure SQLAlchemy ORM Relationships

Define proper ORM relationships between resources instead of JSON spec.

**Rejected:**
- Too rigid for flexible CRD definitions
- Would require schema changes for new resource types
- JSON spec allows dynamic configuration
- Kubernetes-style resources favor flexible annotations/spec

### Alternative 4: SQLAlchemy 1.4

Use SQLAlchemy 1.4 instead of 2.0.

**Rejected:**
- 2.0 provides better type hint support with Mapped types
- 2.0 is the future direction of SQLAlchemy
- 2.0 has improved async support
- New project should use latest stable version

## Implementation Notes

### Dependencies

```toml
[project.dependencies]
sqlalchemy[asyncio]>=2.0.0    # ORM with async support
alembic>=1.12.0               # Database migrations
asyncpg>=0.29.0               # PostgreSQL async driver
psycopg2-binary>=2.9.9        # PostgreSQL sync driver (for Alembic)

[project.optional-dependencies]
dev = [
    "aiosqlite>=0.19.0",      # Async SQLite for testing
]
```

### Testing Strategy

```bash
# Run all backend tests
pytest tests/unit/crd_backend tests/integration/crd_backend

# Run by marker
pytest tests/ -m epic_7
pytest tests/ -m backend
pytest tests/ -m unit
pytest tests/ -m integration

# Run with coverage
pytest tests/ -m epic_7 --cov=backend --cov-report=html
```

**Test Categories:**
- Model unit tests (10 tests) - SQLite in-memory
- Migration tests (5 tests) - File-based SQLite
- Database connection tests (3 tests) - Async/sync session management

### Performance Considerations

- **Connection Pooling**: 20 connections in pool, 10 max overflow for production
- **Indexes**: Composite indexes on (kind, namespace) and (status, namespace) for common queries
- **JSON Storage**: Use PostgreSQL JSONB for indexed JSON queries in production
- **Soft Deletes**: Queries should filter `deleted_at IS NULL` by default

### Security Considerations

- **Namespace Isolation**: All queries must filter by namespace for multi-tenancy
- **Created By Tracking**: Audit trail with created_by field
- **Input Validation**: Name validation prevents injection attacks
- **Database Permissions**: Use least-privilege database users

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [Kubernetes Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)
