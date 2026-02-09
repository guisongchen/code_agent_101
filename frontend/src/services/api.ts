/** API Client
 *
 * Axios instance with interceptors for JWT token and error handling
 */

import axios, {
  AxiosInstance,
  AxiosError,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from "axios";

// =============================================================================
// API Configuration
// =============================================================================

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// =============================================================================
// Axios Instance
// =============================================================================

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds
});

// =============================================================================
// Request Interceptor - Add JWT Token
// =============================================================================

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage (only in browser)
    if (typeof window !== "undefined") {
      const tokenStr = localStorage.getItem("token");
      if (tokenStr) {
        try {
          const token = JSON.parse(tokenStr);
          if (token.accessToken) {
            config.headers.Authorization = `Bearer ${token.accessToken}`;
          }
        } catch {
          // Invalid token format, ignore
        }
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// =============================================================================
// Response Interceptor - Error Handling
// =============================================================================

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as { detail?: string; message?: string };

      switch (status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          if (typeof window !== "undefined") {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.location.href = "/login";
          }
          break;
        case 403:
          // Forbidden
          console.error("Access forbidden:", data?.detail || data?.message);
          break;
        case 404:
          // Not found
          console.error("Resource not found:", data?.detail || data?.message);
          break;
        case 422:
          // Validation error
          console.error("Validation error:", data?.detail || data?.message);
          break;
        case 500:
          // Server error
          console.error("Server error:", data?.detail || data?.message);
          break;
        default:
          console.error(`API error (${status}):`, data?.detail || data?.message);
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error("Network error: No response from server");
    } else {
      // Something happened in setting up the request
      console.error("Request error:", error.message);
    }

    return Promise.reject(error);
  }
);

// =============================================================================
// API Response Types
// =============================================================================

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

// =============================================================================
// Helper Functions
// =============================================================================

export function getApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    return {
      status: axiosError.response?.status || 500,
      message:
        axiosError.response?.data?.detail ||
        axiosError.response?.data?.message ||
        axiosError.message ||
        "An error occurred",
      detail: axiosError.response?.data?.detail,
    };
  }
  return {
    status: 500,
    message: error instanceof Error ? error.message : "An unknown error occurred",
  };
}

export default api;
