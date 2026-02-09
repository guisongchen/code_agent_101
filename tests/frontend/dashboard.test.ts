/** Dashboard and Navigation Tests
 *
 * Tests for Epic 24: Dashboard and Navigation
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

  it("should have resource statistics cards", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("resourceCards");
    expect(content).toContain("Statistic");
  });

  it("should display all resource types", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Ghosts");
    expect(content).toContain("Models");
    expect(content).toContain("Shells");
    expect(content).toContain("Bots");
    expect(content).toContain("Teams");
    expect(content).toContain("Skills");
  });

  it("should have quick action buttons", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("quickActions");
    expect(content).toContain("Create Task");
    expect(content).toContain("Open Chat");
  });

  it("should have recent activity section", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Recent Tasks");
    expect(content).toContain("Activity Timeline");
  });

  it("should use useResources hook", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("useResources");
  });

  it("should use useTasks hook", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("useTasks");
  });
});

// =============================================================================
// Test Suite: Breadcrumb Navigation
// =============================================================================

describe("Breadcrumb Navigation", () => {
  it("should have BreadcrumbNav component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/layout/BreadcrumbNav.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export BreadcrumbNav component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/layout/BreadcrumbNav.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export function BreadcrumbNav");
  });

  it("should use usePathname hook", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/layout/BreadcrumbNav.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("usePathname");
  });

  it("should have route name mappings", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/layout/BreadcrumbNav.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("routeNames");
    expect(content).toContain("Dashboard");
    expect(content).toContain("Tasks");
  });

  it("should have home icon link", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/layout/BreadcrumbNav.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("HomeOutlined");
    expect(content).toContain('href="/"');
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

  it("should have header with user info", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("Header");
    expect(content).toContain("user?.username");
    expect(content).toContain("Avatar");
  });

  it("should have logout functionality", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("LogoutOutlined");
    expect(content).toContain("logout");
  });

  it("should use ProtectedRoute", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("ProtectedRoute");
  });

  it("should include BreadcrumbNav", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("BreadcrumbNav");
  });

  it("should have all navigation items", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("Dashboard");
    expect(content).toContain("Tasks");
    expect(content).toContain("Chat");
    expect(content).toContain("Ghosts");
    expect(content).toContain("Models");
    expect(content).toContain("Shells");
    expect(content).toContain("Bots");
    expect(content).toContain("Teams");
    expect(content).toContain("Skills");
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
// Test Suite: Layout Components Index
// =============================================================================

describe("Layout Components Index", () => {
  it("should have layout components index file", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/layout/index.ts"
    );
    expect(fileExists(indexPath)).toBe(true);
  });

  it("should export BreadcrumbNav", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/layout/index.ts"
    );
    const content = readFile(indexPath);
    expect(content).toContain('export * from "./BreadcrumbNav"');
  });
});
