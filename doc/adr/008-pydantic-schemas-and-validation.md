# ADR 008: Pydantic Schemas & Validation

## Status

Accepted

## Context

With the database layer (Epic 7) in place, we needed a robust validation and serialization layer for the CRD API. The system required:

1. **API Request/Response Validation**: Validate incoming API requests and format responses consistently
2. **Field Aliasing**: Support camelCase in JSON (JavaScript convention) while using snake_case in Python
3. **Reference Validation**: Ensure Bot resources correctly reference Ghost, Model, and Shell resources
4. **Type Safety**: Leverage Python type hints for static analysis and IDE support
5. **Kubernetes Compatibility**: Follow Kubernetes-style resource patterns (metadata, spec, status)
6. **Database Integration**: Convert between Pydantic schemas and SQLAlchemy models seamlessly

Key requirements included:
- Pydantic v2 for performance and modern Python support
- Consistent schema structure across all CRD types
- Custom validators for Kubernetes-style naming conventions
- Reference validation to ensure data integrity
- from_db_model() methods for ORM integration

## Decision

We implemented a comprehensive Pydantic v2 schema layer with consistent patterns across all CRD types.

### 1. Base Schemas

**Decision:** Create reusable base schemas (Metadata, ResourceRef, BaseCRD, BaseSpec) that all CRD types extend.

**Rationale:**
- DRY principle - common fields and validation in one place
- Consistent API structure across all resource types
- Type-safe with Pydantic v2 BaseModel

**Schema Design:**
```python
class Metadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=255)
    namespace: str = Field(default="default", min_length=1, max_length=255)
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", v):
            raise ValueError("Name must follow Kubernetes naming convention")
        return v
```

**Location:** `backend/schemas/base.py`

### 2. Field Aliasing

**Decision:** Use Pydantic v2 field aliases for camelCase JSON serialization while maintaining snake_case in Python.

**Rationale:**
- Follows JavaScript/JSON conventions for API consumers
- Maintains Python PEP 8 naming conventions in code
- Enables seamless frontend/backend integration

**Example:**
```python
class GhostSpec(BaseSpec):
    model_config = ConfigDict(populate_by_name=True)

    system_prompt: str = Field(..., alias="systemPrompt")
    context_window: Optional[int] = Field(default=None, alias="contextWindow")
    tools_enabled: Optional[List[str]] = Field(default=None, alias="toolsEnabled")
```

JSON request:
```json
{
  "systemPrompt": "You are helpful",
  "contextWindow": 4096,
  "toolsEnabled": ["file_reader"]
}
```

**Location:** All schema files in `backend/schemas/`

### 3. CRD-Specific Schemas

**Decision:** Create separate schema modules for each CRD type with request/response variants.

**Rationale:**
- Clear separation of concerns
- Different schemas for creation vs response (id, timestamps)
- Resource-specific validation logic

**Structure per Resource:**
- `{Resource}Spec` - The specification body
- `{Resource}CRD` - Complete CRD for internal use
- `{Resource}CreateRequest` - API request for creation
- `{Resource}Response` - API response with metadata

**Location:**
- `backend/schemas/ghost.py`
- `backend/schemas/model.py`
- `backend/schemas/shell.py`
- `backend/schemas/bot.py`
- `backend/schemas/team.py`
- `backend/schemas/skill.py`

### 4. Reference Validation

**Decision:** Implement custom validators to ensure resource references point to correct kinds.

**Rationale:**
- Data integrity - prevent invalid references at API boundary
- Clear error messages for API consumers
- Bot resources must reference correct resource types

**Implementation:**
```python
class BotSpec(BaseSpec):
    ghost_ref: ResourceRef = Field(..., alias="ghostRef")
    model_ref: ResourceRef = Field(..., alias="modelRef")
    shell_ref: ResourceRef = Field(..., alias="shellRef")

    @field_validator("ghost_ref")
    @classmethod
    def validate_ghost_ref(cls, v: ResourceRef) -> ResourceRef:
        if v.kind != KindType.GHOST:
            raise ValueError(f"ghostRef must reference a Ghost resource, got {v.kind}")
        return v
```

**Location:** `backend/schemas/bot.py`, `backend/schemas/team.py`

### 5. ORM Integration

**Decision:** Implement `from_db_model()` class methods for converting SQLAlchemy models to Pydantic schemas.

**Rationale:**
- Clean separation between database and API layers
- Reusable conversion logic
- Handles JSON spec deserialization

**Implementation:**
```python
class GhostResponse(BaseModel):
    @classmethod
    def from_db_model(cls, db_model: Any) -> "GhostResponse":
        spec_data = db_model.spec or {}
        return cls(
            id=db_model.id,
            api_version=db_model.api_version,
            kind="ghost",
            metadata=Metadata(
                name=db_model.name,
                namespace=db_model.namespace,
                created_by=db_model.created_by,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            ),
            spec=GhostSpec(**spec_data),
        )
```

