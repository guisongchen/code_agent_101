# ADR 021: CRD Resource Management UI

## Status

Accepted

## Context

Epic 21 required implementing CRUD interfaces for all CRD (Custom Resource Definition) resources in the Wegent platform: Ghost, Model, Shell, Bot, Team, and Skill. The backend already provided RESTful APIs for these resources through a consistent pattern (list, create, update, delete with namespace support). The frontend needed:

1. A consistent UI pattern for managing all 6 resource types without code duplication
2. Namespace-based resource isolation (multi-tenancy support)
3. Search, filtering, and pagination for resource lists
4. Form-based creation and editing with YAML spec support
5. Delete confirmation to prevent accidental data loss
6. Responsive design using Ant Design components

The challenge was designing an architecture that would avoid duplicating similar code across 6 resource pages while maintaining flexibility for resource-specific columns and behaviors.

## Decision

### 1. Reusable Component Architecture

**Decision:** Create two reusable components (`ResourceList` and `ResourceForm`) that can be configured for any resource type, paired with a custom hook (`useResources`) for CRUD operations.

**Rationale:**
- Eliminates code duplication across 6 resource pages
- Ensures consistent UX patterns (search, pagination, delete confirmation)
- Makes future resource types easy to add with minimal code
- Centralizes common logic (loading states, error handling, namespace filtering)

**Component Design:**

```typescript
// ResourceList - Configurable table with common features
export interface ResourceListProps<T> {
  title: string;
  resources: T[];
  loading: boolean;
  total: number;
  currentNamespace: string;
  namespaces: string[];
  columns: ColumnsType<T>;
  onCreate: () => void;
  onEdit: (item: T) => void;
  onDelete: (item: T) => void;
  onNamespaceChange: (namespace: string) => void;
  onSearch?: (value: string) => void;
  createButtonText?: string;
}

// ResourceForm - Modal form with tabs for Basic Info and Spec
export interface ResourceFormData {
  metadata: {
    name: string;
    namespace: string;
    description?: string;
  };
  spec: Record<string, unknown>;
}

export interface ResourceFormProps {
  title: string;
  open: boolean;
  resource?: ResourceFormData;
  namespaces: string[];
  onSubmit: (values: ResourceFormData) => void;
  onCancel: () => void;
}
```

**Location:**
- `frontend/src/components/resources/ResourceList.tsx`
- `frontend/src/components/resources/ResourceForm.tsx`
- `frontend/src/components/resources/index.ts`

### 2. Custom Hook for CRUD Operations

**Decision:** Implement `useResources` hook that accepts resource-specific API functions and provides unified state management.

**Rationale:**
- Separates data fetching logic from UI components
- Provides consistent loading states and error handling
- Manages namespace filtering automatically
- Extracts unique namespaces from resources for the filter dropdown

**Hook Design:**

```typescript
export function useResources<T extends { name: string; namespace: string }>({
  listFn,
  createFn,
  updateFn,
  deleteFn,
}: UseResourcesOptions<T>): UseResourcesReturn<T> {
  const [resources, setResources] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentNamespace, setCurrentNamespace] = useState("");
  const [namespaces, setNamespaces] = useState<string[]>([
    "default", "production", "staging"
  ]);

  const fetchResources = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listFn({
        namespace: currentNamespace || undefined,
      });
      setResources(response.items);
      setTotal(response.total);
      // Extract unique namespaces from resources
      const uniqueNamespaces = Array.from(
        new Set(response.items.map((r) => r.namespace))
      );
      if (uniqueNamespaces.length > 0) {
        setNamespaces((prev) =>
          Array.from(new Set([...prev, ...uniqueNamespaces]))
        );
      }
    } catch (error) {
      message.error("Failed to fetch resources");
    } finally {
      setLoading(false);
    }
  }, [listFn, currentNamespace]);

  // ... createResource, updateResource, deleteResource implementations
}
```

**Location:** `frontend/src/hooks/useResources.ts`

