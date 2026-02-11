/** Task API Service
 *
 * Simple CRUD operations for tasks
 */

import api from "@/lib/api";
import type { Task, TaskCreateRequest, ListResponse, Message } from "@/types";

export async function listTasks(): Promise<Task[]> {
  const response = await api.get<ListResponse<Task>>("/tasks");
  return response.items;
}

export async function getTask(id: string): Promise<Task> {
  return api.get<Task>(`/tasks/${id}`);
}

export async function createTask(data: TaskCreateRequest): Promise<Task> {
  return api.post<Task>("/tasks", data);
}

export async function updateTask(id: string, data: Partial<TaskCreateRequest>): Promise<Task> {
  return api.patch<Task>(`/tasks/${id}`, data);
}

export async function deleteTask(id: string): Promise<void> {
  return api.delete(`/tasks/${id}`);
}

export async function getTaskMessages(taskId: string): Promise<Message[]> {
  const response = await api.get<ListResponse<Message>>(`/tasks/${taskId}/messages`);
  return response.items;
}

export async function sendMessage(taskId: string, content: string): Promise<void> {
  return api.post(`/tasks/${taskId}/messages`, { content });
}
