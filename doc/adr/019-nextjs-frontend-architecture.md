# ADR 019: Next.js Frontend Architecture

## Status

Accepted

## Context

The Wegent platform needed a modern frontend implementation to replace the existing vanilla HTML/CSS/JS frontend (Phase 1). The Frontend MVP requirements specified a Next.js 15 + React 19 + TypeScript implementation with the following key requirements:

1. **Modern Stack**: Next.js 15 with App Router, React 19, TypeScript
2. **UI Framework**: Ant Design 5 for consistent, enterprise-grade components
3. **Styling**: Tailwind CSS 3 for utility-first styling with custom theme
4. **State Management**: React Context for authentication state
5. **HTTP Client**: Axios with interceptors for API communication
6. **Real-time**: Socket.io-client for WebSocket connections

The existing vanilla frontend at `frontend/` provided basic CRUD operations but lacked:
- Type safety
- Component reusability
- Modern development experience
- Scalable architecture
- Proper state management

## Decision

### 1. Framework Selection: Next.js 15 with App Router

**Decision:** Use Next.js 15 with the App Router pattern instead of Pages Router.

**Rationale:**
- App Router provides better performance with Server Components
- Built-in layout support for dashboard structure
- Simplified data fetching patterns
- Future-proof architecture (Pages Router is legacy)

**Project Structure:**
```
frontend/src/app/
├── (dashboard)/           # Route group for authenticated pages
│   ├── layout.tsx         # Dashboard layout with sidebar
│   ├── page.tsx           # Dashboard home
│   ├── ghosts/page.tsx
│   ├── models/page.tsx
│   ├── shells/page.tsx
│   ├── bots/page.tsx
│   ├── teams/page.tsx
│   └── skills/page.tsx
├── login/page.tsx         # Login page (unauthenticated)
├── layout.tsx             # Root layout with providers
└── globals.css            # Global styles
```

**Location:** `frontend/src/app/`

### 2. TypeScript Configuration

**Decision:** Use strict TypeScript with path aliases.

**Rationale:**
- Type safety across the entire application
- Better IDE support and autocomplete
- Path aliases (`@/*`) simplify imports
- Strict mode catches potential errors early

**Configuration:**
```json
{
  "compilerOptions": {
    "strict": true,
    "jsx": "preserve",
    "esModuleInterop": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Location:** `frontend/tsconfig.json`

### 3. UI Framework: Ant Design 5

**Decision:** Use Ant Design 5 as the primary UI component library.

**Rationale:**
- Enterprise-grade components (Table, Form, Modal, etc.)
- Built-in TypeScript support
- Comprehensive theming system
- Good documentation and community

**Theme Configuration:**
```typescript
const antdTheme = {
  token: {
    colorPrimary: "#1890ff",
    colorSuccess: "#52c41a",
    colorWarning: "#faad14",
    colorError: "#f5222d",
    borderRadius: 6,
  },
};
```

**Location:** `frontend/src/app/layout.tsx`

### 4. Styling: Tailwind CSS 3 + Custom Theme

**Decision:** Use Tailwind CSS 3 with custom colors matching Ant Design.

**Rationale:**
- Utility-first approach for rapid styling
- Custom theme aligns with Ant Design colors
- Responsive design utilities
- No runtime CSS-in-JS overhead

**Configuration:**
```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1890ff",
          50: "#e6f7ff",
          // ... 50-900 shades
        },
        success: { DEFAULT: "#52c41a", ... },
        warning: { DEFAULT: "#faad14", ... },
        error: { DEFAULT: "#f5222d", ... },
      },
    },
  },
};
```

**Location:** `frontend/tailwind.config.ts`

### 5. HTTP Client: Axios with Interceptors

**Decision:** Use Axios with request/response interceptors for API communication.

**Rationale:**
- Request interceptor adds JWT token automatically
- Response interceptor handles 401/403 errors
- Centralized error handling
- Type-safe API responses

**Implementation:**
```typescript
// Request interceptor - add JWT token
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token.accessToken}`;
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logout();
    }
    return Promise.reject(error);
  }
);
```