### 3. Resource Page Pattern

**Decision:** Each resource page follows a consistent pattern: map API responses to list items, define resource-specific columns, and wire up the reusable components.

**Rationale:**
- Each resource has different fields to display in the table
- Resource-specific columns provide meaningful context (e.g., "Tools" count for Skills, "Members" count for Teams)
- Form submission handles both create and edit modes uniformly

**Example Page Structure (Skills):**

```typescript
export default function SkillsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState<SkillResponse | null>(null);

  const {
    resources, loading, total, currentNamespace, namespaces,
    fetchResources, createResource, updateResource, deleteResource, setCurrentNamespace,
  } = useResources<SkillResponse>({
    listFn: skillApi.list,
    createFn: skillApi.create,
    updateFn: skillApi.update,
    deleteFn: skillApi.delete,
  });

  // Map API response to list items with resource-specific fields
  const skillListItems: SkillListItem[] = resources.map((skill) => ({
    id: skill.id,
    name: skill.metadata.name,
    namespace: skill.metadata.namespace,
    version: skill.spec.version || "-",
    author: skill.spec.author || "-",
    tools: skill.spec.tools?.length || 0,
    description: skill.spec.description || "-",
  }));

  // Resource-specific columns
  const columns: ColumnsType<SkillListItem> = [
    { title: "Name", dataIndex: "name", key: "name" },
    { title: "Namespace", dataIndex: "namespace", key: "namespace" },
    { title: "Version", dataIndex: "version", key: "version" },
    { title: "Author", dataIndex: "author", key: "author" },
    { title: "Tools", dataIndex: "tools", key: "tools" },
    { title: "Description", dataIndex: "description", key: "description" },
  ];

  // CRUD handlers
  const handleCreate = () => { /* ... */ };
  const handleEdit = (item: SkillListItem) => { /* ... */ };
  const handleDelete = async (item: SkillListItem) => { /* ... */ };
  const handleSubmit = async (values: ResourceFormData) => { /* ... */ };

  return (
    <div>
      <ResourceList<SkillListItem> /* props */ />
      <ResourceForm /* props */ />
    </div>
  );
}
```

**Location:**
- `frontend/src/app/(dashboard)/ghosts/page.tsx`
- `frontend/src/app/(dashboard)/models/page.tsx`
- `frontend/src/app/(dashboard)/shells/page.tsx`
- `frontend/src/app/(dashboard)/bots/page.tsx`
- `frontend/src/app/(dashboard)/teams/page.tsx`
- `frontend/src/app/(dashboard)/skills/page.tsx`

### 4. Namespace-Based Resource Isolation

**Decision:** Implement namespace filtering at the list level with a dropdown selector that filters resources and persists the selection during the session.

**Rationale:**
- Matches backend's namespace-scoped API design
- Enables multi-tenancy use cases (production vs staging isolation)
- Namespace list is dynamically populated from existing resources plus defaults

**Implementation:**

```typescript
// In ResourceList component
<Select
  placeholder="All Namespaces"
  value={currentNamespace || undefined}
  onChange={onNamespaceChange}
  allowClear
  style={{ width: 180 }}
>
  {namespaces.map((ns) => (
    <Option key={ns} value={ns}>{ns}</Option>
  ))}
</Select>
```

### 5. Form Design with Tabs

**Decision:** Use Ant Design Tabs to separate Basic Info (metadata) from Spec (YAML editor) in the resource form.

**Rationale:**
- Metadata fields (name, namespace, description) are common across all resources
- Spec is resource-specific YAML/JSON that benefits from a code editor
- Tabs prevent overwhelming users with too many fields at once
- Supports both create mode (empty form) and edit mode (pre-populated)

**Form Structure:**

