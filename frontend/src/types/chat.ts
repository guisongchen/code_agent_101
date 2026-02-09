/** Chat Types
 *
 * Based on backend/schemas/chat.py
 */

export interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  threadId?: string;
  stream?: boolean;
  showThinking?: boolean;
}

export interface ChatEvent {
  type: "content" | "tool_call" | "tool_result" | "thinking" | "error" | "done";
  data: Record<string, unknown>;
}

export interface ChatResponse {
  content: string;
  toolCalls?: Record<string, unknown>[];
  thinking?: string;
  error?: string;
  botName: string;
  namespace: string;
  threadId?: string;
  model?: string;
  usage?: { promptTokens: number; completionTokens: number; totalTokens: number };
}

export interface ChatValidationResponse {
  valid: boolean;
  botName: string;
  namespace: string;
  errors: string[];
  warnings: string[];
  ghost?: string;
  model?: string;
  shell?: string;
}

export interface ChatSessionInfo {
  threadId: string;
  botName: string;
  namespace: string;
  messageCount: number;
  createdAt?: string;
  lastActivity?: string;
}

// WebSocket event types for chat
export interface ChatStreamEvent {
  type: "chat:delta" | "chat:tool_call" | "chat:tool_result" | "chat:thinking" | "chat:complete" | "chat:error";
  content?: string;
  toolCall?: Record<string, unknown>;
  toolResult?: Record<string, unknown>;
  thinking?: string;
  error?: string;
  usage?: { promptTokens: number; completionTokens: number; totalTokens: number };
}
