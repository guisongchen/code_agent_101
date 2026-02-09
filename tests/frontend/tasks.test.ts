/** Task Management Tests
 *
 * Tests for Epic 22: Task Management Dashboard
 */

import { describe, it, expect } from "@jest/globals";
import fs from "fs";
import path from "path";

// =============================================================================
// Test Utilities
// =============================================================================

function fileExists(filePath: string): boolean {
  try {
    return fs.existsSync(filePath);
  } catch {
    return false;
  }
}

function readFile(filePath: string): string | null {
  try {
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return null;
  }
}

const frontendRoot = path.join(__dirname, "../../frontend");

// =============================================================================
// Test Suite: Task API Service
// =============================================================================

describe("Task API Service", () => {
  it("should have tasks service file", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    expect(fileExists(servicePath)).toBe(true);
  });

  it("should export taskApi", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export const taskApi");
  });

  it("should have list method", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("list:");
    expect(content).toContain("/tasks");
  });

  it("should have get method", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("get:");
    expect(content).toContain("/tasks/${taskId}");
  });

  it("should have create method", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("create:");
    expect(content).toContain('"/tasks"');
  });

  it("should have updateStatus method", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("updateStatus:");
    expect(content).toContain("/tasks/${taskId}/status");
  });

  it("should have cancel method", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("cancel:");
    expect(content).toContain('status: "cancelled"');
  });

  it("should have delete method", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("delete:");
  });

  it("should have execute method", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("execute:");
    expect(content).toContain("/tasks/${taskId}/execute");
  });

  it("should support namespace filter", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("namespace");
    expect(content).toContain('params.append("namespace"');
  });

  it("should support status filter", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("status");
    expect(content).toContain('params.append("status"');
  });
});

// =============================================================================
// Test Suite: useTasks Hook
// =============================================================================

describe("useTasks Hook", () => {
  it("should have useTasks hook file", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    expect(fileExists(hookPath)).toBe(true);
  });

  it("should export useTasks hook", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("export function useTasks");
  });

  it("should have tasks state", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("tasks");
    expect(content).toContain("setTasks");
  });

  it("should have loading state", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("loading");
    expect(content).toContain("setLoading");
  });

  it("should have fetchTasks function", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("fetchTasks");
  });

  it("should have createTask function", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("createTask");
  });

  it("should have cancelTask function", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("cancelTask");
  });

  it("should have deleteTask function", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("deleteTask");
  });

  it("should have executeTask function", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("executeTask");
  });

  it("should support namespace filtering", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("currentNamespace");
    expect(content).toContain("setCurrentNamespace");
  });

  it("should support status filtering", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("statusFilter");
    expect(content).toContain("setStatusFilter");
  });

  it("should have real-time updates support", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTasks.ts");
    const content = readFile(hookPath);
    expect(content).toContain("enableRealtime");
    expect(content).toContain("setInterval");
  });
});

// =============================================================================
// Test Suite: Tasks Page
// =============================================================================

describe("Tasks Page", () => {
  it("should have tasks page file", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    expect(fileExists(pagePath)).toBe(true);
  });

  it("should use useTasks hook", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("useTasks");
  });

  it("should have status filter dropdown", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("statusFilter");
    expect(content).toContain('placeholder="Filter by Status"');
  });

  it("should have search functionality", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("searchText");
    expect(content).toContain('placeholder="Search tasks..."');
  });

  it("should have create task button", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Create Task");
    expect(content).toContain("PlusOutlined");
  });

  it("should have execute action for pending tasks", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain('status === "pending"');
    expect(content).toContain("PlayCircleOutlined");
    expect(content).toContain("handleExecute");
  });

  it("should have cancel action for running tasks", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain('status === "running"');
    expect(content).toContain("StopOutlined");
    expect(content).toContain("handleCancel");
  });

  it("should have view detail action", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("EyeOutlined");
    expect(content).toContain("handleView");
  });

  it("should have delete action with confirmation", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("DeleteOutlined");
    expect(content).toContain("handleDelete");
    expect(content).toContain("Popconfirm");
  });

  it("should display status badges", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Badge");
    expect(content).toContain("statusColors");
    expect(content).toContain("statusLabels");
  });

  it("should use ResourceList component", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("ResourceList");
  });
});

// =============================================================================
// Test Suite: Task Detail Page
// =============================================================================

describe("Task Detail Page", () => {
  it("should have task detail page file", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    expect(fileExists(pagePath)).toBe(true);
  });

  it("should fetch task by ID", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("taskApi.get");
    expect(content).toContain("params.id");
  });

  it("should display task information", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Task Information");
    expect(content).toContain("Descriptions");
  });

  it("should have execution timeline", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Execution Timeline");
    expect(content).toContain("Timeline");
  });

  it("should display task input", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Task Input");
    expect(content).toContain("task.input");
  });

  it("should display task output", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Task Output");
    expect(content).toContain("task.output");
  });

  it("should display error output", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Error");
    expect(content).toContain("task.error");
    expect(content).toContain('type="error"');
  });

  it("should have execute button for pending tasks", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain('status === "pending"');
    expect(content).toContain("taskApi.execute");
  });

  it("should have cancel button for running tasks", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain('status === "running"');
    expect(content).toContain("taskApi.cancel");
  });

  it("should auto-refresh for running tasks", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/[id]/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain('status === "running"');
    expect(content).toContain("setInterval");
  });
});

// =============================================================================
// Test Suite: Task Create Modal
// =============================================================================

describe("Task Create Modal", () => {
  it("should have TaskCreateModal component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/tasks/TaskCreateModal.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export TaskCreateModal component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/tasks/TaskCreateModal.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export function TaskCreateModal");
  });

  it("should have name input field", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/tasks/TaskCreateModal.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain('name="name"');
    expect(content).toContain("Task Name");
  });

  it("should have namespace select", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/tasks/TaskCreateModal.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain('name="namespace"');
    expect(content).toContain("Namespace");
  });

  it("should have team selection", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/tasks/TaskCreateModal.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain('name="teamId"');
    expect(content).toContain("Team");
  });

  it("should have input textarea", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/tasks/TaskCreateModal.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain('name="input"');
    expect(content).toContain("Task Input");
  });

  it("should have submit and cancel buttons", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/tasks/TaskCreateModal.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("onSubmit");
    expect(content).toContain("onCancel");
    expect(content).toContain('type="primary"');
  });
});

// =============================================================================
// Test Suite: Navigation
// =============================================================================

describe("Tasks Navigation", () => {
  it("should have Tasks in navigation", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain('label: <Link href="/tasks">Tasks</Link>');
  });

  it("should have CheckSquareOutlined icon for Tasks", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("CheckSquareOutlined");
  });
});

// =============================================================================
// Test Suite: useTeams Hook
// =============================================================================

describe("useTeams Hook", () => {
  it("should have useTeams hook file", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTeams.ts");
    expect(fileExists(hookPath)).toBe(true);
  });

  it("should export useTeams hook", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTeams.ts");
    const content = readFile(hookPath);
    expect(content).toContain("export function useTeams");
  });

  it("should fetch teams from API", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useTeams.ts");
    const content = readFile(hookPath);
    expect(content).toContain("teamApi.list");
  });
});
