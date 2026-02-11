/** Team API Service
 *
 * Simple CRUD operations for teams
 */

import api from "@/lib/api";
import type { Team, TeamCreateRequest, ListResponse } from "@/types";

export async function listTeams(): Promise<Team[]> {
  const response = await api.get<ListResponse<Team>>("/teams");
  return response.items;
}

export async function getTeam(id: string): Promise<Team> {
  return api.get<Team>(`/teams/${id}`);
}

export async function createTeam(data: TeamCreateRequest): Promise<Team> {
  return api.post<Team>("/teams", data);
}

export async function updateTeam(id: string, data: Partial<TeamCreateRequest>): Promise<Team> {
  return api.patch<Team>(`/teams/${id}`, data);
}

export async function deleteTeam(id: string): Promise<void> {
  return api.delete(`/teams/${id}`);
}
