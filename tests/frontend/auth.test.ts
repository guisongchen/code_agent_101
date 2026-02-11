/** Authentication Tests
 *
 * Tests for Simplified Frontend - Authentication Removed
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
// Test Suite: Authentication Removed
// =============================================================================

describe("Authentication Removed (Simplified)", () => {
  it("should NOT have login page", () => {
    const loginPagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    expect(fileExists(loginPagePath)).toBe(false);
  });

  it("should NOT have register page", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    expect(fileExists(registerPagePath)).toBe(false);
  });

  it("should NOT have auth context", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    expect(fileExists(authContextPath)).toBe(false);
  });

  it("should NOT have auth service", () => {
    const authServicePath = path.join(frontendRoot, "src/services/auth.ts");
    expect(fileExists(authServicePath)).toBe(false);
  });

  it("should NOT have auth types", () => {
    const authTypesPath = path.join(frontendRoot, "src/types/auth.ts");
    expect(fileExists(authTypesPath)).toBe(false);
  });

  it("should NOT have context directory", () => {
    const contextDir = path.join(frontendRoot, "src/context");
    expect(fileExists(contextDir)).toBe(false);
  });
});

// =============================================================================
// Test Suite: Dashboard Direct Access
// =============================================================================

describe("Dashboard Direct Access (No Auth)", () => {
  it("should NOT have separate root page (dashboard serves root directly)", () => {
    // The dashboard at (dashboard)/page.tsx serves the root path directly
    // No redirect needed since route groups don't affect URL structure
    const pagePath = path.join(frontendRoot, "src/app/page.tsx");
    expect(fileExists(pagePath)).toBe(false);
  });

  it("should NOT have ProtectedRoute in layout", () => {
    const layoutPath = path.join(frontendRoot, "src/app/(dashboard)/layout.tsx");
    const content = readFile(layoutPath);
    expect(content).not.toContain("ProtectedRoute");
  });

  it("should NOT have useAuth in layout", () => {
    const layoutPath = path.join(frontendRoot, "src/app/(dashboard)/layout.tsx");
    const content = readFile(layoutPath);
    expect(content).not.toContain("useAuth");
  });

  it("should NOT have logout functionality", () => {
    const layoutPath = path.join(frontendRoot, "src/app/(dashboard)/layout.tsx");
    const content = readFile(layoutPath);
    expect(content).not.toContain("logout");
    expect(content).not.toContain("LogoutOutlined");
  });
});
