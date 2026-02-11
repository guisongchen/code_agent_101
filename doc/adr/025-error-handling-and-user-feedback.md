# ADR 025: Error Handling and User Feedback

## Status

Accepted

## Context

The Wegent frontend application needed a comprehensive error handling and user feedback system to provide a robust user experience. Without proper error handling, users would encounter:

- Unhandled JavaScript crashes that break the entire application
- Confusing error messages from API failures
- No visual feedback during loading states
- Unclear validation errors on forms
- Silent failures when network connectivity is lost
- Accidental destructive actions without confirmation

The requirements for this epic included:
1. Graceful error recovery from component crashes
2. Consistent user feedback through notifications
3. Loading states to improve perceived performance
4. Custom error pages for 404 and 500 errors
5. Form validation with clear error messages
6. API error handling with retry logic
7. Network status detection and user notification
8. Confirmation dialogs for destructive actions

## Decision

### 1. React Error Boundaries for Crash Handling

**Decision:** Implement React class-based Error Boundaries to catch JavaScript errors in child components and display a fallback UI.

**Rationale:**
- Error boundaries are the standard React pattern for graceful error recovery
- Prevents entire application crashes from single component failures
- Provides users with actionable options (retry, go home, reload)
- Allows error details to be displayed for debugging

**Implementation:**
```typescript
// frontend/src/components/error/ErrorBoundary.tsx
export class ErrorBoundary extends Component<Props, State> {
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }
}
```

**Location:** `frontend/src/components/error/ErrorBoundary.tsx`

### 2. Next.js Error Pages

**Decision:** Use Next.js error.tsx convention for route-level error handling and a custom not-found.tsx for 404 errors.

**Rationale:**
- Next.js provides built-in error handling conventions
- error.tsx catches errors in specific route segments
- not-found.tsx handles 404 errors for non-existent routes
- Allows different error UIs for different parts of the application

**Implementation:**
- `frontend/src/app/error.tsx` - Root error boundary
- `frontend/src/app/(dashboard)/error.tsx` - Dashboard-specific errors
- `frontend/src/app/not-found.tsx` - 404 Not Found page

### 3. Ant Design Message API for Notifications

**Decision:** Use Ant Design's built-in `message` API for toast notifications rather than building a custom system.

**Rationale:**
- Ant Design is already the primary UI library
- Message API provides consistent styling with the rest of the application
- Supports success, error, warning, info, and loading states
- No additional dependencies required

**Usage:**
```typescript
import { message } from "antd";

message.success("Task created successfully");
message.error("Failed to fetch tasks");
message.warning("You are offline");
```

### 4. Custom Hooks for Error Handling

**Decision:** Create reusable hooks for consistent error handling patterns across the application.

**Rationale:**
- Hooks provide a clean, reusable abstraction
- Centralizes error handling logic
- Makes testing easier by isolating error handling
- Supports both simple and complex use cases

**Implementation:**

**useErrorHandler** - Wraps async functions with error handling and retry logic:
```typescript
// frontend/src/hooks/useErrorHandler.ts
export function useErrorHandler<T = unknown>(
  asyncFunction: (...args: unknown[]) => Promise<T>,
  options: UseErrorHandlerOptions = {}
): UseErrorHandlerReturn<T>
```

**useFormErrorHandler** - Form-specific error handling with field-level errors:
```typescript
export function useFormErrorHandler(): UseFormErrorHandlerReturn
```

**Location:** `frontend/src/hooks/useErrorHandler.ts`

### 5. Skeleton Screens for Loading States

**Decision:** Implement skeleton screen components using Ant Design's Skeleton component for various UI patterns.

**Rationale:**
- Improves perceived performance
- Reduces layout shift during loading
- Provides visual feedback that content is loading
- Better user experience than spinners for content-heavy pages

**Implementation:**
```typescript
// frontend/src/components/ui/SkeletonScreens.tsx
export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps)
export function FormSkeleton({ fields = 6 }: FormSkeletonProps)
export function DashboardSkeleton()
export function ChatSkeleton({ messages = 5 }: ChatSkeletonProps)
```

**Location:** `frontend/src/components/ui/SkeletonScreens.tsx`

### 6. Form Validation Utilities

**Decision:** Create a comprehensive validation utility with predefined rules and presets for common field types.

**Rationale:**
- Ensures consistent validation across all forms
- Supports Kubernetes naming conventions for CRD resources
- Provides clear, user-friendly error messages
- Integrates easily with Ant Design forms

**Implementation:**
```typescript
// frontend/src/utils/validation.ts
export const validationPresets = {
  username: [...],
  password: [...],
  email: [...],
  resourceName: [...],  // Kubernetes DNS subdomain names
  namespace: [...],
};

export function validateValue(value: unknown, rules: ValidationRules, fieldName: string)
export function createValidationRule(rules: ValidationRules, fieldName: string)
```

