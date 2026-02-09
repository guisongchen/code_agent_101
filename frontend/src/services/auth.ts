/** Auth API Service
 *
 * Authentication-related API calls
 */

import api from "./api";
import {
  LoginRequest,
  RegisterRequest,
  Token,
  UserResponse,
  CurrentUser,
} from "@/types";

// =============================================================================
// Auth API Functions
// =============================================================================

/**
 * Login user with username and password
 */
export async function login(credentials: LoginRequest): Promise<Token> {
  // Use form data for OAuth2 password flow
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const response = await api.post<Token>("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
  return response.data;
}

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<UserResponse> {
  const response = await api.post<UserResponse>("/auth/register", data);
  return response.data;
}

/**
 * Get current user information
 */
export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<CurrentUser>("/auth/me");
  return response.data;
}

/**
 * Store token in localStorage
 */
export function storeToken(token: Token): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("token", JSON.stringify(token));
  }
}

/**
 * Get token from localStorage
 */
export function getToken(): Token | null {
  if (typeof window === "undefined") return null;
  const tokenStr = localStorage.getItem("token");
  if (!tokenStr) return null;
  try {
    return JSON.parse(tokenStr) as Token;
  } catch {
    return null;
  }
}

/**
 * Remove token from localStorage
 */
export function removeToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("token");
  }
}

/**
 * Store user in localStorage
 */
export function storeUser(user: UserResponse): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("user", JSON.stringify(user));
  }
}

/**
 * Get user from localStorage
 */
export function getStoredUser(): UserResponse | null {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr) as UserResponse;
  } catch {
    return null;
  }
}

/**
 * Remove user from localStorage
 */
export function removeUser(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("user");
  }
}
