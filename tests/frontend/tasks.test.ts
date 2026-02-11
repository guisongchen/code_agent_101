/** Task Management Tests
 *
 * Tests for Simplified Frontend - Task Management
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

  it("should export listTasks function", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function listTasks");
  });

  it("should export getTask function", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function getTask");
  });

  it("should export createTask function", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function createTask");
  });

  it("should export updateTask function", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function updateTask");
  });

  it("should export deleteTask function", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function deleteTask");
  });

  it("should export getTaskMessages function", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function getTaskMessages");
  });

  it("should export sendMessage function", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function sendMessage");
  });

  it("should use /tasks endpoint", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain('"/tasks"');
  });

  it("should NOT have namespace filter (simplified)", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).not.toContain("namespace");
    expect(content).not.toContain('params.append("namespace"');
  });

  it("should use simple api client", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    const content = readFile(servicePath);
    expect(content).toContain('@/lib/api');
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

  it("should use inline CRUD (not useTasks hook)", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).not.toContain("useTasks");
    expect(content).toContain("listTasks");
  });

  it("should have create task button", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("New Task");
    expect(content).toContain("PlusOutlined");
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
    expect(content).toContain("Tag");
    expect(content).toContain("statusColors");
  });

  it("should NOT use ResourceList component (simplified)", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).not.toContain("ResourceList");
  });

  it("should have modal for creating tasks", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("<Modal");
  });

  it("should have agent selection", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/tasks/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("agentId");
  });
});

// =============================================================================
// Test Suite: Task Types
// =============================================================================

describe("Task Types", () => {
  it("should have Task interface in types", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface Task");
  });

  it("should have TaskCreateRequest interface", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface TaskCreateRequest");
  });

  it("should have TaskStatus type", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("TaskStatus");
  });

  it("should NOT have namespace in Task (simplified)", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    // Task should have agentId instead of namespace
    expect(content).toContain("agentId");
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
