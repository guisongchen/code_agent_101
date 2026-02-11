/** Chat Interface Tests
 *
 * Tests for Simplified Frontend - Chat with HTTP Polling
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
// Test Suite: Chat Page
// =============================================================================

describe("Chat Page", () => {
  it("should have chat page file", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    expect(fileExists(pagePath)).toBe(true);
  });

  it("should use HTTP polling (not WebSocket)", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("setInterval");
    expect(content).toContain("pollMessages");
    // Check for actual WebSocket usage, not just comments
    expect(content).not.toMatch(/new\s+WebSocket/);
    expect(content).not.toContain("WebSocket(");
  });

  it("should poll every 2 seconds", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("2000");
  });

  it("should NOT use useChat hook (simplified)", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).not.toContain("useChat");
  });

  it("should have task selector", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Select");
    expect(content).toContain("selectedTaskId");
  });

  it("should have message input area", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("TextArea");
  });

  it("should have send button", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("SendOutlined");
    expect(content).toContain("handleSend");
  });

  it("should read task ID from URL params", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("useSearchParams");
    expect(content).toContain('get("task")');
  });

  it("should be wrapped in Suspense", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("Suspense");
  });

  it("should use getTaskMessages service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("getTaskMessages");
  });

  it("should use sendMessage service", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("sendMessage");
  });

  it("should auto-scroll to bottom", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("scrollIntoView");
    expect(content).toContain("messagesEndRef");
  });
});

// =============================================================================
// Test Suite: Chat Navigation
// =============================================================================

describe("Chat Navigation", () => {
  it("should have Chat in navigation", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain('label: <Link href="/chat">Chat</Link>');
  });

  it("should have MessageOutlined icon for Chat", () => {
    const layoutPath = path.join(
      frontendRoot,
      "src/app/(dashboard)/layout.tsx"
    );
    const content = readFile(layoutPath);
    expect(content).toContain("MessageOutlined");
  });
});

// =============================================================================
// Test Suite: Chat Components (Old ones removed)
// =============================================================================

describe("Old Chat Components Removed", () => {
  it("should NOT have useChat hook file", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    expect(fileExists(hookPath)).toBe(false);
  });

  it("should NOT have ChatContainer component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    expect(fileExists(componentPath)).toBe(false);
  });

  it("should NOT have ChatMessage component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    expect(fileExists(componentPath)).toBe(false);
  });

  it("should NOT have ChatInput component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatInput.tsx"
    );
    expect(fileExists(componentPath)).toBe(false);
  });

  it("should NOT have chat components directory", () => {
    const dirPath = path.join(frontendRoot, "src/components/chat");
    expect(fileExists(dirPath)).toBe(false);
  });
});
