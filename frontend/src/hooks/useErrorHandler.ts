/** Error Handler Hook
 *
 * Custom hook for consistent error handling across the application.
 * Provides retry logic, error state management, and integration with Ant Design.
 */

import { useState, useCallback, useRef } from "react";
import { message } from "antd";
import { getApiError, ApiError } from "@/services/api";

// =============================================================================
// Types
// =============================================================================

interface UseErrorHandlerOptions {
  maxRetries?: number;
  retryDelay?: number;
  showNotification?: boolean;
  onError?: (error: ApiError) => void;
  onRetry?: (attempt: number) => void;
}

interface UseErrorHandlerReturn<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  execute: (...args: unknown[]) => Promise<T | null>;
  reset: () => void;
  retry: () => Promise<T | null>;
}

// =============================================================================
// Error Handler Hook
// =============================================================================

export function useErrorHandler<T = unknown>(
  asyncFunction: (...args: unknown[]) => Promise<T>,
  options: UseErrorHandlerOptions = {}
): UseErrorHandlerReturn<T> {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    showNotification = true,
    onError,
    onRetry,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  // Store the last arguments for retry functionality
  const lastArgsRef = useRef<unknown[]>([]);
  const retryCountRef = useRef(0);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    retryCountRef.current = 0;
    lastArgsRef.current = [];
  }, []);

  const executeWithRetry = useCallback(
    async (args: unknown[], attempt: number): Promise<T | null> => {
      try {
        setLoading(true);
        setError(null);

        const result = await asyncFunction(...args);
        setData(result);
        retryCountRef.current = 0;
        return result;
      } catch (err) {
        const apiError = getApiError(err);

        // Check if we should retry
        if (attempt < maxRetries && shouldRetry(apiError)) {
          retryCountRef.current = attempt;
          onRetry?.(attempt);

          // Wait before retrying
          await delay(retryDelay * attempt);
          return executeWithRetry(args, attempt + 1);
        }

        // Max retries reached or non-retryable error
        setError(apiError);

        if (showNotification) {
          message.error(apiError.message || "An error occurred");
        }

        onError?.(apiError);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [asyncFunction, maxRetries, retryDelay, showNotification, onError, onRetry]
  );

  const execute = useCallback(
    async (...args: unknown[]): Promise<T | null> => {
      lastArgsRef.current = args;
      retryCountRef.current = 0;
      return executeWithRetry(args, 0);
    },
    [executeWithRetry]
  );

  const retry = useCallback(async (): Promise<T | null> => {
    if (lastArgsRef.current.length === 0) {
      console.warn("No previous arguments to retry with");
      return null;
    }
    retryCountRef.current = 0;
    return executeWithRetry(lastArgsRef.current, 0);
  }, [executeWithRetry]);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    retry,
  };
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Determine if an error is retryable based on status code
 */
function shouldRetry(error: ApiError): boolean {
  // Retry on network errors (status 0) or server errors (5xx)
  if (error.status === 0) return true;
  if (error.status >= 500 && error.status < 600) return true;
  if (error.status === 429) return true; // Rate limited

  // Don't retry client errors (4xx except 429)
  return false;
}

/**
 * Simple delay utility
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// =============================================================================
// Convenience Hook for API Calls with Immediate Execution
// =============================================================================

interface UseApiCallOptions extends UseErrorHandlerOptions {
  immediate?: boolean;
}

export function useApiCall<T = unknown>(
  asyncFunction: (...args: unknown[]) => Promise<T>,
  options: UseApiCallOptions = {}
): UseErrorHandlerReturn<T> {
  const { immediate = false, ...handlerOptions } = options;

  const handler = useErrorHandler(asyncFunction, handlerOptions);

  // Note: We don't auto-execute here to avoid React hooks rules issues
  // The caller should use useEffect to trigger immediate execution if needed

  return handler;
}

// =============================================================================
// Hook for Handling Form Submission Errors
// =============================================================================

interface FormError {
  field: string;
  message: string;
}

interface UseFormErrorHandlerReturn {
  formErrors: FormError[];
  setFormErrors: (errors: FormError[]) => void;
  clearFieldError: (field: string) => void;
  handleApiError: (error: unknown) => void;
  hasError: (field: string) => boolean;
  getError: (field: string) => string | undefined;
}

export function useFormErrorHandler(): UseFormErrorHandlerReturn {
  const [formErrors, setFormErrors] = useState<FormError[]>([]);

  const clearFieldError = useCallback((field: string) => {
    setFormErrors((prev) => prev.filter((e) => e.field !== field));
  }, []);

  const handleApiError = useCallback((error: unknown) => {
    const apiError = getApiError(error);

    // Try to parse validation errors from the API response
    if (apiError.detail && typeof apiError.detail === "object") {
      const errors: FormError[] = [];

      // Handle FastAPI validation error format
      const detail = apiError.detail as unknown[];
      if (Array.isArray(detail)) {
        detail.forEach((item) => {
          const err = item as { loc?: string[]; msg?: string };
          if (err.loc && err.msg) {
            const field = err.loc[err.loc.length - 1];
            errors.push({ field, message: err.msg });
          }
        });
      }

      setFormErrors(errors);
    } else {
      // Generic error - show as toast
      message.error(apiError.message);
    }
  }, []);

  const hasError = useCallback(
    (field: string): boolean => {
      return formErrors.some((e) => e.field === field);
    },
    [formErrors]
  );

  const getError = useCallback(
    (field: string): string | undefined => {
      return formErrors.find((e) => e.field === field)?.message;
    },
    [formErrors]
  );

  return {
    formErrors,
    setFormErrors,
    clearFieldError,
    handleApiError,
    hasError,
    getError,
  };
}

export default useErrorHandler;
