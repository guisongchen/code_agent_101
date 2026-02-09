/** Chat Interface Tests
 *
 * Tests for Epic 23: Real-time Chat Interface
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
// Test Suite: useChat Hook
// =============================================================================

describe("useChat Hook", () => {
  it("should have useChat hook file", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    expect(fileExists(hookPath)).toBe(true);
  });

  it("should export useChat hook", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("export function useChat");
  });

  it("should have WebSocket connection management", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("WebSocket");
    expect(content).toContain("wsRef");
  });

  it("should have connection state tracking", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("isConnected");
    expect(content).toContain("isConnecting");
  });

  it("should have streaming state", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("isStreaming");
  });

  it("should handle chat:send event", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("chat:send");
    expect(content).toContain("sendMessage");
  });

  it("should handle chat:cancel event", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("chat:cancel");
    expect(content).toContain("cancelGeneration");
  });

  it("should handle streaming events", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("chat:start");
    expect(content).toContain("chat:chunk");
    expect(content).toContain("chat:done");
  });

  it("should handle tool call events", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("chat:tool_start");
    expect(content).toContain("chat:tool_result");
  });

  it("should request message history", () => {
    const hookPath = path.join(frontendRoot, "src/hooks/useChat.ts");
    const content = readFile(hookPath);
    expect(content).toContain("history:request");
    expect(content).toContain("requestHistory");
  });
});

// =============================================================================
// Test Suite: ChatMessage Component
// =============================================================================

describe("ChatMessage Component", () => {
  it("should have ChatMessage component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export ChatMessage component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export function ChatMessage");
  });

  it("should have role-based styling", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("roleConfig");
    expect(content).toContain("user:");
    expect(content).toContain("assistant:");
  });

  it("should display user messages", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("user:");
    expect(content).toContain("UserOutlined");
  });

  it("should display assistant messages", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("assistant:");
    expect(content).toContain("RobotOutlined");
  });

  it("should display tool messages", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("tool:");
    expect(content).toContain("ToolOutlined");
  });

  it("should show typing indicator", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("isStreaming");
    expect(content).toContain("Typing");
  });

  it("should display tool call details", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("tool_call");
    expect(content).toContain("messageType === \"tool_call\"");
  });

  it("should display tool result", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatMessage.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("tool_result");
    expect(content).toContain("messageType === \"tool_result\"");
  });
});

// =============================================================================
// Test Suite: ChatInput Component
// =============================================================================

describe("ChatInput Component", () => {
  it("should have ChatInput component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatInput.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export ChatInput component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatInput.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export function ChatInput");
  });

  it("should have text input area", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatInput.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("TextArea");
  });

  it("should have send button", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatInput.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("SendOutlined");
    expect(content).toContain("onSend");
  });

  it("should have cancel button for streaming", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatInput.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("StopOutlined");
    expect(content).toContain("onCancel");
    expect(content).toContain("isStreaming");
  });

  it("should handle Enter key to send", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatInput.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("onKeyDown");
    expect(content).toContain('e.key === "Enter"');
  });
});

// =============================================================================
// Test Suite: ChatContainer Component
// =============================================================================

describe("ChatContainer Component", () => {
  it("should have ChatContainer component file", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    expect(fileExists(componentPath)).toBe(true);
  });

  it("should export ChatContainer component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("export function ChatContainer");
  });

  it("should use useChat hook", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("useChat");
  });

  it("should render ChatMessage components", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("ChatMessage");
  });

  it("should render ChatInput component", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("ChatInput");
  });

  it("should show connection status", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("isConnected");
    expect(content).toContain("Badge");
  });

  it("should auto-scroll to bottom", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("scrollIntoView");
    expect(content).toContain("messagesEndRef");
  });

  it("should request history on mount", () => {
    const componentPath = path.join(
      frontendRoot,
      "src/components/chat/ChatContainer.tsx"
    );
    const content = readFile(componentPath);
    expect(content).toContain("requestHistory");
    expect(content).toContain("useEffect");
  });
});

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

  it("should use ChatContainer component", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("ChatContainer");
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

  it("should use useTasks hook", () => {
    const pagePath = path.join(
      frontendRoot,
      "src/app/(dashboard)/chat/page.tsx"
    );
    const content = readFile(pagePath);
    expect(content).toContain("useTasks");
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
// Test Suite: Chat Components Index
// =============================================================================

describe("Chat Components Index", () => {
  it("should have index file for chat components", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/chat/index.ts"
    );
    expect(fileExists(indexPath)).toBe(true);
  });

  it("should export ChatMessage", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/chat/index.ts"
    );
    const content = readFile(indexPath);
    expect(content).toContain('export * from "./ChatMessage"');
  });

  it("should export ChatInput", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/chat/index.ts"
    );
    const content = readFile(indexPath);
    expect(content).toContain('export * from "./ChatInput"');
  });

  it("should export ChatContainer", () => {
    const indexPath = path.join(
      frontendRoot,
      "src/components/chat/index.ts"
    );
    const content = readFile(indexPath);
    expect(content).toContain('export * from "./ChatContainer"');
  });
});
