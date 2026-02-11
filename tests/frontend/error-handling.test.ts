/** Error Handling and User Feedback Tests
 *
 * Tests for Epic 25: Error Handling and User Feedback
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
// Test Suite: Error Boundary Component
// =============================================================================

describe("Error Boundary Component", () => {
  it("should have ErrorBoundary component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/error/ErrorBoundary.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export ErrorBoundary class component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/error/ErrorBoundary.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export class ErrorBoundary");
    expect(content).toContain("extends Component");
    expect(content).toContain("componentDidCatch");
  });
});

// =============================================================================
// Test Suite: Toast Notification System
// =============================================================================

describe("Toast Notification System", () => {
  it("should use Ant Design message API for notifications", () => {
    // Check that error handler uses message API
    const hookPath = path.join(
      frontendRoot,
      "src/hooks/useErrorHandler.ts"
    );
    const content = readFile(hookPath);
    expect(content).toContain('import { message } from "antd"');
    expect(content).toContain("message.error");
  });

  it("should show notifications in network status hook", () => {
    const hookPath = path.join(
      frontendRoot,
      "src/hooks/useNetworkStatus.ts"
    );
    const content = readFile(hookPath);
    expect(content).toContain("message");
    expect(content).toContain("from \"antd\"");
    expect(content).toContain("message.open");
    expect(content).toContain("message.success");
    expect(content).toContain("message.warning");
  });
});

// =============================================================================
// Test Suite: Form Validation
// =============================================================================

describe("Form Validation", () => {
  it("should have validation utilities file", () => {
    const validationPath = path.join(
      frontendRoot,
      "src/utils/validation.ts"
    );
    expect(fileExists(validationPath)).toBe(true);
  });

  it("should export validation functions", () => {
    const validationPath = path.join(
      frontendRoot,
      "src/utils/validation.ts"
    );
    const content = readFile(validationPath);
    expect(content).toContain("export function validateValue");
    expect(content).toContain("export function validateForm");
    expect(content).toContain("export function createValidationRule");
  });

  it("should have predefined validation presets", () => {
    const validationPath = path.join(
      frontendRoot,
      "src/utils/validation.ts"
    );
    const content = readFile(validationPath);
    expect(content).toContain("export const validationPresets");
    expect(content).toContain("username:");
    expect(content).toContain("password:");
    expect(content).toContain("email:");
    expect(content).toContain("resourceName:");
  });
});

// =============================================================================
// Test Suite: Error Handling Components
// =============================================================================

describe("Error Handling", () => {
  it("should have root error.tsx file", () => {
    const errorPath = path.join(frontendRoot, "src/app/error.tsx");
    expect(fileExists(errorPath)).toBe(true);
  });

  it("should have dashboard error.tsx file", () => {
    const errorPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/error.tsx"
    );
    expect(fileExists(errorPath)).toBe(true);
  });

  it("should have not-found.tsx file", () => {
    const notFoundPath = path.join(frontendRoot, "src/app/not-found.tsx");
    expect(fileExists(notFoundPath)).toBe(true);
  });

  it("should have error handler hook", () => {
    const hookPath = path.join(
      frontendRoot,
      "src/hooks/useErrorHandler.ts"
    );
    expect(fileExists(hookPath)).toBe(true);
  });
});

// =============================================================================
// Test Suite: Skeleton Screens
// =============================================================================

describe("Skeleton Screens", () => {
  it("should have SkeletonScreens component file", () => {
    const skeletonPath = path.join(
      frontendRoot,
      "src/components/ui/SkeletonScreens.tsx"
    );
    expect(fileExists(skeletonPath)).toBe(true);
  });

  it("should export multiple skeleton components", () => {
    const skeletonPath = path.join(
      frontendRoot,
      "src/components/ui/SkeletonScreens.tsx"
    );
    const content = readFile(skeletonPath);
    expect(content).toContain("export function TableSkeleton");
    expect(content).toContain("export function FormSkeleton");
    expect(content).toContain("export function DashboardSkeleton");
  });
});

// =============================================================================
// Test Suite: Network Status
// =============================================================================

describe("Network Status Detection", () => {
  it("should have useNetworkStatus hook", () => {
    const hookPath = path.join(
      frontendRoot,
      "src/hooks/useNetworkStatus.ts"
    );
    expect(fileExists(hookPath)).toBe(true);
  });

  it("should detect online/offline status", () => {
    const hookPath = path.join(
      frontendRoot,
      "src/hooks/useNetworkStatus.ts"
    );
    const content = readFile(hookPath);
    expect(content).toContain("navigator.onLine");
    expect(content).toContain("online");
    expect(content).toContain("offline");
  });
});

// =============================================================================
// Test Suite: Confirmation Dialogs
// =============================================================================

describe("Confirmation Dialogs", () => {
  it("should have ConfirmDialog component file", () => {
    const dialogPath = path.join(
      frontendRoot,
      "src/components/ui/ConfirmDialog.tsx"
    );
    expect(fileExists(dialogPath)).toBe(true);
  });

  it("should export confirm functions", () => {
    const dialogPath = path.join(
      frontendRoot,
      "src/components/ui/ConfirmDialog.tsx"
    );
    const content = readFile(dialogPath);
    expect(content).toContain("export function confirm");
    expect(content).toContain("export function confirmDelete");
    expect(content).toContain("export function useConfirmDialog");
  });
});

// =============================================================================
// Test Suite: Component Index Files
// =============================================================================

describe("Component Index Files", () => {
  it("should have error components index file", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/error/index.ts"
    );
    expect(fileExists(indexPath)).toBe(true);
  });

  it("should export ErrorBoundary from index", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/error/index.ts"
    );
    const content = readFile(indexPath);
    expect(content).toContain('export { ErrorBoundary');
  });

  it("should have UI components index file", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/ui/index.ts"
    );
    expect(fileExists(indexPath)).toBe(true);
  });
});
