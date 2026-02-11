/** Network Status Hook
 *
 * Detects online/offline status and notifies users when connection changes.
 * Provides retry functionality for failed requests when connection is restored.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { message, Button, Space } from "antd";
import {
  WifiOutlined,
  DisconnectOutlined,
  ReloadOutlined,
} from "@ant-design/icons";

// =============================================================================
// Types
// =============================================================================

interface NetworkStatus {
  isOnline: boolean;
  wasOffline: boolean;
  checkConnection: () => Promise<boolean>;
}

interface UseNetworkStatusOptions {
  showNotifications?: boolean;
  onOffline?: () => void;
  onOnline?: () => void;
  checkInterval?: number; // ms, 0 to disable
}

// =============================================================================
// Network Status Hook
// =============================================================================

export function useNetworkStatus(
  options: UseNetworkStatusOptions = {}
): NetworkStatus {
  const {
    showNotifications = true,
    onOffline,
    onOnline,
    checkInterval = 0,
  } = options;

  const [isOnline, setIsOnline] = useState(true);
  const [wasOffline, setWasOffline] = useState(false);
  const notificationKeyRef = useRef<string | null>(null);

  // Check actual connection by making a lightweight request
  const checkConnection = useCallback(async (): Promise<boolean> => {
    try {
      // Try to fetch a small resource or use navigator.onLine as fallback
      const online = navigator.onLine;

      if (!online) {
        return false;
      }

      // Additional check: try to ping the API
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/health`, {
          method: "HEAD",
          signal: controller.signal,
          cache: "no-store",
        });
        clearTimeout(timeoutId);
        return true;
      } catch {
        clearTimeout(timeoutId);
        // If health check fails but browser says online, we're likely online
        // but the server might be down
        return navigator.onLine;
      }
    } catch {
      return navigator.onLine;
    }
  }, []);

  // Handle going offline
  const handleOffline = useCallback(() => {
    setIsOnline(false);
    setWasOffline(true);
    onOffline?.();

    if (showNotifications) {
      notificationKeyRef.current = "network-offline";
      message.open({
        key: notificationKeyRef.current,
        type: "warning",
        duration: 0, // Don't auto-close
        icon: <DisconnectOutlined />,
        content: (
          <Space>
            <span>You are offline</span>
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => {
                checkConnection().then((online) => {
                  if (online) {
                    setIsOnline(true);
                    message.success("Connection restored", 2);
                  } else {
                    message.error("Still offline", 2);
                  }
                });
              }}
            >
              Retry
            </Button>
          </Space>
        ),
      });
    }
  }, [checkConnection, onOffline, showNotifications]);

  // Handle going online
  const handleOnline = useCallback(() => {
    setIsOnline(true);
    onOnline?.();

    if (showNotifications && wasOffline) {
      // Close the offline notification
      if (notificationKeyRef.current) {
        message.destroy(notificationKeyRef.current);
      }

      message.open({
        type: "success",
        icon: <WifiOutlined />,
        content: "Connection restored",
        duration: 3,
      });
    }
  }, [onOnline, showNotifications, wasOffline]);

  // Set up event listeners
  useEffect(() => {
    // Set initial state
    setIsOnline(navigator.onLine);

    // Add event listeners
    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);

    // Optional periodic check
    let intervalId: NodeJS.Timeout | null = null;
    if (checkInterval > 0) {
      intervalId = setInterval(() => {
        checkConnection().then((online) => {
          if (online !== isOnline) {
            if (online) {
              handleOnline();
            } else {
              handleOffline();
            }
          }
        });
      }, checkInterval);
    }

    // Cleanup
    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
      if (intervalId) {
        clearInterval(intervalId);
      }
      if (notificationKeyRef.current) {
        message.destroy(notificationKeyRef.current);
      }
    };
  }, [
    checkConnection,
    checkInterval,
    handleOffline,
    handleOnline,
    isOnline,
  ]);

  return {
    isOnline,
    wasOffline,
    checkConnection,
  };
}

// =============================================================================
// Hook for Online-Only Operations
// =============================================================================

interface UseOnlineOperationOptions {
  onOfflineAttempt?: () => void;
  offlineMessage?: string;
}

interface UseOnlineOperationReturn<T> {
  executeIfOnline: (operation: () => Promise<T>) => Promise<T | null>;
  isOnline: boolean;
}

export function useOnlineOperation<T = unknown>(
  options: UseOnlineOperationOptions = {}
): UseOnlineOperationReturn<T> {
  const { onOfflineAttempt, offlineMessage = "This action requires an internet connection" } =
    options;

  const { isOnline } = useNetworkStatus({ showNotifications: false });

  const executeIfOnline = useCallback(
    async (operation: () => Promise<T>): Promise<T | null> => {
      if (!isOnline) {
        onOfflineAttempt?.();
        message.warning(offlineMessage);
        return null;
      }

      try {
        return await operation();
      } catch (error) {
        // Re-throw to let caller handle
        throw error;
      }
    },
    [isOnline, onOfflineAttempt, offlineMessage]
  );

  return {
    executeIfOnline,
    isOnline,
  };
}

// =============================================================================
// Hook for Retry with Backoff
// =============================================================================

interface RetryOptions {
  maxAttempts?: number;
  baseDelay?: number;
  maxDelay?: number;
  onRetry?: (attempt: number, error: Error) => void;
}

export function useRetryWithBackoff(options: RetryOptions = {}) {
  const { maxAttempts = 3, baseDelay = 1000, maxDelay = 10000, onRetry } =
    options;

  const retry = useCallback(
    async <T,>(operation: () => Promise<T>): Promise<T> => {
      let lastError: Error;

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          return await operation();
        } catch (error) {
          lastError = error instanceof Error ? error : new Error(String(error));

          if (attempt === maxAttempts) {
            throw lastError;
          }

          onRetry?.(attempt, lastError);

          // Exponential backoff with jitter
          const delay = Math.min(
            baseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000,
            maxDelay
          );

          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }

      throw lastError!;
    },
    [maxAttempts, baseDelay, maxDelay, onRetry]
  );

  return { retry };
}

export default useNetworkStatus;
