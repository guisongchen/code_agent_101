/** Authentication Context
 *
 * Provides auth state management, login/logout functions, and protected route wrapper
 */

"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import {
  AuthState,
  LoginRequest,
  RegisterRequest,
  UserResponse,
  Token,
} from "@/types";
import {
  login as loginApi,
  register as registerApi,
  getCurrentUser,
  storeToken,
  removeToken,
  storeUser,
  removeUser,
  getStoredUser,
  getToken,
} from "@/services/auth";

// =============================================================================
// Token Expiration Check
// =============================================================================

function isTokenExpired(token: Token): boolean {
  // Calculate expiration time (issued at + expires_in)
  // We consider token expired 60 seconds before actual expiry
  const bufferSeconds = 60;
  const expiryTime = Date.now() + (token.expiresIn * 1000) - (bufferSeconds * 1000);
  return Date.now() >= expiryTime;
}

// =============================================================================
// Context Types
// =============================================================================

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// =============================================================================
// Default State
// =============================================================================

const defaultAuthState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// =============================================================================
// Create Context
// =============================================================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// =============================================================================
// Auth Provider Component
// =============================================================================

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>(defaultAuthState);
  const router = useRouter();

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = () => {
      const token = getToken();
      const user = getStoredUser();

      if (token && user) {
        // Check if token is expired
        if (isTokenExpired(token)) {
          // Token expired, clear storage
          removeToken();
          removeUser();
          setState({
            ...defaultAuthState,
            isLoading: false,
          });
        } else {
          setState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        }
      } else {
        setState({
          ...defaultAuthState,
          isLoading: false,
        });
      }
    };

    initAuth();
  }, []);

  // Token refresh interval
  useEffect(() => {
    if (!state.isAuthenticated || !state.token) return;

    // Check token expiration every minute
    const interval = setInterval(() => {
      if (state.token && isTokenExpired(state.token)) {
        // Token expired, logout
        logout();
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [state.isAuthenticated, state.token]);

  // Login function
  const login = useCallback(async (credentials: LoginRequest) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const token = await loginApi(credentials);
      storeToken(token);

      // Fetch user info
      const user = await getCurrentUser();
      const userResponse: UserResponse = {
        id: user.id,
        username: user.username,
        email: user.email,
        defaultNamespace: user.defaultNamespace,
        role: user.role,
        isActive: true,
      };
      storeUser(userResponse);

      setState({
        user: userResponse,
        token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      router.push("/");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Login failed";
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
      throw error;
    }
  }, [router]);

  // Register function
  const register = useCallback(async (data: RegisterRequest) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      await registerApi(data);

      // Auto-login after registration
      await login({
        username: data.username,
        password: data.password,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Registration failed";
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
      }));
      throw error;
    }
  }, [login]);

  // Logout function
  const logout = useCallback(() => {
    removeToken();
    removeUser();
    setState({
      ...defaultAuthState,
      isLoading: false,
    });
    router.push("/login");
  }, [router]);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    try {
      const user = await getCurrentUser();
      const userResponse: UserResponse = {
        id: user.id,
        username: user.username,
        email: user.email,
        defaultNamespace: user.defaultNamespace,
        role: user.role,
        isActive: true,
      };
      storeUser(userResponse);
      setState((prev) => ({
        ...prev,
        user: userResponse,
      }));
    } catch {
      // If refresh fails, logout
      logout();
    }
  }, [logout]);

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// =============================================================================
// useAuth Hook
// =============================================================================

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// =============================================================================
// Protected Route Component
// =============================================================================

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
