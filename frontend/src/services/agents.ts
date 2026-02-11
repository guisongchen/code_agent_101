/** Agent API Service
 *
 * Simple CRUD operations for agents
 */

import api from "@/lib/api";
import type { Agent, AgentCreateRequest, ListResponse } from "@/types";

export async function listAgents(): Promise<Agent[]> {
  const response = await api.get<ListResponse<Agent>>("/agents");
  return response.items;
}

export async function getAgent(id: string): Promise<Agent> {
  return api.get<Agent>(`/agents/${id}`);
}

export async function createAgent(data: AgentCreateRequest): Promise<Agent> {
  return api.post<Agent>("/agents", data);
}

export async function updateAgent(id: string, data: Partial<AgentCreateRequest>): Promise<Agent> {
  return api.patch<Agent>(`/agents/${id}`, data);
}

export async function deleteAgent(id: string): Promise<void> {
  return api.delete(`/agents/${id}`);
}
