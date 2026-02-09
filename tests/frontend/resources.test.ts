/** Resource Management Tests
 *
 * Tests for Epic 21: CRD Resource Management UI
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
// Test Suite: Resource List Component
// =============================================================================

describe("Resource List Component", () => {
  it("should have ResourceList component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export ResourceList component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export function ResourceList");
  });

  it("should have table for displaying resources", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("<Table");
  });

  it("should have create button", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("onCreate");
    expect(content).toContain("PlusOutlined");
  });

  it("should have edit action", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("onEdit");
    expect(content).toContain("EditOutlined");
  });

  it("should have delete action with confirmation", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("onDelete");
    expect(content).toContain("Popconfirm");
    expect(content).toContain("DeleteOutlined");
  });

  it("should have namespace filter", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("currentNamespace");
    expect(content).toContain("onNamespaceChange");
  });

  it("should have search functionality", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("onSearch");
    expect(content).toContain("SearchOutlined");
  });

  it("should have pagination", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceList.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("pagination");
    expect(content).toContain("showTotal");
  });
});

// =============================================================================
// Test Suite: Resource Form Component
// =============================================================================

describe("Resource Form Component", () => {
  it("should have ResourceForm component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceForm.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export ResourceForm component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceForm.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export function ResourceForm");
  });

  it("should have modal for form display", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceForm.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("<Modal");
  });

  it("should have form fields for metadata", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceForm.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain('["metadata", "name"]');
    expect(content).toContain('["metadata", "namespace"]');
    expect(content).toContain('["metadata", "description"]');
  });

  it("should have tabs for basic info and spec", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceForm.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("<Tabs");
    expect(content).toContain('key="basic"');
    expect(content).toContain('key="spec"');
  });

  it("should support both create and edit modes", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceForm.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("isEditing");
    expect(content).toContain("editing");
  });

  it("should have submit and cancel buttons", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/resources/ResourceForm.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("onSubmit");
    expect(content).toContain("onCancel");
    expect(content).toContain('htmlType="submit"');
  });
});

// =============================================================================
// Test Suite: useResources Hook
// =============================================================================

describe("useResources Hook", () => {
  it("should have useResources hook file", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useResources.ts");
    expect(fileExists(hookPath)).toBe(true);
  });

  it("should export useResources hook", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useResources.ts");
    const content = readFile(hookPath);
    expect(content).toContain("export function useResources");
  });

  it("should have CRUD operations", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useResources.ts");
    const content = readFile(hookPath);
    expect(content).toContain("createResource");
    expect(content).toContain("updateResource");
    expect(content).toContain("deleteResource");
    expect(content).toContain("fetchResources");
  });

  it("should have namespace management", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useResources.ts");
    const content = readFile(hookPath);
    expect(content).toContain("currentNamespace");
    expect(content).toContain("namespaces");
    expect(content).toContain("setCurrentNamespace");
  });

  it("should have loading state", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useResources.ts");
    const content = readFile(hookPath);
    expect(content).toContain("loading");
    expect(content).toContain("setLoading");
  });
});

// =============================================================================
// Test Suite: Resource Pages
// =============================================================================

describe("Resource Management Pages", () => {
  const pages = [
    { name: "ghosts", title: "Ghosts" },
    { name: "models", title: "Models" },
    { name: "shells", title: "Shells" },
    { name: "bots", title: "Bots" },
    { name: "teams", title: "Teams" },
    { name: "skills", title: "Skills" },
  ];

  it.each(pages)("should have $name page", ({ name }) => {
    const pagePath = path.join(
      frontendRoot,
      `src/app/(dashboard)/${name}/page.tsx`
    );
    expect(fileExists(pagePath)).toBe(true);
  });

  it.each(pages)("should use ResourceList in $name page", ({ name }) => {
    const pagePath = path.join(
      frontendRoot,
      `src/app/(dashboard)/${name}/page.tsx`
    );
    const content = readFile(pagePath);
    expect(content).toContain("ResourceList");
  });

  it.each(pages)("should use ResourceForm in $name page", ({ name }) => {
    const pagePath = path.join(
      frontendRoot,
      `src/app/(dashboard)/${name}/page.tsx`
    );
    const content = readFile(pagePath);
    expect(content).toContain("ResourceForm");
  });

  it.each(pages)("should use useResources hook in $name page", ({ name }) => {
    const pagePath = path.join(
      frontendRoot,
      `src/app/(dashboard)/${name}/page.tsx`
    );
    const content = readFile(pagePath);
    expect(content).toContain("useResources");
  });

  it.each(pages)("should have CRUD handlers in $name page", ({ name }) => {
    const pagePath = path.join(
      frontendRoot,
      `src/app/(dashboard)/${name}/page.tsx`
    );
    const content = readFile(pagePath);
    expect(content).toContain("handleCreate");
    expect(content).toContain("handleEdit");
    expect(content).toContain("handleDelete");
    expect(content).toContain("handleSubmit");
  });
});

// =============================================================================
// Test Suite: Resource API Services
// =============================================================================

describe("Resource API Services", () => {
  const resources = ["ghost", "model", "shell", "bot", "team", "skill"];

  it.each(resources)("should have %sApi export", (resource) => {
    const servicePath = path.join(frontendRoot, "src/services/resources.ts");
    const content = readFile(servicePath);
    expect(content).toContain(`export const ${resource}Api`);
  });

  it.each(resources)("%sApi should have list method", (resource) => {
    const servicePath = path.join(frontendRoot, "src/services/resources.ts");
    const content = readFile(servicePath);
    expect(content).toContain(`${resource}Api = {`);
    expect(content).toContain("list:");
  });

  it.each(resources)("%sApi should have create method", (resource) => {
    const servicePath = path.join(frontendRoot, "src/services/resources.ts");
    const content = readFile(servicePath);
    expect(content).toContain("create:");
  });

  it.each(resources)("%sApi should have update method", (resource) => {
    const servicePath = path.join(frontendRoot, "src/services/resources.ts");
    const content = readFile(servicePath);
    expect(content).toContain("update:");
  });

  it.each(resources)("%sApi should have delete method", (resource) => {
    const servicePath = path.join(frontendRoot, "src/services/resources.ts");
    const content = readFile(servicePath);
    expect(content).toContain("delete:");
  });
});

// =============================================================================
// Test Suite: Resource Components Index
// =============================================================================

describe("Resource Components Index", () => {
  it("should have index file for resource components", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/resources/index.ts"
    );
    expect(fileExists(indexPath)).toBe(true);
  });

  it("should export ResourceList from index", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/resources/index.ts"
    );
    const content = readFile(indexPath);
    expect(content).toContain('export * from "./ResourceList"');
  });

  it("should export ResourceForm from index", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/resources/index.ts"
    );
    const content = readFile(indexPath);
    expect(content).toContain('export * from "./ResourceForm"');
  });
});