**Location:** `frontend/src/services/api.ts`

### 6. Authentication: React Context + localStorage

**Decision:** Use React Context for auth state with localStorage persistence.

**Rationale:**
- Simple, no external state management library needed
- Token persistence across page refreshes
- ProtectedRoute wrapper for authenticated routes
- Easy to extend with refresh token logic

**Implementation:**
```typescript
interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// ProtectedRoute component
export function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  // Redirect to login if not authenticated
}
```

**Location:** `frontend/src/context/auth-context.tsx`

### 7. TypeScript Types

**Decision:** Create comprehensive TypeScript types based on backend schemas.

**Rationale:**
- Type safety across frontend-backend boundary
- Single source of truth for data structures
- Better IDE autocomplete and error detection

**Type Categories:**
- `auth.ts` - Token, User, LoginRequest types
- `resources.ts` - Ghost, Model, Shell, Bot, Team, Skill types
- `task.ts` - Task types
- `message.ts` - Message types
- `session.ts` - Session types
- `chat.ts` - Chat types

**Location:** `frontend/src/types/`

### 8. API Services

**Decision:** Organize API calls into service modules.

**Rationale:**
- Clean separation of concerns
- Reusable API methods
- Easy to mock for testing

**Structure:**
```typescript
// services/api.ts - Axios instance
// services/auth.ts - Auth API (login, register, me)
// services/resources.ts - CRUD APIs for all resource types
```

**Location:** `frontend/src/services/`

## Consequences

### Positive

- **Type Safety**: Full TypeScript coverage prevents runtime errors
- **Modern DX**: Next.js 15 + React 19 provides excellent developer experience
- **Component Reusability**: Ant Design + custom components are reusable
- **Scalable Architecture**: App Router pattern supports future growth
- **Consistent Styling**: Tailwind + Ant Design theme ensures visual consistency
- **Secure Auth**: JWT tokens with automatic handling

### Negative

- **Bundle Size**: Ant Design adds ~200KB to bundle (acceptable trade-off)
- **Learning Curve**: Team needs to learn Next.js App Router patterns
- **Build Time**: Type checking adds to build time
- **Node Version**: Next.js 15 requires Node.js 18.17+ (documented requirement)

## Alternatives Considered

### Alternative 1: Keep Vanilla HTML/CSS/JS

**Description:** Continue using the existing vanilla frontend.

**Rejected:**
- No type safety
- Manual DOM manipulation is error-prone
- Hard to maintain as features grow
- No component reusability

### Alternative 2: Use Vite + React (without Next.js)

**Description:** Use Vite as the build tool with plain React.

**Rejected:**
- No built-in routing (need react-router)
- No built-in API routes
- No Server Components
- Less optimized for production

### Alternative 3: Use Pages Router instead of App Router

**Description:** Use Next.js but with the legacy Pages Router.

**Rejected:**
- Pages Router is in maintenance mode
- No Server Components support
- Less optimal performance
- App Router is the future of Next.js

### Alternative 4: Use Redux for State Management

**Description:** Use Redux Toolkit for authentication state.

**Rejected:**
- Overkill for simple auth state
- React Context is sufficient
- Redux adds bundle size and complexity

## Implementation Notes

### Dependencies

```json
{
  "dependencies": {
    "next": "^15.5.12",
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "antd": "^6.2.3",
    "axios": "^1.13.5",
    "socket.io-client": "^4.8.3"
  },
  "devDependencies": {
    "typescript": "^5",
    "tailwindcss": "^3.4.19",
    "jest": "^29.7.0"
  }
}
```

### Testing Strategy

```bash
# Run frontend tests
cd frontend/
npm test

# Run all tests including backend
pytest tests/
```

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Build Commands

```bash
# Development server
npm run dev

# Production build
npm run build

# Run tests
npm test

# Lint
npm run lint
```

## References

- [Next.js 15 Documentation](https://nextjs.org/docs)
- [React 19 Documentation](https://react.dev/)
- [Ant Design 5 Documentation](https://ant.design/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Epic 19 Implementation Plan](../epics/019-frontend-project-setup.md)
