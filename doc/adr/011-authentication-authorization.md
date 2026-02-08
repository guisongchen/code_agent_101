# ADR 011: Authentication & Authorization

## Status

Accepted

## Context

With the RESTful API in place (Epic 10), we needed to secure the endpoints and implement user management. The system needed:

1. **User authentication**: Verify user identity for API access
2. **Session management**: Stateless authentication for scalability
3. **Role-based access control**: Different permissions for admin vs regular users
4. **Namespace isolation**: Users should only access resources in their allowed namespaces
5. **Secure password storage**: Passwords must never be stored in plain text

Key requirements included:
- JWT tokens for stateless authentication
- Password hashing for security
- User registration and login endpoints
- Protected CRD endpoints (optional auth for flexibility)
- Admin role for privileged operations

## Decision

We implemented JWT-based authentication with role-based access control using FastAPI's security utilities.

### 1. JWT Token Authentication

**Decision:** Use JWT (JSON Web Tokens) for stateless authentication.

**Rationale:**
- Stateless - no server-side session storage required
- Self-contained - token includes user ID and role
- Industry standard - widely supported and understood
- Works well with FastAPI's OAuth2 integration

**Implementation:**
```python
# backend/core/security.py
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
```

**Location:** `backend/core/security.py`

### 2. Password Hashing

**Decision:** Use SHA-256 with salt for password hashing (PyJWT-compatible).

**Rationale:**
- No additional dependencies required (PyJWT already installed)
- Salt prevents rainbow table attacks
- Secure comparison prevents timing attacks
- Can upgrade to bcrypt in production

**Implementation:**
```python
# backend/core/security.py
def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hash_value}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    salt, stored_hash = hashed_password.split("$", 1)
    computed_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
    return secrets.compare_digest(computed_hash, stored_hash)
```

**Location:** `backend/core/security.py`

### 3. User Model

**Decision:** Create a SQLAlchemy User model with role support.

**Rationale:**
- Stores user credentials securely
- Supports soft delete for account recovery
- Role enumeration for RBAC
- Email validation at schema level

**Implementation:**
```python
# backend/models/user.py
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)
    default_namespace: Mapped[str] = mapped_column(String(255), nullable=False, default="default")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
```

**Location:** `backend/models/user.py`

### 4. Authentication Endpoints

**Decision:** Implement RESTful auth endpoints using FastAPI.

**Rationale:**
- Standard OAuth2 password flow
- JSON request/response bodies
- Proper HTTP status codes
- Auto-generated OpenAPI documentation

**Implementation:**
```python
# backend/api/v1/auth.py
@router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest, session: AsyncSession = Depends(get_db_session)):
    auth_service = AuthService(session)
    try:
        user = await auth_service.create_user(request)
        return auth_service.to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/auth/login", response_model=Token)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    auth_service = AuthService(session)
    user = await auth_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return Token(access_token=access_token, token_type="bearer", expires_in=get_token_expiry_seconds())
```

**Location:** `backend/api/v1/auth.py`

### 5. Dependency Injection for Auth

**Decision:** Use FastAPI dependencies for authentication and authorization.

**Rationale:**
- Clean separation of concerns
- Reusable across endpoints
- Automatic OpenAPI security documentation
- Easy to test with dependency overrides

**Implementation:**
```python
# backend/api/dependencies.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), ...) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    payload = decode_access_token(token)
    # ... validate and return user

async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
```

**Location:** `backend/api/dependencies.py`

## Consequences

### Positive

- **Security**: Passwords are never stored in plain text
- **Scalability**: Stateless JWT tokens work well with horizontal scaling
- **Flexibility**: Easy to add new roles or permissions
- **Standards-compliant**: OAuth2 Bearer token format
- **Testability**: Dependencies can be easily mocked in tests

### Negative

- **Token revocation**: JWTs cannot be easily revoked before expiration
- **Token size**: JWTs are larger than session IDs
- **Secret management**: JWT secret must be securely managed
- **No built-in refresh**: Token refresh must be implemented separately

## Alternatives Considered

### Alternative 1: Session-based Authentication

Use server-side sessions with cookies.

**Rejected:**
- Requires session storage (Redis/database)
- Harder to scale horizontally
- Not ideal for API-first architecture
- More complex with async FastAPI

### Alternative 2: API Keys

Use static API keys for authentication.

**Rejected:**
- No built-in expiration
- Harder to implement role-based access
- Less secure for user authentication
- Better suited for service-to-service auth

### Alternative 3: OAuth2/OpenID Connect

Use external identity providers.

**Rejected:**
- Adds external dependency
- More complex setup
- Overkill for MVP
- Can be added later as an option

## Implementation Notes

### Dependencies

```toml
# Using PyJWT (already installed)
# No additional dependencies required for basic JWT
```

### API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login and get token | No |
| GET | `/api/v1/auth/me` | Get current user info | Yes |
| POST | `/api/v1/auth/admin/register` | Register admin user | Admin only |

### Testing Strategy

```bash
# Run auth tests
pytest tests/unit/crd_backend/api/test_auth.py -v

# Run with coverage
pytest tests/unit/crd_backend/api/test_auth.py --cov=backend.core --cov=backend.api
```

**Test Categories:**
- Registration tests (4 tests)
- Login tests (4 tests)
- Current user tests (3 tests)
- Admin registration tests (3 tests)
- JWT token tests (6 tests)
- Protected endpoint tests (4 tests)
- **Total: 24 tests**

### Security Considerations

1. **JWT Secret**: Change `SECRET_KEY` in production
2. **Token Expiration**: Default 30 minutes, configurable
3. **Password Policy**: Minimum 8 characters enforced
4. **HTTPS**: Always use HTTPS in production
5. **CORS**: Configure appropriately for frontend

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [OAuth2 Bearer Token](https://oauth.net/2/bearer-tokens/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
