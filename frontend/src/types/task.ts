/** Task Types
 *
 * Based on backend/schemas/task.py
 */

export type TaskStatus =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export interface TaskCreateRequest {
  name: string;
  namespace: string;
  teamId?: string;
  input?: string;
  spec?: Record<string, unknown>;
  createdBy?: string;
}

export interface TaskStatusUpdate {
  status: TaskStatus;
  output?: string;
  error?: string;
}

export interface TaskResponse {
  id: string;
  name: string;
  namespace: string;
  status: TaskStatus;
  teamId?: string;
  input?: string;
  output?: string;
  error?: string;
  spec?: Record<string, unknown>;
  startedAt?: string;
  completedAt?: string;
  createdBy?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TaskListResponse {
  items: TaskResponse[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}
