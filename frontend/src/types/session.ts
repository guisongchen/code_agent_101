/** Session Types
 *
 * Based on backend/schemas/session.py
 */

export type SessionStatus = "active" | "expired" | "closed" | "recovered";

export interface SessionCreateRequest {
  userId: number;
  taskId?: string;
  threadId?: string;
  sessionId?: string;
  meta?: Record<string, unknown>;
  expiresInHours?: number;
}

export interface SessionResponse {
  id: string;
  sessionId: string;
  userId: number;
  taskId?: string;
  threadId: string;
  status: SessionStatus;
  connectionCount: number;
  meta: Record<string, unknown>;
  lastActivityAt: string;
  expiresAt: string;
  recoveryToken?: string;
  createdAt: string;
  updatedAt: string;
}

export interface SessionRecoveryRequest {
  recoveryToken: string;
  sessionId?: string;
  meta?: Record<string, unknown>;
}

export interface SessionRecoveryResponse {
  success: boolean;
  session?: SessionResponse;
  message: string;
}

export interface SessionListRequest {
  userId?: number;
  taskId?: string;
  status?: SessionStatus;
  activeOnly?: boolean;
  limit?: number;
  offset?: number;
}

export interface SessionListResponse {
  sessions: SessionResponse[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface SessionMetrics {
  totalSessions: number;
  activeSessions: number;
  expiredSessions: number;
  closedSessions: number;
  recoveredSessions: number;
  totalConnections: number;
  avgConnectionsPerSession: number;
}

export interface SessionUpdateRequest {
  meta?: Record<string, unknown>;
  extendExpiry?: boolean;
  expiresInHours?: number;
}

export interface WebSocketSessionEvent {
  type: "session:state";
  sessionId: string;
  status: SessionStatus;
  connectionCount: number;
  expiresAt: string;
}

export interface WebSocketSessionRecoveryEvent {
  type: "session:recovered";
  success: boolean;
  sessionId?: string;
  previousSessionId?: string;
  message: string;
}
