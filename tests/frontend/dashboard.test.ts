/** Dashboard and Navigation Tests
 *
 * Tests for Simplified Frontend - Dashboard and Navigation
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
// Test Suite: Dashboard Page
// =============================================================================

describe("Dashboard Page", () => {
  it("should have dashboard page file", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    expect(fileExists(pagePath)).toBe(true);
  });

  it("should export DashboardPage component", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("export default function DashboardPage");
  });

  it("should have agent statistics card", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Agents");
    expect(content).toContain("RobotOutlined");
  });

  it("should have task statistics card", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Tasks");
    expect(content).toContain("CheckSquareOutlined");
  });

  it("should have quick action buttons", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("New Agent");
    expect(content).toContain("New Task");
    expect(content).toContain("Open Chat");
  });

  it("should have recent tasks section", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Recent Tasks");
  });

  it("should use listAgents service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("listAgents");
  });

  it("should use listTasks service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("listTasks");
  });
});

// =============================================================================
// Test Suite: Dashboard Layout
// =============================================================================

describe("Dashboard Layout", () => {
  it("should have dashboard layout file", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    expect(fileExists(layoutPath)).toBe(true);
  });

  it("should have sidebar navigation", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("Sider");
    expect(content).toContain("Menu");
  });

  it("should NOT have authentication (simplified)", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).not.toContain("useAuth");
    expect(content).not.toContain("ProtectedRoute");
    expect(content).not.toContain("logout");
  });

  it("should have simplified navigation items", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("Dashboard");
    expect(content).toContain("Agents");
    expect(content).toContain("Tasks");
    expect(content).toContain("Chat");
    expect(content).toContain("Teams");
    // Old complex resources removed
    expect(content).not.toContain("Ghosts");
    expect(content).not.toContain("Models");
    expect(content).not.toContain("Shells");
    expect(content).not.toContain("Bots");
    expect(content).not.toContain("Skills");
  });

  it("should show Personal Mode indicator", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("Personal Mode");
  });

  it("should be responsive", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("breakpoint");
    expect(content).toContain("collapsedWidth");
  });
});

// =============================================================================
// Test Suite: Root Layout (No Auth)
// =============================================================================

describe("Root Layout", () => {
  it("should have root layout file", () => {
    const layoutPath = path.join(frontendRoot, "src/app/layout.tsx");
    expect(fileExists(layoutPath)).toBe(true);
  });

  it("should NOT have AuthProvider (simplified)", () => {
    const layoutPath = path.join(frontendRoot, "src/app/layout.tsx");
    const content = readFile(layoutPath);
    expect(content).not.toContain("AuthProvider");
    expect(content).not.toContain("auth-context");
  });

  it("should have Ant Design ConfigProvider", () => {
    const layoutPath = path.join(frontendRoot, "src/app/layout.tsx");
    const content = readFile(layoutPath);
    expect(content).toContain("ConfigProvider");
  });
});
