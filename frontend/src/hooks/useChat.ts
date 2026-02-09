/** useChat Hook
 *
 * WebSocket-based chat hook for real-time task communication
 */

import { useState, useCallback, useEffect, useRef } from "react";
import type { MessageResponse, MessageRole } from "@/types";

// WebSocket event types
interface ChatMessageEvent {
  type: "chat:start" | "chat:chunk" | "chat:done" | "chat:error" | "chat:cancelled" | "chat:tool_start" | "chat:tool_result" | "chat:thinking";
  content?: string;
  data?: Record<string, unknown>;
  tool_call?: Record<string, unknown>;
  tool_result?: Record<string, unknown>;
  thinking?: string;
  error?: string;
  timestamp?: string;
}

interface UseChatOptions {
  taskId: string;
  token?: string;
  onMessage?: (message: MessageResponse) => void;
  onError?: (error: string) => void;
}

interface UseChatReturn {
  messages: MessageResponse[];
  isConnected: boolean;
  isConnecting: boolean;
  isStreaming: boolean;
  connectionError: string | null;
  sendMessage: (content: string) => void;
  cancelGeneration: () => void;
  requestHistory: (limit?: number, offset?: number) => void;
  clearMessages: () => void;
}

// Generate a temporary ID for optimistic updates
let tempIdCounter = 0;
const generateTempId = () => `temp-${Date.now()}-${++tempIdCounter}`;

export function useChat({
  taskId,
  token,
  onMessage,
  onError,
}: UseChatOptions): UseChatReturn {
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const currentAssistantMessageRef = useRef<Partial<MessageResponse> | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get WebSocket URL from environment
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

  const connect = useCallback(() => {
    if (!taskId || wsRef.current?.readyState === WebSocket.OPEN) return;

    setIsConnecting(true);
    setConnectionError(null);

    const url = `${wsUrl}/api/v1/tasks/${taskId}/chat?token=${token || ""}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      setIsConnecting(false);
      setConnectionError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data: ChatMessageEvent = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsConnecting(false);
      setIsStreaming(false);
    };

    ws.onerror = (error) => {
      setConnectionError("WebSocket connection error");
      setIsConnecting(false);
      onError?.("Connection error");
    };

    wsRef.current = ws;
  }, [taskId, token, wsUrl]);

  const handleWebSocketMessage = useCallback((data: ChatMessageEvent) => {
    switch (data.type) {
      case "chat:start":
        setIsStreaming(true);
        currentAssistantMessageRef.current = {
          id: generateTempId(),
          taskId,
          role: "assistant" as MessageRole,
          messageType: "text",
          content: "",
          threadId: taskId,
          sequence: messages.length + 1,
          meta: {},
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        break;

      case "chat:chunk":
        if (currentAssistantMessageRef.current) {
          currentAssistantMessageRef.current.content += data.content || "";
          // Update messages with streaming content
          setMessages((prev) => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage?.role === "assistant" && lastMessage.id.startsWith("temp-")) {
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, content: currentAssistantMessageRef.current?.content || "" } as MessageResponse,
              ];
            }
            return [
              ...prev,
              currentAssistantMessageRef.current as MessageResponse,
            ];
          });
        }
        break;

      case "chat:thinking":
        // Could be displayed separately or appended to content
        if (currentAssistantMessageRef.current) {
          currentAssistantMessageRef.current.meta = {
            ...currentAssistantMessageRef.current.meta,
            thinking: data.thinking,
          };
        }
        break;

      case "chat:tool_start":
        // Add tool call message
        const toolMessage: MessageResponse = {
          id: generateTempId(),
          taskId,
          role: "tool",
          messageType: "tool_call",
          content: `Using tool: ${data.tool_call?.name || "unknown"}`,
          threadId: taskId,
          sequence: messages.length + 1,
          toolName: data.tool_call?.name as string,
          toolCallId: data.tool_call?.id as string,
          meta: data.tool_call || {},
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, toolMessage]);
        break;

      case "chat:tool_result":
        // Add tool result message
        const toolResultMessage: MessageResponse = {
          id: generateTempId(),
          taskId,
          role: "tool",
          messageType: "tool_result",
          content: JSON.stringify(data.tool_result?.result || {}),
          threadId: taskId,
          sequence: messages.length + 1,
          toolCallId: data.tool_call?.id as string,
          meta: data.tool_result || {},
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, toolResultMessage]);
        break;

      case "chat:done":
        setIsStreaming(false);
        currentAssistantMessageRef.current = null;
        break;

      case "chat:cancelled":
        setIsStreaming(false);
        currentAssistantMessageRef.current = null;
        break;

      case "chat:error":
        setIsStreaming(false);
        setConnectionError(data.error || "Unknown error");
        onError?.(data.error || "Unknown error");
        break;
    }
  }, [taskId, messages.length, onError]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.("Not connected to chat");
      return;
    }

    // Add user message optimistically
    const userMessage: MessageResponse = {
      id: generateTempId(),
      taskId,
      role: "user",
      messageType: "text",
      content,
      threadId: taskId,
      sequence: messages.length + 1,
      meta: {},
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to server
    wsRef.current.send(
      JSON.stringify({
        type: "chat:send",
        content,
      })
    );
  }, [taskId, messages.length, onError]);

  const cancelGeneration = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "chat:cancel" }));
    }
  }, []);

  const requestHistory = useCallback((limit = 50, offset = 0) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "history:request",
          limit,
          offset,
        })
      );
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Connect on mount and when taskId/token changes
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    messages,
    isConnected,
    isConnecting,
    isStreaming,
    connectionError,
    sendMessage,
    cancelGeneration,
    requestHistory,
    clearMessages,
  };
}
