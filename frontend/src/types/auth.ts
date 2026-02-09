/** Authentication and User Types
 *
 * Based on backend/schemas/auth.py
 */

export type UserRole = "admin" | "user";

export interface Token {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface TokenPayload {
  sub?: string;
  exp?: number;
  iat?: number;
  role?: string;
}

export interface UserBase {
  username: string;
  email: string;
  defaultNamespace: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  defaultNamespace: string;
}

export interface UserResponse extends UserBase {
  id: string;
  role: UserRole;
  isActive: boolean;
  createdAt?: string;
}

export interface UserInDB extends UserBase {
  id: string;
  hashedPassword: string;
  role: UserRole;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  defaultNamespace: string;
}

export interface CurrentUser {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  defaultNamespace: string;
}

export interface AuthState {
  user: UserResponse | null;
  token: Token | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
