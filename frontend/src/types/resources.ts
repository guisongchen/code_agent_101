/** Resource Types (CRD Resources)
 *
 * Based on backend/schemas/*.py for Ghost, Model, Shell, Bot, Team, Skill
 */

export type KindType = "ghost" | "model" | "shell" | "bot" | "team" | "skill";

// =============================================================================
// Base Types
// =============================================================================

export interface Metadata {
  name: string;
  namespace: string;
  createdBy?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface ResourceRef {
  kind: KindType;
  name: string;
  namespace: string;
}

export interface BaseSpec {
  description?: string;
}

export interface BaseCRD {
  apiVersion: string;
  kind: KindType;
  metadata: Metadata;
  spec: BaseSpec;
}

// =============================================================================
// Ghost Types
// =============================================================================

export interface GhostSpec extends BaseSpec {
  systemPrompt: string;
  contextWindow?: number;
  temperature?: number;
  toolsEnabled?: string[];
  metadata?: Record<string, unknown>;
}

export interface GhostCRD extends BaseCRD {
  kind: "ghost";
  spec: GhostSpec;
}

export interface GhostCreateRequest {
  metadata: Metadata;
  spec: GhostSpec;
}

export interface GhostResponse {
  id: string;
  apiVersion: string;
  kind: string;
  metadata: Metadata;
  spec: GhostSpec;
}

// =============================================================================
// Model Types
// =============================================================================

export interface ModelConfig {
  provider: string;
  modelName: string;
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

export interface ModelSpec extends BaseSpec {
  config: ModelConfig;
  capabilities?: string[];
  contextLength?: number;
  costPer1kTokens?: { input: number; output: number };
  defaultTemperature?: number;
  supportsStreaming?: boolean;
  metadata?: Record<string, unknown>;
}

export interface ModelCRD extends BaseCRD {
  kind: "model";
  spec: ModelSpec;
}

export interface ModelCreateRequest {
  metadata: Metadata;
  spec: ModelSpec;
}

export interface ModelResponse {
  id: string;
  apiVersion: string;
  kind: string;
  metadata: Metadata;
  spec: ModelSpec;
}

// =============================================================================
// Shell Types
// =============================================================================

export type ShellType = "chat" | "code" | "notebook";

export interface EnvironmentVariable {
  name: string;
  value?: string;
  secretRef?: string;
}

export interface ResourceLimits {
  cpu?: string;
  memory?: string;
  timeout?: number;
}

export interface ShellSpec extends BaseSpec {
  type: ShellType;
  image?: string;
  command?: string[];
  workingDir?: string;
  env?: EnvironmentVariable[];
  resources?: ResourceLimits;
  allowedTools?: string[];
  networkAccess?: boolean;
  persistentStorage?: boolean;
  metadata?: Record<string, unknown>;
}

export interface ShellCRD extends BaseCRD {
  kind: "shell";
  spec: ShellSpec;
}

export interface ShellCreateRequest {
  metadata: Metadata;
  spec: ShellSpec;
}

export interface ShellResponse {
  id: string;
  apiVersion: string;
  kind: string;
  metadata: Metadata;
  spec: ShellSpec;
}

// =============================================================================
// Bot Types
// =============================================================================

export interface BotSpec extends BaseSpec {
  ghostRef: ResourceRef;
  modelRef: ResourceRef;
  shellRef: ResourceRef;
  skills?: ResourceRef[];
  autoInvokeTools?: boolean;
  maxIterations?: number;
  metadata?: Record<string, unknown>;
}

export interface BotCRD extends BaseCRD {
  kind: "bot";
  spec: BotSpec;
}

export interface BotCreateRequest {
  metadata: Metadata;
  spec: BotSpec;
}

export interface BotResponse {
  id: string;
  apiVersion: string;
  kind: string;
  metadata: Metadata;
  spec: BotSpec;
}

// =============================================================================
// Team Types
// =============================================================================

export interface TeamMember {
  botRef: ResourceRef;
  role: string;
  priority?: number;
}

export interface TeamSpec extends BaseSpec {
  members: TeamMember[];
  coordinationStrategy?: string;
  sharedContext?: boolean;
  metadata?: Record<string, unknown>;
}

export interface TeamCRD extends BaseCRD {
  kind: "team";
  spec: TeamSpec;
}

export interface TeamCreateRequest {
  metadata: Metadata;
  spec: TeamSpec;
}

export interface TeamResponse {
  id: string;
  apiVersion: string;
  kind: string;
  metadata: Metadata;
  spec: TeamSpec;
}

// =============================================================================
// Skill Types
// =============================================================================

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface SkillSpec extends BaseSpec {
  version: string;
  author?: string;
  tools?: ToolDefinition[];
  dependencies?: string[];
  configSchema?: Record<string, unknown>;
  defaultConfig?: Record<string, unknown>;
  entryPoint?: string;
  metadata?: Record<string, unknown>;
}

export interface SkillCRD extends BaseCRD {
  kind: "skill";
  spec: SkillSpec;
}

export interface SkillCreateRequest {
  metadata: Metadata;
  spec: SkillSpec;
}

export interface SkillResponse {
  id: string;
  apiVersion: string;
  kind: string;
  metadata: Metadata;
  spec: SkillSpec;
}

// =============================================================================
// Resource List Response
// =============================================================================

export interface ResourceListResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}
