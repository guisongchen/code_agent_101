/** Resources API Service
 *
 * CRD resource API calls (Ghost, Model, Shell, Bot, Team, Skill)
 */

import api from "./api";
import {
  GhostResponse,
  GhostCreateRequest,
  ModelResponse,
  ModelCreateRequest,
  ShellResponse,
  ShellCreateRequest,
  BotResponse,
  BotCreateRequest,
  TeamResponse,
  TeamCreateRequest,
  SkillResponse,
  SkillCreateRequest,
  ResourceListResponse,
  KindType,
} from "@/types";

// =============================================================================
// Generic Resource API
// =============================================================================

interface ListOptions {
  namespace?: string;
  limit?: number;
  offset?: number;
}

async function listResources<T>(
  kind: KindType,
  options: ListOptions = {}
): Promise<ResourceListResponse<T>> {
  const params = new URLSearchParams();
  if (options.namespace) params.append("namespace", options.namespace);
  if (options.limit) params.append("limit", options.limit.toString());
  if (options.offset) params.append("offset", options.offset.toString());

  const response = await api.get<ResourceListResponse<T>>(
    `/kinds/${kind}s?${params.toString()}`
  );
  return response.data;
}

async function getResource<T>(
  kind: KindType,
  name: string,
  namespace: string = "default"
): Promise<T> {
  const response = await api.get<T>(
    `/kinds/${kind}s/${name}?namespace=${namespace}`
  );
  return response.data;
}

async function createResource<T>(
  kind: KindType,
  data: unknown
): Promise<T> {
  const response = await api.post<T>(`/kinds/${kind}s`, data);
  return response.data;
}

async function updateResource<T>(
  kind: KindType,
  name: string,
  data: unknown,
  namespace: string = "default"
): Promise<T> {
  const response = await api.put<T>(
    `/kinds/${kind}s/${name}?namespace=${namespace}`,
    data
  );
  return response.data;
}

async function deleteResource(
  kind: KindType,
  name: string,
  namespace: string = "default"
): Promise<void> {
  await api.delete(`/kinds/${kind}s/${name}?namespace=${namespace}`);
}

// =============================================================================
// Ghost API
// =============================================================================

export const ghostApi = {
  list: (options?: ListOptions) =>
    listResources<GhostResponse>("ghost", options),
  get: (name: string, namespace?: string) =>
    getResource<GhostResponse>("ghost", name, namespace),
  create: (data: GhostCreateRequest) =>
    createResource<GhostResponse>("ghost", data),
  update: (name: string, data: GhostCreateRequest, namespace?: string) =>
    updateResource<GhostResponse>("ghost", name, data, namespace),
  delete: (name: string, namespace?: string) =>
    deleteResource("ghost", name, namespace),
};

// =============================================================================
// Model API
// =============================================================================

export const modelApi = {
  list: (options?: ListOptions) =>
    listResources<ModelResponse>("model", options),
  get: (name: string, namespace?: string) =>
    getResource<ModelResponse>("model", name, namespace),
  create: (data: ModelCreateRequest) =>
    createResource<ModelResponse>("model", data),
  update: (name: string, data: ModelCreateRequest, namespace?: string) =>
    updateResource<ModelResponse>("model", name, data, namespace),
  delete: (name: string, namespace?: string) =>
    deleteResource("model", name, namespace),
};

// =============================================================================
// Shell API
// =============================================================================

export const shellApi = {
  list: (options?: ListOptions) =>
    listResources<ShellResponse>("shell", options),
  get: (name: string, namespace?: string) =>
    getResource<ShellResponse>("shell", name, namespace),
  create: (data: ShellCreateRequest) =>
    createResource<ShellResponse>("shell", data),
  update: (name: string, data: ShellCreateRequest, namespace?: string) =>
    updateResource<ShellResponse>("shell", name, data, namespace),
  delete: (name: string, namespace?: string) =>
    deleteResource("shell", name, namespace),
};

// =============================================================================
// Bot API
// =============================================================================

export const botApi = {
  list: (options?: ListOptions) =>
    listResources<BotResponse>("bot", options),
  get: (name: string, namespace?: string) =>
    getResource<BotResponse>("bot", name, namespace),
  create: (data: BotCreateRequest) =>
    createResource<BotResponse>("bot", data),
  update: (name: string, data: BotCreateRequest, namespace?: string) =>
    updateResource<BotResponse>("bot", name, data, namespace),
  delete: (name: string, namespace?: string) =>
    deleteResource("bot", name, namespace),
};

// =============================================================================
// Team API
// =============================================================================

export const teamApi = {
  list: (options?: ListOptions) =>
    listResources<TeamResponse>("team", options),
  get: (name: string, namespace?: string) =>
    getResource<TeamResponse>("team", name, namespace),
  create: (data: TeamCreateRequest) =>
    createResource<TeamResponse>("team", data),
  update: (name: string, data: TeamCreateRequest, namespace?: string) =>
    updateResource<TeamResponse>("team", name, data, namespace),
  delete: (name: string, namespace?: string) =>
    deleteResource("team", name, namespace),
};

// =============================================================================
// Skill API
// =============================================================================

export const skillApi = {
  list: (options?: ListOptions) =>
    listResources<SkillResponse>("skill", options),
  get: (name: string, namespace?: string) =>
    getResource<SkillResponse>("skill", name, namespace),
  create: (data: SkillCreateRequest) =>
    createResource<SkillResponse>("skill", data),
  update: (name: string, data: SkillCreateRequest, namespace?: string) =>
    updateResource<SkillResponse>("skill", name, data, namespace),
  delete: (name: string, namespace?: string) =>
    deleteResource("skill", name, namespace),
};
