/** Tasks API Service
 *
 * Task management API calls (list, create, update, delete, execute)
 */

import api from "./api";
import type {
  TaskResponse,
  TaskCreateRequest,
  TaskStatusUpdate,
  TaskStatus,
} from "@/types";

// =============================================================================
// Types
// =============================================================================

interface ListTasksOptions {
  namespace?: string;
  status?: TaskStatus;
  teamId?: string;
}

// =============================================================================
// Task API
// =============================================================================

export const taskApi = {
  /**
   * List all tasks with optional filtering
   */
  list: async (options: ListTasksOptions = {}): Promise<TaskResponse[]> => {
    const params = new URLSearchParams();
    if (options.namespace) params.append("namespace", options.namespace);
    if (options.status) params.append("status", options.status);
    if (options.teamId) params.append("team_id", options.teamId);

    const queryString = params.toString();
    const url = queryString ? `/tasks?${queryString}` : "/tasks";

    const response = await api.get<TaskResponse[]>(url);
    return response.data;
  },

  /**
   * Get a specific task by ID
   */
  get: async (taskId: string): Promise<TaskResponse> => {
    const response = await api.get<TaskResponse>(`/tasks/${taskId}`);
    return response.data;
  },

  /**
   * Create a new task
   */
  create: async (data: TaskCreateRequest): Promise<TaskResponse> => {
    const response = await api.post<TaskResponse>("/tasks", data);
    return response.data;
  },

  /**
   * Update task status (start, complete, fail, cancel)
   */
  updateStatus: async (
    taskId: string,
    update: TaskStatusUpdate
  ): Promise<TaskResponse> => {
    const response = await api.patch<TaskResponse>(
      `/tasks/${taskId}/status`,
      update
    );
    return response.data;
  },

  /**
   * Cancel a task
   */
  cancel: async (taskId: string): Promise<TaskResponse> => {
    return taskApi.updateStatus(taskId, { status: "cancelled" });
  },

  /**
   * Delete a task
   */
  delete: async (taskId: string): Promise<void> => {
    await api.delete(`/tasks/${taskId}`);
  },

  /**
   * Execute a task with chat_shell integration
   */
  execute: async (
    taskId: string,
    options?: { botName?: string; namespace?: string }
  ): Promise<TaskResponse> => {
    const params = new URLSearchParams();
    if (options?.botName) params.append("bot_name", options.botName);
    if (options?.namespace) params.append("namespace", options.namespace);

    const queryString = params.toString();
    const url = queryString
      ? `/tasks/${taskId}/execute?${queryString}`
      : `/tasks/${taskId}/execute`;

    const response = await api.post<TaskResponse>(url);
    return response.data;
  },
};