**Location:** All response schemas in `backend/schemas/`

### 6. Task Schemas

**Decision:** Create separate Task schemas since Task has a different lifecycle from CRD resources.

**Rationale:**
- Tasks are execution units, not declarative resources
- Different fields (input, output, error, status transitions)
- Separate API endpoints

**Location:** `backend/schemas/task.py`

### 7. Schema Organization

**Decision:** Organize schemas with clear separation of concerns.

**Structure:**
```
backend/schemas/
├── __init__.py       # Exports all public schemas
├── base.py           # Base schemas (Metadata, ResourceRef, BaseCRD)
├── ghost.py          # Ghost schemas
├── model.py          # Model schemas
├── shell.py          # Shell schemas
├── bot.py            # Bot schemas with reference validation
├── team.py           # Team schemas
├── skill.py          # Skill schemas
└── task.py           # Task schemas
```

## Consequences

### Positive

- **Type Safety**: Pydantic v2 provides static type checking and runtime validation
- **API Consistency**: All endpoints follow the same request/response structure
- **Developer Experience**: IDE autocomplete and type hints throughout
- **Documentation**: Schemas serve as API documentation with Field descriptions
- **Validation at Boundary**: Invalid data rejected at API entry point
- **Frontend Integration**: camelCase JSON aligns with JavaScript conventions
- **Testability**: Schema validation easily unit testable
- **Performance**: Pydantic v2 is significantly faster than v1

### Negative

- **Boilerplate**: Multiple schema classes per resource (Spec, CRD, Request, Response)
- **Maintenance Overhead**: Changes to models require corresponding schema updates
- **Validation Duplication**: Some validation exists in both SQLAlchemy and Pydantic
- **Learning Curve**: Team must understand Pydantic v2 patterns
- **Import Complexity**: Careful import management to avoid circular dependencies

## Alternatives Considered

### Alternative 1: SQLAlchemy Models Directly as Schemas

Use SQLAlchemy models directly for API serialization.

**Rejected:**
- Tight coupling between database and API layers
- Difficult to handle field aliasing (camelCase)
- No clean way to have different schemas for create vs response
- Validation logic mixed with database concerns

### Alternative 2: Pydantic v1

Use Pydantic v1 instead of v2.

**Rejected:**
- Pydantic v2 has significantly better performance
- v2 has improved type annotation support
- v2 is the future direction of Pydantic
- New project should use latest stable version

### Alternative 3: Separate Request/Response Schemas Only

Have only Request and Response schemas, no intermediate CRD schemas.

**Rejected:**
- CRD schemas useful for internal service layer
- Kubernetes-style consistency (metadata + spec pattern)
- Easier to implement generic CRUD operations

### Alternative 4: No Field Aliasing

Use snake_case in JSON API as well.

**Rejected:**
- JavaScript/frontend conventions favor camelCase
- Kubernetes APIs use camelCase
- Better developer experience for frontend teams

## Implementation Notes

### Dependencies

```toml
[project.dependencies]
pydantic>=2.0.0    # Schema validation and serialization
```

### Testing Strategy

```bash
# Run all schema tests
pytest tests/unit/crd_backend/schemas/ -v

# Run by resource type
pytest tests/unit/crd_backend/schemas/test_bot.py -v
pytest tests/unit/crd_backend/schemas/test_ghost.py -v

# Run by epic marker
pytest tests/ -m epic_8 -v

# Run with coverage
pytest tests/unit/crd_backend/schemas/ --cov=backend.schemas --cov-report=term-missing
```

**Test Categories:**
- Base schema validation (10 tests)
- Ghost schemas (5 tests)
- Model schemas (5 tests)
- Shell schemas (5 tests)
- Bot schemas with reference validation (6 tests)
- Team schemas with member validation (5 tests)
- Skill schemas with version validation (5 tests)
- Task schemas (5 tests)
- **Total: 76 tests**

### Performance Considerations

- Pydantic v2 is ~5-50x faster than v1 for validation
- Use `model_dump()` instead of deprecated `dict()` method
- `ConfigDict(populate_by_name=True)` enables both alias and field name access

### Security Considerations

- Validation happens at API boundary before reaching services
- Kubernetes naming convention prevents path traversal attacks
- Reference validation ensures resources can't spoof other types

## References

- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [Pydantic Field Types](https://docs.pydantic.dev/latest/concepts/fields/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Kubernetes API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
- [JSON Field Naming Convention](https://google.github.io/styleguide/jsoncstyleguide.xml?showone=Property_Name_Format#Property_Name_Format)
