/** Agents Management Tests
 *
 * Tests for Simplified Frontend - Agents (consolidated from Ghosts/Models/Shells/Bots)
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
// Test Suite: Agents Page
// =============================================================================

describe("Agents Page", () => {
  it("should have agents page file", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    expect(fileExists(pagePath)).toBe(true);
  });

  it("should export default component", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("export default function AgentsPage");
  });

  it("should have Table for displaying agents", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("<Table");
  });

  it("should have create button", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("New Agent");
    expect(content).toContain("PlusOutlined");
  });

  it("should have edit action", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("handleEdit");
    expect(content).toContain("EditOutlined");
  });

  it("should have delete action with confirmation", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("handleDelete");
    expect(content).toContain("Popconfirm");
    expect(content).toContain("DeleteOutlined");
  });

  it("should have modal for create/edit", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("<Modal");
  });

  it("should have form with agent fields", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("name");
    expect(content).toContain("modelProvider");
    expect(content).toContain("modelName");
    expect(content).toContain("systemPrompt");
  });

  it("should use listAgents service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("listAgents");
  });

  it("should use createAgent service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("createAgent");
  });

  it("should use updateAgent service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("updateAgent");
  });

  it("should use deleteAgent service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/agents/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("deleteAgent");
  });
});

// =============================================================================
// Test Suite: Agent API Service
// =============================================================================

describe("Agent API Service", () => {
  it("should have agents service file", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    expect(fileExists(servicePath)).toBe(true);
  });

  it("should export listAgents function", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function listAgents");
  });

  it("should export getAgent function", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function getAgent");
  });

  it("should export createAgent function", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function createAgent");
  });

  it("should export updateAgent function", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function updateAgent");
  });

  it("should export deleteAgent function", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    const content = readFile(servicePath);
    expect(content).toContain("export async function deleteAgent");
  });

  it("should use /agents endpoint", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    const content = readFile(servicePath);
    expect(content).toContain('"/agents"');
  });

  it("should use simple api client", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    const content = readFile(servicePath);
    expect(content).toContain('@/lib/api');
  });
});

// =============================================================================
// Test Suite: Agent Types
// =============================================================================

describe("Agent Types", () => {
  it("should have Agent interface in types", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface Agent");
  });

  it("should have AgentCreateRequest interface", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface AgentCreateRequest");
  });

  it("should have required agent fields", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("modelProvider");
    expect(content).toContain("modelName");
    expect(content).toContain("systemPrompt");
  });
});

// =============================================================================
// Test Suite: Navigation
// =============================================================================

describe("Agents Navigation", () => {
  it("should have Agents in navigation", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain('label: <Link href="/agents">Agents</Link>');
  });

  it("should have RobotOutlined icon for Agents", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("RobotOutlined");
  });
});
