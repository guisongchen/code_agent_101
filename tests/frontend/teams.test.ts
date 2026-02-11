/** Teams Management Tests
 *
 * Tests for Simplified Frontend - Teams
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
// Test Suite: Teams Page
// =============================================================================

describe("Teams Page", () => {
  it("should have teams page file", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    expect(fileExists(pagePath)).toBe(true);
  });

  it("should export default component", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("export default function TeamsPage");
  });

  it("should have Table for displaying teams", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("<Table");
  });

  it("should have create button", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("New Team");
    expect(content).toContain("PlusOutlined");
  });

  it("should have edit action", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("handleEdit");
    expect(content).toContain("EditOutlined");
  });

  it("should have delete action with confirmation", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("handleDelete");
    expect(content).toContain("Popconfirm");
    expect(content).toContain("DeleteOutlined");
  });

  it("should have modal for create/edit", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("<Modal");
  });

  it("should have agent selection", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("agentIds");
    expect(content).toContain('mode="multiple"');
  });

  it("should use listTeams service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("listTeams");
  });

  it("should use createTeam service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("createTeam");
  });

  it("should use updateTeam service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("updateTeam");
  });

  it("should use deleteTeam service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/teams/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("deleteTeam");
  });
});

// =============================================================================
// Test Suite: Team API Service
// =============================================================================

describe("Team API Service", () => {
  it("should have teams service file", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    expect(fileExists(servicePath)).toBe(true);
  });

  it("should export listTeams function", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function listTeams");
  });

  it("should export getTeam function", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function getTeam");
  });

  it("should export createTeam function", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function createTeam");
  });

  it("should export updateTeam function", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function updateTeam");
  });

  it("should export deleteTeam function", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function deleteTeam");
  });

  it("should use /teams endpoint", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    const content = readFile(servicePath);
    expect(content).toContain('"/teams"');
  });

  it("should use simple api client", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    const content = readFile(servicePath);
    expect(content).toContain('@/lib/api');
  });
});

// =============================================================================
// Test Suite: Team Types
// =============================================================================

describe("Team Types", () => {
  it("should have Team interface in types", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface Team");
  });

  it("should have TeamCreateRequest interface", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface TeamCreateRequest");
  });

  it("should have agentIds array", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("agentIds: string[]");
  });
});

// =============================================================================
// Test Suite: Navigation
// =============================================================================

describe("Teams Navigation", () => {
  it("should have Teams in navigation", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain('label: <Link href="/teams">Teams</Link>');
  });

  it("should have TeamOutlined icon for Teams", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("TeamOutlined");
  });
});
