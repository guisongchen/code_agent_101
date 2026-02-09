# ADR 020: Authentication and User Management

## Status

Accepted

## Context

Epic 20 focuses on implementing a complete user authentication system for the Wegent frontend. The requirements included:

1. **Login Page**: Username/password form with validation
2. **Registration Page**: User signup with email validation
3. **JWT Token Management**: Secure storage and handling
4. **Protected Routes**: Route-level authentication guards
5. **Token Refresh**: Automatic token expiration handling
6. **Error Handling**: User-friendly error messages

The backend already provides authentication endpoints (`/auth/login`, `/auth/register`, `/auth/me`) with JWT token-based authentication. The frontend needed to integrate with these endpoints and provide a seamless user experience.

## Decision

### 1. React Context for Auth State

**Decision:** Use React Context API for global authentication state management.

**Rationale:**
- Simple and built into React (no external dependencies)
- Sufficient for auth state (user, token, loading states)
- Easy to access via `useAuth()` hook throughout the app
- Avoids prop drilling

**Implementation:**
```typescript
interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
```

**Location:** `frontend/src/context/auth-context.tsx`

### 2. localStorage for Token Persistence

**Decision:** Store JWT tokens in localStorage for persistence across page refreshes.

**Rationale:**
- Tokens persist across browser sessions
- Simple to implement
- Works with SSR (checked on client-side only)
- Token expiration handled separately

**Implementation:**
```typescript
export function storeToken(token: Token): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("token", JSON.stringify(token));
  }
}

export function getToken(): Token | null {
  if (typeof window === "undefined") return null;
  const tokenStr = localStorage.getItem("token");
  // ... parse and return
}
```

**Location:** `frontend/src/services/auth.ts`

### 3. ProtectedRoute Component

**Decision:** Create a `ProtectedRoute` wrapper component for authenticated pages.

**Rationale:**
- Declarative way to protect routes
- Handles loading states and redirects
- Reusable across all authenticated pages
- Integrates with Next.js App Router

**Implementation:**
```typescript
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated) return null;
  return <>{children}</>;
}
```

**Location:** `frontend/src/context/auth-context.tsx`

### 4. Token Expiration Checking

**Decision:** Implement client-side token expiration checking with automatic logout.

**Rationale:**
- Backend returns `expires_in` with tokens
- Proactive expiration prevents failed API calls
- Interval check ensures timely logout
- Buffer time (60s) prevents edge cases

**Implementation:**
```typescript
function isTokenExpired(token: Token): boolean {
  const bufferSeconds = 60;
  const expiryTime = Date.now() + (token.expiresIn * 1000) - (bufferSeconds * 1000);
  return Date.now() >= expiryTime;
}

// Check every minute
useEffect(() => {
  const interval = setInterval(() => {
    if (token && isTokenExpired(token)) {
      logout();
    }
  }, 60000);
  return () => clearInterval(interval);
}, [token]);
```

**Location:** `frontend/src/context/auth-context.tsx`

### 5. Separate Login and Registration Pages

**Decision:** Create separate `/login` and `/register` pages with cross-links.

**Rationale:**
- Clear separation of concerns
- Different form validations
- Better UX (focused tasks)
- SEO-friendly separate URLs

**Implementation:**
```
/frontend/src/app/
├── login/
│   └── page.tsx       # Login form
└── register/
    └── page.tsx       # Registration form
```

**Location:** `frontend/src/app/login/page.tsx`, `frontend/src/app/register/page.tsx`

### 6. Form Validation Strategy

**Decision:** Use Ant Design Form validation with custom rules.

**Rationale:**
- Built-in validation in Ant Design
- Real-time feedback to users
- Consistent error display
- Password confirmation matching

**Implementation:**
```typescript
<Form.Item
  name="password"
  rules={[
    { required: true, message: "Please enter your password" },
    { min: 8, message: "Password must be at least 8 characters" },
  ]}
>
  <Input.Password prefix={<LockOutlined />} placeholder="Password" />
</Form.Item>
```

**Location:** `frontend/src/app/register/page.tsx`

## Consequences

### Positive

- **Secure Authentication**: JWT tokens with expiration checking
- **Good UX**: Clear login/register flows with validation
- **Maintainable**: Centralized auth logic in context
- **Type Safe**: TypeScript types for all auth operations
- **Testable**: 34 tests covering auth functionality
- **Responsive**: Works on mobile and desktop

### Negative

- **localStorage Limitations**: Vulnerable to XSS (mitigated by httpOnly cookies on backend)
- **No Refresh Tokens**: Access token expiry requires re-login
- **Client-Side Only**: Token check only runs in browser

## Alternatives Considered

### Alternative 1: Redux for Auth State

**Description:** Use Redux Toolkit for authentication state management.

**Rejected:**
- Overkill for simple auth state
- Adds bundle size (~20KB)
- More boilerplate code
- Context API is sufficient

### Alternative 2: httpOnly Cookies

**Description:** Store tokens in httpOnly cookies instead of localStorage.

**Rejected:**
- Requires backend changes
- More complex CSRF protection needed
- localStorage is acceptable for this use case
- XSS risk mitigated by short token expiry

### Alternative 3: Single Auth Page with Tabs

**Description:** Combine login and register on one page with tabs.

**Rejected:**
- Less clear UX
- Harder to link directly to register
- SEO less effective
- Separate pages are cleaner

### Alternative 4: Silent Token Refresh

**Description:** Automatically refresh tokens before expiry.

**Rejected:**
- Backend doesn't support refresh tokens yet
- Would require backend changes
- Current interval check is sufficient for MVP

## Implementation Notes

### Dependencies

```json
{
  "dependencies": {
    "antd": "^6.2.3",
    "axios": "^1.13.5"
  }
}
```

### Testing Strategy

```bash
# Run frontend tests
cd frontend/
npm test

# Test output
Test Suites: 2 passed (project-setup, auth)
Tests:       68 passed (34 + 34)
```

### Test Coverage

| Category | Tests |
|----------|-------|
| Login Page | 5 tests |
| Registration Page | 6 tests |
| Auth Context | 12 tests |
| Protected Route | 3 tests |
| Auth Services | 6 tests |
| Navigation | 2 tests |
| **Total** | **34 tests** |

### API Integration

```typescript
// Login
POST /api/v1/auth/login
Body: { username: string, password: string }
Response: { accessToken: string, tokenType: string, expiresIn: number }

// Register
POST /api/v1/auth/register
Body: { username: string, email: string, password: string, defaultNamespace: string }
Response: UserResponse

// Get Current User
GET /api/v1/auth/me
Headers: Authorization: Bearer <token>
Response: UserResponse
```

## References

- [Epic 20 Implementation](../epic/frontend_mvp.md#epic-20-authentication-and-user-management)
- [React Context Documentation](https://react.dev/reference/react/useContext)
- [Ant Design Form Validation](https://ant.design/components/form#form-demo-validate-static)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-jwt-bcp)
