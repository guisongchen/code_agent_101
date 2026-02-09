/** Message Types
 *
 * Based on backend/schemas/message.py
 */

export type MessageRole = "user" | "assistant" | "system" | "tool";

export type MessageType = "text" | "thinking" | "tool_call" | "tool_result" | "error";

export interface MessageCreateRequest {
  taskId: string;
  role: MessageRole;
  content: string;
  messageType?: MessageType;
  threadId?: string;
  sequence?: number;
  tokensUsed?: number;
  promptTokens?: number;
  completionTokens?: number;
  model?: string;
  toolName?: string;
  toolCallId?: string;
  meta?: Record<string, unknown>;
}

export interface MessageResponse {
  id: string;
  taskId: string;
  role: MessageRole;
  messageType: MessageType;
  content: string;
  threadId: string;
  sequence: number;
  tokensUsed?: number;
  promptTokens?: number;
  completionTokens?: number;
  model?: string;
  toolName?: string;
  toolCallId?: string;
  meta: Record<string, unknown>;
  generatedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface MessageHistoryRequest {
  threadId?: string;
  limit?: number;
  offset?: number;
  beforeSequence?: number;
  afterSequence?: number;
}

export interface MessageHistoryResponse {
  taskId: string;
  threadId?: string;
  messages: MessageResponse[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface MessageHistorySyncEvent {
  type: "history:sync";
  taskId: string;
  threadId: string;
  messages: MessageResponse[];
  total: number;
  hasMore: boolean;
}

export interface MessageHistoryRequestEvent {
  type: "history:request";
  threadId?: string;
  limit: number;
  offset: number;
}
