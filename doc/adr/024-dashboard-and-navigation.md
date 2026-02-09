# ADR 024: Dashboard and Navigation

## Status

Accepted

## Context

Epic 24 required implementing a comprehensive dashboard and navigation system for the Wegent frontend. The application had grown to include multiple resource types (Ghosts, Models, Shells, Bots, Teams, Skills), Tasks, and Chat functionality. Users needed:

1. A central dashboard providing an overview of all resources
2. Quick access to common actions (create task, open chat, etc.)
3. Recent activity visibility
4. Clear navigation between different sections
5. Breadcrumb navigation for deep pages
6. Responsive layout for different screen sizes

The challenge was designing a dashboard that would scale with the application and provide meaningful insights without overwhelming users with information.

## Decision

### 1. Resource Statistics Cards

**Decision:** Display resource counts as clickable cards on the dashboard, showing totals for each resource type.

**Rationale:**
- Provides immediate visibility into system state
- Cards are scannable and visually distinct
- Click-through navigation to resource management pages
- Color coding helps distinguish resource types

**Implementation:**

```typescript
const resourceCards = [
  {
    key: "ghosts",
    title: "Ghosts",
    icon: <FileTextOutlined style={{ fontSize: 24, color: "#1890ff" }} />,
    color: "#1890ff",
    link: "/ghosts",
  },
  // ... similar for models, shells, bots, teams, skills
];

// Usage with recharts for visual appeal
<Row gutter={[16, 16]}>
  {resourceCards.map((card) => (
    <Col xs={24} sm={12} lg={8} xl={4} key={card.key}>
      <Link href={card.link}>
        <Card hoverable style={{ borderTop: `3px solid ${card.color}` }}>
          <Statistic
            value={resourceCounts[card.key]}
            valueStyle={{ fontSize: 32, fontWeight: "bold", color: card.color }}
          />
        </Card>
      </Link>
    </Col>
  ))}
</Row>
```

**Location:** `frontend/src/app/(dashboard)/page.tsx`

### 2. Quick Action Buttons

**Decision:** Provide prominent quick action buttons for the most common user tasks.

**Rationale:**
- Reduces time to complete common actions
- Discoverability for new users
- Provides clear entry points to key workflows

**Implementation:**

```typescript
const quickActions = [
  { label: "Create Task", icon: <CheckSquareOutlined />, link: "/tasks" },
  { label: "Open Chat", icon: <MessageOutlined />, link: "/chat" },
  { label: "New Bot", icon: <RobotOutlined />, link: "/bots" },
  { label: "New Team", icon: <TeamOutlined />, link: "/teams" },
];

<Row gutter={[16, 16]}>
  {quickActions.map((action) => (
    <Col xs={12} sm={6} key={action.label}>
      <Link href={action.link}>
        <Button type="dashed" icon={action.icon} size="large" block>
          {action.label}
        </Button>
      </Link>
    </Col>
  ))}
</Row>
```

### 3. Recent Activity Sections

**Decision:** Display recent tasks and activity timeline on the dashboard.

**Rationale:**
- Users can quickly see what's happening in the system
- Provides context without navigating to other pages
- Timeline view shows chronological activity flow

**Implementation:**

```typescript
// Recent Tasks List
<Card title="Recent Tasks">
  <List
    dataSource={recentTasks.slice(0, 5)}
    renderItem={(task) => (
      <List.Item>
        <List.Item.Meta
          title={<Link href={`/tasks/${task.id}`}>{task.name}</Link>}
          description={<Tag color={statusColors[task.status]}>{task.status}</Tag>}
        />
      </List.Item>
    )}
  />
</Card>

// Activity Timeline
<Card title="Activity Timeline">
  <Timeline
    items={recentTasks.slice(0, 5).map((task) => ({
      dot: <ClockCircleOutlined style={{ color: "#1890ff" }} />,
      children: (
        <div>
          <Text strong>{task.name}</Text>
          <Tag color={statusColors[task.status]}>{task.status}</Tag>
        </div>
      ),
    }))}
  />
</Card>
```

### 4. Sidebar Navigation

**Decision:** Use Ant Design's Layout.Sider with Menu for primary navigation.

**Rationale:**
- Collapsible sidebar saves screen space
- Icons + text labels provide clear navigation
- Selected state shows current location
- Responsive breakpoint handling for mobile

**Implementation:**

```typescript
const navigationItems = [
  { key: "/", icon: <DashboardOutlined />, label: <Link href="/">Dashboard</Link> },
  { key: "/tasks", icon: <CheckSquareOutlined />, label: <Link href="/tasks">Tasks</Link> },
  { key: "/chat", icon: <MessageOutlined />, label: <Link href="/chat">Chat</Link> },
  // ... resource links
];

<Sider theme="light" breakpoint="lg" collapsedWidth="80">
  <Menu mode="inline" selectedKeys={[pathname]} items={navigationItems} />
</Sider>
```

