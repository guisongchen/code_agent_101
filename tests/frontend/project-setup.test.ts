/** Project Setup Tests
 *
 * Tests for Epic 19: Project Setup and Core Infrastructure
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

const projectRoot = path.join(__dirname, "../../frontend");

// =============================================================================
// Test Suite: Project Setup Verification
// =============================================================================

describe("Project Setup Verification", () => {
  describe("Configuration Files", () => {
    it("should have package.json", () => {
      const filePath = path.join(projectRoot, "package.json");
      expect(fileExists(filePath)).toBe(true);
    });

    it("should have tsconfig.json", () => {
      const filePath = path.join(projectRoot, "tsconfig.json");
      expect(fileExists(filePath)).toBe(true);
    });

    it("should have tailwind.config.ts", () => {
      const filePath = path.join(projectRoot, "tailwind.config.ts");
      expect(fileExists(filePath)).toBe(true);
    });

    it("should have postcss.config.mjs", () => {
      const filePath = path.join(projectRoot, "postcss.config.mjs");
      expect(fileExists(filePath)).toBe(true);
    });

    it("should have next.config.ts", () => {
      const filePath = path.join(projectRoot, "next.config.ts");
      expect(fileExists(filePath)).toBe(true);
    });

    it("should have eslint.config.mjs", () => {
      const filePath = path.join(projectRoot, "eslint.config.mjs");
      expect(fileExists(filePath)).toBe(true);
    });

    it("should have .env.local", () => {
      const filePath = path.join(projectRoot, ".env.local");
      expect(fileExists(filePath)).toBe(true);
    });

    it("should have .env.example", () => {
      const filePath = path.join(projectRoot, ".env.example");
      expect(fileExists(filePath)).toBe(true);
    });
  });

  describe("Project Structure", () => {
    const requiredDirs = [
      "src/app",
      "src/components",
      "src/hooks",
      "src/services",
      "src/types",
      "src/context",
      "src/lib",
      "src/styles",
      "public",
    ];

    it.each(requiredDirs)("should have %s directory", (dir) => {
      const dirPath = path.join(projectRoot, dir);
      expect(fileExists(dirPath)).toBe(true);
    });
  });
});

// =============================================================================
// Test Suite: TypeScript Configuration
// =============================================================================

describe("TypeScript Configuration", () => {
  it("should have valid tsconfig.json with strict mode", () => {
    const tsConfigPath = path.join(projectRoot, "tsconfig.json");
    const content = readFile(tsConfigPath);
    expect(content).not.toBeNull();

    const config = JSON.parse(content!);
    expect(config.compilerOptions.strict).toBe(true);
    expect(["preserve", "react-jsx"]).toContain(config.compilerOptions.jsx);
    expect(config.compilerOptions.esModuleInterop).toBe(true);
  });

  it("should have path aliases configured", () => {
    const tsConfigPath = path.join(projectRoot, "tsconfig.json");
    const content = readFile(tsConfigPath);
    expect(content).not.toBeNull();

    const config = JSON.parse(content!);
    expect(config.compilerOptions.paths["@/*"]).toBeDefined();
    expect(config.compilerOptions.paths["@/*"][0]).toBe("./src/*");
  });
});

// =============================================================================
// Test Suite: Tailwind Configuration
// =============================================================================

describe("Tailwind Configuration", () => {
  it("should have custom theme colors matching design system", () => {
    const tailwindPath = path.join(projectRoot, "tailwind.config.ts");
    const content = readFile(tailwindPath);
    expect(content).not.toBeNull();

    // Check for Ant Design colors
    expect(content).toContain("#1890ff"); // Primary
    expect(content).toContain("#52c41a"); // Success
    expect(content).toContain("#faad14"); // Warning
    expect(content).toContain("#f5222d"); // Error
  });

  it("should have content paths configured", () => {
    const tailwindPath = path.join(projectRoot, "tailwind.config.ts");
    const content = readFile(tailwindPath);
    expect(content).not.toBeNull();

    expect(content).toContain("./src/app/**/*");
    expect(content).toContain("./src/components/**/*");
  });
});

// =============================================================================
// Test Suite: Axios Setup
// =============================================================================

describe("Axios Setup", () => {
  it("should have api.ts with interceptors", () => {
    const apiPath = path.join(projectRoot, "src/services/api.ts");
    expect(fileExists(apiPath)).toBe(true);

    const content = readFile(apiPath);
    expect(content).not.toBeNull();
    expect(content).toContain("axios.create");
    expect(content).toContain("interceptors.request");
    expect(content).toContain("interceptors.response");
  });

  it("should have auth token handling in request interceptor", () => {
    const apiPath = path.join(projectRoot, "src/services/api.ts");
    const content = readFile(apiPath);
    expect(content).not.toBeNull();

    expect(content).toContain("Authorization");
    expect(content).toContain("Bearer");
    expect(content).toContain("localStorage");
  });

  it("should have error handling in response interceptor", () => {
    const apiPath = path.join(projectRoot, "src/services/api.ts");
    const content = readFile(apiPath);
    expect(content).not.toBeNull();

    expect(content).toContain("401");
    expect(content).toContain("403");
  });
});

// =============================================================================
// Test Suite: Environment Variables
// =============================================================================

