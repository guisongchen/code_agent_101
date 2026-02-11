/** Project Setup Tests
 *
 * Tests for Simplified Frontend - Project Structure
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
// Test Suite: Project Structure
// =============================================================================

describe("Simplified Project Structure", () => {
  it("should have package.json", () => {
    const packagePath = path.join(frontendRoot, "package.json");
    expect(fileExists(packagePath)).toBe(true);
  });

  it("should have next.config.ts with static export", () => {
    const configPath = path.join(frontendRoot, "next.config.ts");
    expect(fileExists(configPath)).toBe(true);
    const content = readFile(configPath);
    expect(content).toContain("output: 'export'");
    expect(content).toContain("distDir: 'dist'");
  });

  it("should have tsconfig.json", () => {
    const configPath = path.join(frontendRoot, "tsconfig.json");
    expect(fileExists(configPath)).toBe(true);
  });

  it("should have src directory", () => {
    const srcPath = path.join(frontendRoot, "src");
    expect(fileExists(srcPath)).toBe(true);
  });

  it("should have app directory", () => {
    const appPath = path.join(frontendRoot, "src/app");
    expect(fileExists(appPath)).toBe(true);
  });

  it("should have lib directory", () => {
    const libPath = path.join(frontendRoot, "src/lib");
    expect(fileExists(libPath)).toBe(true);
  });

  it("should have services directory", () => {
    const servicesPath = path.join(frontendRoot, "src/services");
    expect(fileExists(servicesPath)).toBe(true);
  });

  it("should have types directory", () => {
    const typesPath = path.join(frontendRoot, "src/types");
    expect(fileExists(typesPath)).toBe(true);
  });
});

// =============================================================================
// Test Suite: Removed Directories
// =============================================================================

describe("Removed Directories (Simplified)", () => {
  it("should NOT have context directory", () => {
    const dirPath = path.join(frontendRoot, "src/context");
    expect(fileExists(dirPath)).toBe(false);
  });

  it("should NOT have hooks directory (or it should be empty)", () => {
    const dirPath = path.join(frontendRoot, "src/hooks");
    // Directory might exist but should be empty or contain no hooks
    if (fileExists(dirPath)) {
      const files = fs.readdirSync(dirPath);
      const tsFiles = files.filter(f => f.endsWith('.ts'));
      expect(tsFiles.length).toBe(0);
    }
  });

  it("should NOT have utils directory", () => {
    const dirPath = path.join(frontendRoot, "src/utils");
    expect(fileExists(dirPath)).toBe(false);
  });

  it("should NOT have components/resources directory", () => {
    const dirPath = path.join(frontendRoot, "src/components/resources");
    expect(fileExists(dirPath)).toBe(false);
  });

  it("should NOT have components/chat directory", () => {
    const dirPath = path.join(frontendRoot, "src/components/chat");
    expect(fileExists(dirPath)).toBe(false);
  });

  it("should NOT have components/error directory", () => {
    const dirPath = path.join(frontendRoot, "src/components/error");
    expect(fileExists(dirPath)).toBe(false);
  });

  it("should NOT have components/layout directory", () => {
    const dirPath = path.join(frontendRoot, "src/components/layout");
    expect(fileExists(dirPath)).toBe(false);
  });

  it("should NOT have components/ui directory", () => {
    const dirPath = path.join(frontendRoot, "src/components/ui");
    expect(fileExists(dirPath)).toBe(false);
  });

  it("should NOT have components/tasks directory", () => {
    const dirPath = path.join(frontendRoot, "src/components/tasks");
    expect(fileExists(dirPath)).toBe(false);
  });
});

// =============================================================================
// Test Suite: Removed Pages
// =============================================================================

describe("Removed Pages (Simplified)", () => {
  it("should NOT have login page", () => {
    const pagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have register page", () => {
    const pagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have ghosts page", () => {
    const pagePath = path.join(frontendRoot, "src/app/(dashboard)/ghosts/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have models page", () => {
    const pagePath = path.join(frontendRoot, "src/app/(dashboard)/models/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have shells page", () => {
    const pagePath = path.join(frontendRoot, "src/app/(dashboard)/shells/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have bots page", () => {
    const pagePath = path.join(frontendRoot, "src/app/(dashboard)/bots/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have skills page", () => {
    const pagePath = path.join(frontendRoot, "src/app/(dashboard)/skills/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have task detail page", () => {
    const pagePath = path.join(frontendRoot, "src/app/(dashboard)/tasks/[id]/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });
});

// =============================================================================
// Test Suite: Simplified Types
// =============================================================================

describe("Simplified Types", () => {
  it("should have consolidated types in index.ts", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    expect(fileExists(typesPath)).toBe(true);
  });

  it("should NOT have separate auth types file", () => {
    const typesPath = path.join(frontendRoot, "src/types/auth.ts");
    expect(fileExists(typesPath)).toBe(false);
  });

  it("should NOT have separate resources types file", () => {
    const typesPath = path.join(frontendRoot, "src/types/resources.ts");
    expect(fileExists(typesPath)).toBe(false);
  });

  it("should NOT have separate task types file", () => {
    const typesPath = path.join(frontendRoot, "src/types/task.ts");
    expect(fileExists(typesPath)).toBe(false);
  });

  it("should NOT have separate message types file", () => {
    const typesPath = path.join(frontendRoot, "src/types/message.ts");
    expect(fileExists(typesPath)).toBe(false);
  });

  it("should NOT have separate chat types file", () => {
    const typesPath = path.join(frontendRoot, "src/types/chat.ts");
    expect(fileExists(typesPath)).toBe(false);
  });

  it("should NOT have separate session types file", () => {
    const typesPath = path.join(frontendRoot, "src/types/session.ts");
    expect(fileExists(typesPath)).toBe(false);
  });

  it("should have Agent type", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface Agent");
  });

  it("should have Team type", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface Team");
  });

  it("should have Task type", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).toContain("interface Task");
  });

  it("should NOT have namespace in types", () => {
    const typesPath = path.join(frontendRoot, "src/types/index.ts");
    const content = readFile(typesPath);
    expect(content).not.toContain("namespace:");
  });
});

// =============================================================================
// Test Suite: Simplified Services
// =============================================================================

describe("Simplified Services", () => {
  it("should have agents service", () => {
    const servicePath = path.join(frontendRoot, "src/services/agents.ts");
    expect(fileExists(servicePath)).toBe(true);
  });

  it("should have teams service", () => {
    const servicePath = path.join(frontendRoot, "src/services/teams.ts");
    expect(fileExists(servicePath)).toBe(true);
  });

  it("should have tasks service", () => {
    const servicePath = path.join(frontendRoot, "src/services/tasks.ts");
    expect(fileExists(servicePath)).toBe(true);
  });

  it("should NOT have auth service", () => {
    const servicePath = path.join(frontendRoot, "src/services/auth.ts");
    expect(fileExists(servicePath)).toBe(false);
  });

  it("should NOT have resources service", () => {
    const servicePath = path.join(frontendRoot, "src/services/resources.ts");
    expect(fileExists(servicePath)).toBe(false);
  });

  it("should NOT have services index file", () => {
    const servicePath = path.join(frontendRoot, "src/services/index.ts");
    expect(fileExists(servicePath)).toBe(false);
  });

  it("should NOT have complex axios-based api service", () => {
    const servicePath = path.join(frontendRoot, "src/services/api.ts");
    expect(fileExists(servicePath)).toBe(false);
  });
});