**Location:** `frontend/src/utils/validation.ts`

### 7. Network Status Detection

**Decision:** Implement a hook that detects online/offline status using browser APIs and provides user notifications.

**Rationale:**
- Users need to know when they lose connectivity
- Allows graceful degradation of features
- Provides retry mechanisms when connection is restored
- Uses standard browser `online`/`offline` events

**Implementation:**
```typescript
// frontend/src/hooks/useNetworkStatus.ts
export function useNetworkStatus(options: UseNetworkStatusOptions = {}): NetworkStatus

// Returns:
interface NetworkStatus {
  isOnline: boolean;
  wasOffline: boolean;
  checkConnection: () => Promise<boolean>;
}
```

**Location:** `frontend/src/hooks/useNetworkStatus.ts`

### 8. Confirmation Dialogs

**Decision:** Create a flexible confirmation dialog system with variants for different use cases.

**Rationale:**
- Prevents accidental destructive actions
- Provides consistent dialog styling
- Supports async operations with loading states
- Multiple convenience functions for common patterns

**Implementation:**
```typescript
// frontend/src/components/ui/ConfirmDialog.tsx
export function useConfirmDialog() // Hook-based usage
export function confirm(options: ConfirmDialogOptions): Promise<boolean> // Static usage
export function confirmDelete(itemName: string): Promise<boolean>
export function confirmUnsavedChanges(): Promise<boolean>
```

**Location:** `frontend/src/components/ui/ConfirmDialog.tsx`

## Consequences

### Positive

- **Graceful Degradation:** Application remains usable even when components crash or network is unavailable
- **Consistent User Experience:** All error handling follows the same patterns and styling
- **Better Perceived Performance:** Skeleton screens make the application feel faster
- **Reduced User Errors:** Confirmation dialogs prevent accidental destructive actions
- **Developer Productivity:** Reusable hooks and utilities reduce code duplication
- **Maintainability:** Centralized error handling makes updates easier

### Negative

- **Bundle Size:** Additional error handling code increases bundle size (minimal impact)
- **Complexity:** More abstraction layers can make debugging slightly more complex
- **Learning Curve:** Developers need to understand the error handling patterns

## Alternatives Considered

### Alternative 1: react-error-boundary Library

**Description:** Use the popular `react-error-boundary` npm package instead of custom implementation.

**Rejected:**
- Adds unnecessary dependency when React provides built-in error boundaries
- Custom implementation allows for project-specific error UI
- Easy to implement with minimal code

### Alternative 2: Custom Toast Notification System

**Description:** Build a custom toast notification component instead of using Ant Design's message API.

**Rejected:**
- Would duplicate functionality already provided by Ant Design
- Additional maintenance burden
- Inconsistent styling with the rest of the application

### Alternative 3: react-query for Error Handling

**Description:** Use react-query (TanStack Query) for server state management and error handling.

**Rejected:**
- Would require significant refactoring of existing API layer
- Adds complexity for a problem already solved by custom hooks
- Current axios-based approach is sufficient for our needs

## Implementation Notes

### Dependencies

No new dependencies required. All implementations use:
- React (built-in Error Boundaries)
- Next.js (error.tsx convention)
- Ant Design (message, Skeleton, Modal components)

### Testing Strategy

```bash
# Run error handling tests
cd frontend && npm test -- ../tests/frontend/error-handling.test.ts

# Run all frontend tests
cd frontend && npm test
```

**Test Coverage:**
- Error Boundary component tests (2 tests)
- Toast notification tests (2 tests)
- Form validation tests (3 tests)
- Error handling component tests (13 tests)
- **Total: 20 tests passing**

### Usage Examples

**Error Boundary:**
```tsx
import { ErrorBoundary } from "@/components/error";

<ErrorBoundary>
  <MyComponent />
</ErrorBoundary>
```

**Error Handler Hook:**
```typescript
const { execute, loading, error } = useErrorHandler(fetchData);

// Usage
await execute();
```

**Skeleton Screen:**
```tsx
{loading ? <TableSkeleton rows={5} /> : <Table data={data} />}
```

**Form Validation:**
```typescript
<Form.Item
  name="username"
  rules={validationPresets.username}
>
  <Input />
</Form.Item>
```

**Confirmation Dialog:**
```typescript
const confirmed = await confirmDelete("my-resource");
if (confirmed) {
  await deleteResource("my-resource");
}
```

## References

- [React Error Boundaries Documentation](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [Next.js Error Handling](https://nextjs.org/docs/app/building-your-application/routing/error-handling)
- [Ant Design Message API](https://ant.design/components/message)
- [Ant Design Skeleton](https://ant.design/components/skeleton)
- [MDN Online/Offline Events](https://developer.mozilla.org/en-US/docs/Web/API/Window/online_event)