```typescript
<Tabs activeKey={activeTab} onChange={setActiveTab}>
  <TabPane tab="Basic Info" key="basic">
    <Form.Item name={["metadata", "name"]} rules={[{ required: true }]}>
      <Input placeholder="Resource name" />
    </Form.Item>
    <Form.Item name={["metadata", "namespace"]}>
      <Select placeholder="Select namespace">
        {namespaces.map((ns) => <Option key={ns} value={ns}>{ns}</Option>)}
      </Select>
    </Form.Item>
    <Form.Item name={["metadata", "description"]}>
      <TextArea placeholder="Description" />
    </Form.Item>
  </TabPane>
  <TabPane tab="Spec" key="spec">
    <Form.Item name="spec">
      <TextArea rows={15} placeholder="Enter resource spec as YAML or JSON" />
    </Form.Item>
  </TabPane>
</Tabs>
```

## Consequences

### Positive

- **Code Reusability**: 6 resource pages share the same components, reducing maintenance burden
- **Consistent UX**: All resources have identical interaction patterns (search, filter, pagination, delete confirmation)
- **Type Safety**: TypeScript generics ensure type safety across different resource types
- **Rapid Development**: New resource types can be added with minimal boilerplate
- **Test Coverage**: 65 tests cover all resource management functionality with high confidence
- **Namespace Isolation**: Users can filter resources by namespace, supporting multi-tenant workflows

### Negative

- **Learning Curve**: Developers must understand the generic component pattern before modifying resource pages
- **Limited Customization**: Highly specialized resource UIs may require breaking out of the reusable component pattern
- **Bundle Size**: All resource pages import the same components, though this is mitigated by code splitting in Next.js

## Alternatives Considered

### Alternative 1: Individual Page Components

Create completely separate page components for each resource type without shared abstractions.

**Rejected:**
- Would result in significant code duplication (6 nearly identical list views)
- Maintenance burden: bug fixes would need to be applied to 6 files
- Inconsistent UX risk: each page might evolve different interaction patterns

### Alternative 2: Code Generation

Generate resource pages from a schema definition using a template system.

**Rejected:**
- Adds build-time complexity and tooling requirements
- Generated code is harder to customize for resource-specific needs
- Overkill for 6 resource types; better suited for 20+ resources

### Alternative 3: Dynamic Form Rendering

Use JSON Schema to dynamically render forms based on resource type definitions.

**Rejected:**
- Complex to implement with TypeScript type safety
- YAML spec editing is already flexible enough for resource-specific configuration
- Would require maintaining schema definitions alongside TypeScript types

## Implementation Notes

### Dependencies

No new dependencies required. Uses existing:
- `antd` for UI components (Table, Modal, Form, Tabs, Select, Input)
- `@ant-design/icons` for action icons
- React hooks (useState, useCallback, useEffect)

### Testing Strategy

```bash
# Run resource management tests
npm test -- tests/frontend/resources.test.ts

# All 65 tests passing:
# - ResourceList component: 8 tests
# - ResourceForm component: 7 tests
# - useResources hook: 5 tests
# - Resource pages: 18 tests
# - Resource API services: 24 tests
# - Resource components index: 3 tests
```

### Key Files

| File | Purpose |
|------|---------|
| `frontend/src/components/resources/ResourceList.tsx` | Reusable table with search, filter, pagination |
| `frontend/src/components/resources/ResourceForm.tsx` | Modal form with tabs for create/edit |
| `frontend/src/components/resources/index.ts` | Component exports |
| `frontend/src/hooks/useResources.ts` | CRUD operations hook |
| `frontend/src/services/resources.ts` | API service functions for all resources |
| `frontend/src/app/(dashboard)/*/page.tsx` | Resource-specific pages (6 files) |
| `tests/frontend/resources.test.ts` | 65 resource management tests |

## References

- [Ant Design Table Component](https://ant.design/components/table)
- [Ant Design Form Component](https://ant.design/components/form)
- [React Custom Hooks Pattern](https://react.dev/learn/reusing-logic-with-custom-hooks)
- Epic 21 in `doc/epic/frontend_mvp.md`
