/** Build Verification Tests
 *
 * Tests that verify the frontend compiles and builds successfully
 */

import { describe, it, expect } from "@jest/globals";
import { execSync } from "child_process";
import path from "path";

const frontendRoot = path.join(__dirname, "../../frontend");

// =============================================================================
// Test Suite: TypeScript Compilation
// =============================================================================

describe("TypeScript Compilation", () => {
  it("should compile TypeScript without errors", () => {
    try {
      execSync("npx tsc --noEmit", {
        cwd: frontendRoot,
        encoding: "utf-8",
        timeout: 120000,
      });
      expect(true).toBe(true);
    } catch (error: any) {
      const stdout = error.stdout || "";
      const stderr = error.stderr || "";
      const message = error.message || "";
      console.error("TypeScript compilation errors:", stdout + stderr + message);
      throw new Error(`TypeScript compilation failed:\n${stdout}${stderr}`);
    }
  });
});

// =============================================================================
// Test Suite: Next.js Build
// =============================================================================

describe("Next.js Build", () => {
  it("should build successfully", () => {
    try {
      // Clean previous build first
      execSync("rm -rf .next dist", {
        cwd: frontendRoot,
        encoding: "utf-8",
        timeout: 30000,
      });

      // Run build
      execSync("npm run build", {
        cwd: frontendRoot,
        encoding: "utf-8",
        timeout: 300000, // 5 minutes
        stdio: "pipe",
      });

      expect(true).toBe(true);
    } catch (error: any) {
      const stdout = error.stdout || "";
      const stderr = error.stderr || "";
      console.error("Build errors:", stdout + stderr);
      throw new Error(`Next.js build failed:\n${stdout}${stderr}`);
    }
  });

  it("should generate .next output directory", () => {
    const fs = require("fs");
    const nextDir = path.join(frontendRoot, ".next");
    expect(fs.existsSync(nextDir)).toBe(true);
  });
});

// =============================================================================
// Test Suite: Lint Check
// =============================================================================

describe("ESLint Check", () => {
  it("should have eslint configured", () => {
    const eslintConfig = path.join(frontendRoot, "eslint.config.mjs");
    const eslintConfigJs = path.join(frontendRoot, "eslint.config.js");
    const eslintConfigTs = path.join(frontendRoot, "eslint.config.ts");
    const eslintrc = path.join(frontendRoot, ".eslintrc.json");

    const fs = require("fs");
    const hasConfig =
      fs.existsSync(eslintConfig) ||
      fs.existsSync(eslintConfigJs) ||
      fs.existsSync(eslintConfigTs) ||
      fs.existsSync(eslintrc);

    expect(hasConfig).toBe(true);
  });
});
