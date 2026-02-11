/** Simplified Types for Personal Use
 *
 * Reduced from 6 complex resource types to 3 simple types:
 * - Agent (replaces Ghost + Model + Shell + Bot)
 * - Team (simplified)
 * - Task (simplified)
 */

// =============================================================================
// Agent Type (consolidated from Ghost + Model + Shell + Bot)
// =============================================================================

export interface Agent {
  id: string;
  name: string;
  description?: string;
  // Model configuration (simplified)
  modelProvider: string;
  modelName: string;
  apiKey?: string;
  // Ghost/Persona configuration
  systemPrompt: string;
  temperature?: number;
  // Shell capabilities
  toolsEnabled?: string[];
  autoInvokeTools?: boolean;
  maxIterations?: number;
  createdAt: string;
  updatedAt: string;
}

export interface AgentCreateRequest {
  name: string;
  description?: string;
  modelProvider: string;
  modelName: string;
  apiKey?: string;
  systemPrompt: string;
  temperature?: number;
  toolsEnabled?: string[];
  autoInvokeTools?: boolean;
  maxIterations?: number;
}

// =============================================================================
// Team Type (simplified)
// =============================================================================

export interface Team {
  id: string;
  name: string;
  description?: string;
  agentIds: string[];
  createdAt: string;
  updatedAt: string;
}

export interface TeamCreateRequest {
  name: string;
  description?: string;
  agentIds: string[];
}

// =============================================================================
// Task Type (simplified)
// =============================================================================

export type TaskStatus = "pending" | "running" | "paused" | "completed" | "failed" | "cancelled";

export interface Task {
  id: string;
  name: string;
  description?: string;
  agentId: string;
  status: TaskStatus;
  input?: string;
  output?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TaskCreateRequest {
  name: string;
  description?: string;
  agentId: string;
  input?: string;
}

// =============================================================================
// Message Type (for chat)
// =============================================================================

export type MessageRole = "user" | "assistant" | "tool" | "system";
export type MessageType = "text" | "tool_call" | "tool_result" | "thinking";

export interface Message {
  id: string;
  taskId: string;
  role: MessageRole;
  messageType: MessageType;
  content: string;
  toolName?: string;
  toolCallId?: string;
  meta?: Record<string, unknown>;
  createdAt: string;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface ListResponse<T> {
  items: T[];
  total: number;
}

export interface ChatMessageRequest {
  content: string;
}

export interface ChatStreamEvent {
  type: "start" | "chunk" | "done" | "error" | "tool_start" | "tool_result";
  content?: string;
  toolName?: string;
  toolCallId?: string;
  result?: unknown;
  error?: string;
}
