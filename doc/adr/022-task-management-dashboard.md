# ADR 022: Task Management Dashboard

## Status

Accepted

## Context

Epic 22 required implementing a comprehensive task management interface for the Wegent platform. The backend already provided a complete Task Management API (Epic 12) with endpoints for creating, monitoring, and controlling task execution. The frontend needed:

1. A task list view with real-time status updates
2. Task creation with team selection
3. Task detail view showing execution logs, input, and output
4. Task lifecycle actions (execute, cancel, delete)
5. Status filtering and search capabilities
6. Integration with the existing Team resources for task assignment

The challenge was designing an architecture that would:
- Provide real-time visibility into task execution status
- Handle long-running tasks with polling updates
- Integrate task management with the existing resource management patterns
- Support task execution through the chat_shell integration

## Decision

### 1. Dedicated Task API Service

**Decision:** Create a separate `taskApi` service (`frontend/src/services/tasks.ts`) rather than using the generic resource API pattern.

**Rationale:**
- Tasks have unique endpoints (e.g., `/tasks/{id}/execute`, `/tasks/{id}/status`) not following the standard CRD pattern
- Task operations include lifecycle actions (start, complete, fail, cancel) distinct from CRUD
- Tasks use UUID-based identification rather than name+namespace composite keys

**Service Design:**

```typescript
export const taskApi = {
  list: async (options: ListTasksOptions = {}): Promise<TaskResponse[]> => {
    const params = new URLSearchParams();
    if (options.namespace) params.append("namespace", options.namespace);
    if (options.status) params.append("status", options.status);
    if (options.teamId) params.append("team_id", options.teamId);
    // ...
  },
  get: async (taskId: string): Promise<TaskResponse> =>
    api.get(`/tasks/${taskId}`),
  create: async (data: TaskCreateRequest): Promise<TaskResponse> =>
    api.post("/tasks", data),
  updateStatus: async (taskId: string, update: TaskStatusUpdate) =>
    api.patch(`/tasks/${taskId}/status`, update),
  cancel: async (taskId: string): Promise<TaskResponse> =>
    updateStatus(taskId, { status: "cancelled" }),
  delete: async (taskId: string): Promise<void> =>
    api.delete(`/tasks/${taskId}`),
  execute: async (taskId: string, options?: { botName?: string }) =>
    api.post(`/tasks/${taskId}/execute?${params}`),
};
```

**Location:** `frontend/src/services/tasks.ts`

### 2. Real-Time Status Updates via Polling

**Decision:** Implement polling-based real-time updates in the `useTasks` hook rather than WebSocket integration for the initial implementation.

**Rationale:**
- Tasks API already provides polling-friendly endpoints
- Polling is simpler to implement and debug than WebSocket connections
- 3-second polling interval provides good balance between freshness and server load
- WebSocket integration can be added later for more advanced real-time features

**Hook Design:**

```typescript
export function useTasks(options: UseTasksOptions = {}): UseTasksReturn {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const runningTasksRef = useRef<Set<string>>(new Set());

  // Track running tasks for selective polling
  useEffect(() => {
    runningTasksRef.current = new Set(
      tasks.filter((t) => t.status === "running").map((t) => t.id)
    );
  }, [tasks]);

  // Real-time polling for running tasks
  useEffect(() => {
    if (!options.enableRealtime) return;
    const intervalId = setInterval(() => {
      if (runningTasksRef.current.size > 0) {
        fetchTasks();
      }
    }, 3000);
    return () => clearInterval(intervalId);
  }, [fetchTasks, options.enableRealtime]);
}
```

**Location:** `frontend/src/hooks/useTasks.ts`

### 3. Status-Based UI Actions

**Decision:** Implement conditional action buttons based on task status, showing only relevant actions for each state.

**Rationale:**
- Prevents user confusion by hiding irrelevant actions
- Enforces task lifecycle constraints in the UI
- Provides clear visual feedback about available operations

**Implementation:**

```typescript
// Execute only for pending tasks
{task.status === "pending" && (
  <Button icon={<PlayCircleOutlined />} onClick={handleExecute}>
    Execute
  </Button>
)}

// Cancel only for running tasks
{task.status === "running" && (
  <Button danger icon={<StopOutlined />} onClick={handleCancel}>
    Cancel
  </Button>
)}
```

**Location:** `frontend/src/app/(dashboard)/tasks/page.tsx`

### 4. Task Detail View with Execution Timeline

**Decision:** Create a dedicated task detail page with an execution timeline showing task lifecycle events.

**Rationale:**
- Provides comprehensive task execution visibility
- Timeline visualization helps users understand task progression
- Centralized location for task input, output, and error details

**Timeline Implementation:**

```typescript
const timelineItems = [
  { dot: <ClockCircleOutlined />, children: <div>Created: {createdAt}</div> },
  task.startedAt && {
    dot: <PlayCircleOutlined style={{ color: "#52c41a" }} />,
    color: "green",
    children: <div>Started: {startedAt}</div>,
  },
  task.status === "completed" && {
    dot: <CheckCircleOutlined style={{ color: "#52c41a" }} />,
    children: <div>Completed: {completedAt}</div>,
  },
  // ... failed, cancelled states
];
```

