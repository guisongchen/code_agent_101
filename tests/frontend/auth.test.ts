/** Authentication Tests
 *
 * Tests for Epic 20: Authentication and User Management
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
// Test Suite: Login Page
// =============================================================================

describe("Login Page", () => {
  it("should have login page component", () => {
    const loginPagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    expect(fileExists(loginPagePath)).toBe(true);
  });

  it("should have username and password form fields", () => {
    const loginPagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    const content = readFile(loginPagePath);
    expect(content).not.toBeNull();

    expect(content).toContain('name="username"');
    expect(content).toContain('name="password"');
    expect(content).toContain("Input.Password");
  });

  it("should use useAuth hook for login", () => {
    const loginPagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    const content = readFile(loginPagePath);
    expect(content).toContain("useAuth");
    expect(content).toContain("login(");
  });

  it("should redirect to dashboard after login", () => {
    const loginPagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    const content = readFile(loginPagePath);
    expect(content).toContain('router.push("/")');
  });

  it("should show error message on failed login", () => {
    const loginPagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    const content = readFile(loginPagePath);
    expect(content).toContain("error");
    expect(content).toContain('type="error"');
  });
});

// =============================================================================
// Test Suite: Registration Page
// =============================================================================

describe("Registration Page", () => {
  it("should have registration page component", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    expect(fileExists(registerPagePath)).toBe(true);
  });

  it("should have all required form fields", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    const content = readFile(registerPagePath);
    expect(content).not.toBeNull();

    expect(content).toContain('name="username"');
    expect(content).toContain('name="email"');
    expect(content).toContain('name="password"');
    expect(content).toContain('name="confirmPassword"');
    expect(content).toContain('name="defaultNamespace"');
  });

  it("should validate password confirmation", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    const content = readFile(registerPagePath);
    expect(content).toContain("confirmPassword");
    expect(content).toContain("Passwords do not match");
  });

  it("should validate password length", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    const content = readFile(registerPagePath);
    expect(content).toContain("at least 8 characters");
  });

  it("should use useAuth hook for registration", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    const content = readFile(registerPagePath);
    expect(content).toContain("useAuth");
    expect(content).toContain("register(");
  });

  it("should have link to login page", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    const content = readFile(registerPagePath);
    expect(content).toContain('href="/login"');
  });
});

// =============================================================================
// Test Suite: Auth Context
// =============================================================================

describe("Auth Context", () => {
  it("should have auth context file", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    expect(fileExists(authContextPath)).toBe(true);
  });

  it("should export AuthProvider", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("export function AuthProvider");
  });

  it("should export useAuth hook", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("export function useAuth");
  });

  it("should export ProtectedRoute component", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("export function ProtectedRoute");
  });

  it("should have login function", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("const login = useCallback");
  });

  it("should have register function", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("const register = useCallback");
  });

  it("should have logout function", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("const logout = useCallback");
  });

  it("should store token in localStorage", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("storeToken");
    expect(content).toContain("localStorage");
  });

  it("should clear token on logout", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("removeToken");
    expect(content).toContain("removeUser");
  });

  it("should check token expiration", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("isTokenExpired");
  });

  it("should have token refresh interval", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("setInterval");
    expect(content).toContain("clearInterval");
  });
});

// =============================================================================
// Test Suite: Protected Route
// =============================================================================

describe("Protected Route", () => {
  it("should redirect to login when not authenticated", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain('router.push("/login")');
  });

  it("should show loading state while checking auth", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("isLoading");
    expect(content).toContain("Loading...");
  });

  it("should render children when authenticated", () => {
    const authContextPath = path.join(frontendRoot, "src/context/auth-context.tsx");
    const content = readFile(authContextPath);
    expect(content).toContain("return <>{children}</>");
  });
});

// =============================================================================
// Test Suite: Auth Services
// =============================================================================

describe("Auth Services", () => {
  it("should have auth service file", () => {
    const authServicePath = path.join(frontendRoot, "src/services/auth.ts");
    expect(fileExists(authServicePath)).toBe(true);
  });

  it("should export login function", () => {
    const authServicePath = path.join(frontendRoot, "src/services/auth.ts");
    const content = readFile(authServicePath);
    expect(content).toContain("export async function login");
  });

  it("should export register function", () => {
    const authServicePath = path.join(frontendRoot, "src/services/auth.ts");
    const content = readFile(authServicePath);
    expect(content).toContain("export async function register");
  });

  it("should export getCurrentUser function", () => {
    const authServicePath = path.join(frontendRoot, "src/services/auth.ts");
    const content = readFile(authServicePath);
    expect(content).toContain("export async function getCurrentUser");
  });

  it("should have token storage functions", () => {
    const authServicePath = path.join(frontendRoot, "src/services/auth.ts");
    const content = readFile(authServicePath);
    expect(content).toContain("export function storeToken");
    expect(content).toContain("export function getToken");
    expect(content).toContain("export function removeToken");
  });

  it("should use localStorage for persistence", () => {
    const authServicePath = path.join(frontendRoot, "src/services/auth.ts");
    const content = readFile(authServicePath);
    expect(content).toContain("localStorage.setItem");
    expect(content).toContain("localStorage.getItem");
    expect(content).toContain("localStorage.removeItem");
  });
});

// =============================================================================
// Test Suite: Login-Register Navigation
// =============================================================================

describe("Login-Register Navigation", () => {
  it("should have link to register page on login", () => {
    const loginPagePath = path.join(frontendRoot, "src/app/login/page.tsx");
    const content = readFile(loginPagePath);
    expect(content).toContain('href="/register"');
  });

  it("should have link to login page on register", () => {
    const registerPagePath = path.join(frontendRoot, "src/app/register/page.tsx");
    const content = readFile(registerPagePath);
    expect(content).toContain('href="/login"');
  });
});