**Location:** `frontend/src/app/(dashboard)/layout.tsx`

### 5. Breadcrumb Navigation

**Decision:** Implement dynamic breadcrumb navigation based on current route.

**Rationale:**
- Shows users their current location in the app hierarchy
- Provides easy navigation back to parent pages
- Handles dynamic segments (task IDs, etc.)

**Implementation:**

```typescript
const routeNames: Record<string, string> = {
  "/": "Dashboard",
  "/tasks": "Tasks",
  "/chat": "Chat",
  // ...
};

export function BreadcrumbNav() {
  const pathname = usePathname();
  const pathSegments = pathname.split("/").filter(Boolean);

  const items = [
    { title: <Link href="/"><HomeOutlined /></Link> },
    ...pathSegments.map((segment, index) => {
      const isLast = index === pathSegments.length - 1;
      const title = routeNames[currentPath] || segment;
      return { title: isLast ? title : <Link href={currentPath}>{title}</Link> };
    }),
  ];

  return <Breadcrumb items={items} />;
}
```

**Location:** `frontend/src/components/layout/BreadcrumbNav.tsx`

### 6. Responsive Layout

**Decision:** Use Ant Design's responsive Grid system with breakpoint-specific column widths.

**Rationale:**
- Mobile-first approach
- Cards reflow appropriately on smaller screens
- Sidebar collapses on mobile devices

**Implementation:**

```typescript
// Resource cards - 6 columns on extra large, 3 on large, 2 on small, 1 on mobile
<Col xs={24} sm={12} lg={8} xl={4} key={card.key}>
  <Card>...</Card>
</Col>

// Sidebar with responsive breakpoint
<Sider breakpoint="lg" collapsedWidth="80">
```

### 7. Deferred: Dark/Light Theme Toggle

**Decision:** Defer implementation of dark/light theme toggle to post-MVP.

**Rationale:**
- Not critical for core functionality
- Ant Design's theming requires significant configuration
- Can be added later without breaking changes

## Consequences

### Positive

- **Overview at a Glance**: Users can see system state immediately upon login
- **Quick Navigation**: Common actions are one click away
- **Context Preservation**: Breadcrumbs prevent users from getting lost
- **Mobile Friendly**: Responsive design works on various screen sizes
- **Consistent UX**: Ant Design components provide familiar interaction patterns

### Negative

- **Limited Customization**: No user preferences for dashboard layout (yet)
- **No Real-time Updates**: Dashboard stats don't auto-refresh
- **Static Quick Actions**: Hardcoded actions may not suit all user workflows

## Alternatives Considered

### Alternative 1: Customizable Dashboard Widgets

Allow users to add, remove, and rearrange dashboard widgets.

**Rejected:**
- Adds significant complexity
- Requires widget persistence (database or localStorage)
- Overkill for MVP requirements

### Alternative 2: Top Navigation Bar

Use horizontal top navigation instead of sidebar.

**Rejected:**
- Doesn't scale well with many navigation items
- Sidebar provides better visual hierarchy
- Top nav takes valuable vertical space

### Alternative 3: Full-Screen Dashboard

Dashboard takes full screen without sidebar.

**Rejected:**
- Inconsistent with other pages
- Loses quick navigation context
- Sidebar provides important navigation anchor

## Implementation Notes

### Dependencies

No new dependencies required. Uses existing:
- `antd` for Layout, Menu, Card, Statistic, Timeline, Breadcrumb
- `@ant-design/icons` for navigation icons
- Next.js Link for client-side navigation

### Testing Strategy

```bash
# Run dashboard tests
cd frontend && npm test -- ../tests/frontend/dashboard.test.ts

# All 23 tests passing:
# - Dashboard page: 8 tests
# - Breadcrumb navigation: 5 tests
# - Dashboard layout: 8 tests
# - Layout components index: 2 tests
```

### Key Files

| File | Purpose |
|------|---------|
| `frontend/src/app/(dashboard)/page.tsx` | Dashboard home page |
| `frontend/src/app/(dashboard)/layout.tsx` | Dashboard layout with sidebar |
| `frontend/src/components/layout/BreadcrumbNav.tsx` | Breadcrumb navigation |
| `frontend/src/components/layout/index.ts` | Layout component exports |
| `tests/frontend/dashboard.test.ts` | 23 dashboard tests |

## References

- Ant Design Layout: https://ant.design/components/layout
- Ant Design Grid: https://ant.design/components/grid
- Next.js Routing: https://nextjs.org/docs/routing/introduction