describe("Environment Variables", () => {
  it("should have API URL configured in .env.local", () => {
    const envPath = path.join(projectRoot, ".env.local");
    const content = readFile(envPath);
    expect(content).not.toBeNull();

    expect(content).toContain("NEXT_PUBLIC_API_URL");
    expect(content).toContain("localhost:8000");
  });

  it("should have WebSocket URL configured in .env.local", () => {
    const envPath = path.join(projectRoot, ".env.local");
    const content = readFile(envPath);
    expect(content).not.toBeNull();

    expect(content).toContain("NEXT_PUBLIC_WS_URL");
    expect(content).toContain("ws://localhost:8000");
  });

  it("should have example environment file", () => {
    const envExamplePath = path.join(projectRoot, ".env.example");
    const content = readFile(envExamplePath);
    expect(content).not.toBeNull();

    expect(content).toContain("NEXT_PUBLIC_API_URL");
    expect(content).toContain("NEXT_PUBLIC_WS_URL");
  });
});

// =============================================================================
// Test Suite: Dependencies
// =============================================================================

describe("Dependencies", () => {
  it("should have required dependencies in package.json", () => {
    const packagePath = path.join(projectRoot, "package.json");
    const content = readFile(packagePath);
    expect(content).not.toBeNull();

    const pkg = JSON.parse(content!);

    // Core dependencies
    expect(pkg.dependencies.next).toBeDefined();
    expect(pkg.dependencies.react).toBeDefined();
    expect(pkg.dependencies["react-dom"]).toBeDefined();

    // UI dependencies
    expect(pkg.dependencies.antd).toBeDefined();

    // HTTP client
    expect(pkg.dependencies.axios).toBeDefined();

    // WebSocket
    expect(pkg.dependencies["socket.io-client"]).toBeDefined();
  });

  it("should have required dev dependencies", () => {
    const packagePath = path.join(projectRoot, "package.json");
    const content = readFile(packagePath);
    expect(content).not.toBeNull();

    const pkg = JSON.parse(content!);

    // TypeScript
    expect(pkg.devDependencies.typescript).toBeDefined();
    expect(pkg.devDependencies["@types/node"]).toBeDefined();
    expect(pkg.devDependencies["@types/react"]).toBeDefined();

    // Tailwind (postcss and autoprefixer are in dependencies, not devDependencies)
    expect(pkg.devDependencies.tailwindcss).toBeDefined();
    expect(pkg.dependencies.postcss).toBeDefined();
    expect(pkg.dependencies.autoprefixer).toBeDefined();

    // Linting
    expect(pkg.devDependencies.eslint).toBeDefined();
  });
});

// =============================================================================
// Test Suite: TypeScript Types
// =============================================================================

describe("TypeScript Types", () => {
  it("should have auth types defined", () => {
    const authTypesPath = path.join(projectRoot, "src/types/auth.ts");
    expect(fileExists(authTypesPath)).toBe(true);

    const content = readFile(authTypesPath);
    expect(content).toContain("interface Token");
    expect(content).toContain("interface UserResponse");
    expect(content).toContain("interface LoginRequest");
  });

  it("should have resource types defined", () => {
    const resourceTypesPath = path.join(projectRoot, "src/types/resources.ts");
    expect(fileExists(resourceTypesPath)).toBe(true);

    const content = readFile(resourceTypesPath);
    expect(content).toContain("GhostSpec");
    expect(content).toContain("ModelSpec");
    expect(content).toContain("BotSpec");
  });

  it("should have type exports in index.ts", () => {
    const typesIndexPath = path.join(projectRoot, "src/types/index.ts");
    expect(fileExists(typesIndexPath)).toBe(true);

    const content = readFile(typesIndexPath);
    expect(content).toContain('export * from "./auth"');
    expect(content).toContain('export * from "./resources"');
  });
});

// =============================================================================
// Test Suite: Auth Context
// =============================================================================

describe("Auth Context", () => {
  it("should have auth context with provider", () => {
    const authContextPath = path.join(projectRoot, "src/context/auth-context.tsx");
    expect(fileExists(authContextPath)).toBe(true);

    const content = readFile(authContextPath);
    expect(content).toContain("AuthProvider");
    expect(content).toContain("useAuth");
  });

  it("should have protected route wrapper", () => {
    const authContextPath = path.join(projectRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("ProtectedRoute");
  });
});

// =============================================================================
// Test Suite: Build Verification
// =============================================================================

describe("Build Verification", () => {
  it("should have a build script", () => {
    const packagePath = path.join(projectRoot, "package.json");
    const content = readFile(packagePath);
    expect(content).not.toBeNull();

    const pkg = JSON.parse(content!);
    expect(pkg.scripts.build).toBeDefined();
  });

  it("should have next.config.ts or next.config.js", () => {
    const tsConfig = path.join(projectRoot, "next.config.ts");
    const jsConfig = path.join(projectRoot, "next.config.js");
    const mjsConfig = path.join(projectRoot, "next.config.mjs");

    const hasConfig = fileExists(tsConfig) || fileExists(jsConfig) || fileExists(mjsConfig);
    expect(hasConfig).toBe(true);
  });

  it("should have TypeScript configuration", () => {
    const tsConfig = path.join(projectRoot, "tsconfig.json");
    expect(fileExists(tsConfig)).toBe(true);

    const content = readFile(tsConfig);
    expect(content).not.toBeNull();

    const config = JSON.parse(content!);
    expect(config.compilerOptions.strict).toBe(true);
  });
});