**Location:** `frontend/src/app/(dashboard)/tasks/[id]/page.tsx`

### 5. Team Integration for Task Creation

**Decision:** Integrate team selection into task creation using the existing `useTeams` hook pattern.

**Rationale:**
- Tasks can be assigned to teams for coordinated execution
- Reuses existing team fetching logic
- Provides dropdown with team names for better UX

**Implementation:**

```typescript
const { teams } = useTeams();

// Team selection in create modal
<Form.Item name="teamId" label="Team (Optional)">
  <Select placeholder="Select a team" allowClear>
    {teams.map((team) => (
      <Option key={team.id} value={team.id}>
        {team.metadata.name} ({team.metadata.namespace})
      </Option>
    ))}
  </Select>
</Form.Item>
```

**Location:** `frontend/src/components/tasks/TaskCreateModal.tsx`

### 6. Reuse ResourceList Component

**Decision:** Reuse the existing `ResourceList` component from Epic 21 for the task list view.

**Rationale:**
- Maintains consistent UI patterns across the application
- Reduces code duplication
- Leverages existing pagination, search, and namespace filtering

**Implementation:**

```typescript
<ResourceList<TaskListItem>
  title="Tasks"
  resources={taskListItems}
  loading={loading}
  total={total}
  currentNamespace={currentNamespace}
  namespaces={namespaces}
  columns={columns}
  onCreate={() => setCreateModalOpen(true)}
  // ...
/>
```

**Location:** `frontend/src/app/(dashboard)/tasks/page.tsx`

## Consequences

### Positive

- **Real-time Visibility**: Polling provides near real-time updates for running tasks without WebSocket complexity
- **Lifecycle Enforcement**: Status-based UI actions prevent invalid state transitions
- **Consistent UX**: Reusing ResourceList maintains familiar interface patterns
- **Team Integration**: Tasks can be organized by teams for multi-agent coordination
- **Execution Visibility**: Timeline and input/output display provide comprehensive task monitoring
- **Modular Design**: Separate taskApi service allows independent evolution of task management features

### Negative

- **Polling Overhead**: 3-second polling creates continuous server load even when no tasks are running
- **Delayed Updates**: Polling interval means status changes may not appear immediately
- **No True Real-time**: WebSocket would provide instant updates for task events
- **Limited Concurrency**: High task volume with many running tasks could strain the polling mechanism

## Alternatives Considered

### Alternative 1: WebSocket-Based Real-time Updates

Use WebSocket connections for true real-time task status updates.

**Rejected:**
- More complex implementation requiring WebSocket client setup
- Backend WebSocket endpoints for task events not yet fully implemented
- Polling provides sufficient real-time behavior for MVP requirements
- Can be added later as an enhancement

### Alternative 2: Unified Resource API Pattern

Use the same generic CRUD pattern as Ghost, Model, Shell, etc. for tasks.

**Rejected:**
- Tasks have unique lifecycle operations (execute, cancel) not fitting CRUD pattern
- Tasks use UUID identifiers rather than name+namespace keys
- Task status transitions require specialized handling

### Alternative 3: Inline Task Creation

Embed task creation form directly in the task list page rather than a modal.

**Rejected:**
- Modal provides cleaner separation of concerns
- Task creation requires multiple fields (name, namespace, team, input)
- Modal allows for future expansion with more complex task configuration

## Implementation Notes

### Dependencies

No new dependencies required. Uses existing:
- `antd` for UI components (Timeline, Badge, Card, Descriptions)
- `@ant-design/icons` for status icons
- React hooks (useState, useEffect, useRef, useCallback)

### Testing Strategy

```bash
# Run task management tests
cd frontend && npm test -- ../tests/frontend/tasks.test.ts

# All 56 tests passing:
# - Task API service: 11 tests
# - useTasks hook: 12 tests
# - Tasks page: 11 tests
# - Task detail page: 10 tests
# - Task create modal: 7 tests
# - Tasks navigation: 2 tests
# - useTeams hook: 3 tests
```

### Key Files

| File | Purpose |
|------|---------|
| `frontend/src/services/tasks.ts` | Task API service functions |
| `frontend/src/hooks/useTasks.ts` | Task management hook with polling |
| `frontend/src/hooks/useTeams.ts` | Team fetching for task creation |
| `frontend/src/app/(dashboard)/tasks/page.tsx` | Task list page |
| `frontend/src/app/(dashboard)/tasks/[id]/page.tsx` | Task detail page |
| `frontend/src/components/tasks/TaskCreateModal.tsx` | Task creation modal |
| `frontend/src/app/(dashboard)/layout.tsx` | Updated with Tasks navigation |
| `tests/frontend/tasks.test.ts` | 56 task management tests |

## References

- Epic 12: Task Management API (`doc/adr/012-task-management-api.md`)
- Epic 17: Real-time Event Broadcasting (`doc/adr/017-real-time-event-broadcasting.md`)
- Epic 18: Chat Execution Engine Integration (`doc/adr/018-chat-execution-engine-integration.md`)
- Epic 21: CRD Resource Management UI (`doc/adr/021-crd-resource-management-ui.md`)
