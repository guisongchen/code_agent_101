/** Chat Container Component
 *
 * Main chat interface with message list, input, and connection status
 */

import React, { useRef, useEffect, useState } from "react";
import {
  Card,
  Alert,
  Space,
  Typography,
  Button,
  Badge,
  Tooltip,
  Empty,
} from "antd";
import {
  WifiOutlined,
  DisconnectOutlined,
  ReloadOutlined,
  ClearOutlined,
} from "@ant-design/icons";
import { useChat } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import type { MessageResponse } from "@/types";

const { Text } = Typography;

interface ChatContainerProps {
  taskId: string;
  token?: string;
  title?: string;
  initialMessages?: MessageResponse[];
  onError?: (error: string) => void;
}

export function ChatContainer({
  taskId,
  token,
  title = "Chat",
  initialMessages,
  onError,
}: ChatContainerProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const {
    messages,
    isConnected,
    isConnecting,
    isStreaming,
    connectionError,
    sendMessage,
    cancelGeneration,
    requestHistory,
    clearMessages,
  } = useChat({
    taskId,
    token,
    onError,
  });

  // Merge initial messages with received messages
  const displayMessages = initialMessages
    ? [...initialMessages, ...messages]
    : messages;

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, autoScroll]);

  // Handle scroll to detect if user scrolled up (disable auto-scroll)
  const handleScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        messagesContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  // Request history on mount
  useEffect(() => {
    if (isConnected) {
      requestHistory(50, 0);
    }
  }, [isConnected, requestHistory]);

  return (
    <Card
      title={
        <Space>
          <span>{title}</span>
          {isConnected ? (
            <Badge
              status="success"
              text={<Text type="success">Connected</Text>}
            />
          ) : isConnecting ? (
            <Badge
              status="processing"
              text={<Text type="secondary">Connecting...</Text>}
            />
          ) : (
            <Badge
              status="error"
              text={<Text type="danger">Disconnected</Text>}
            />
          )}
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="Load more history">
            <Button
              icon={<ReloadOutlined />}
              size="small"
              onClick={() => requestHistory(50, displayMessages.length)}
              disabled={!isConnected}
            >
              Load More
            </Button>
          </Tooltip>
          <Tooltip title="Clear messages">
            <Button
              icon={<ClearOutlined />}
              size="small"
              onClick={clearMessages}
              disabled={displayMessages.length === 0}
            >
              Clear
            </Button>
          </Tooltip>
          {isConnected ? (
            <WifiOutlined style={{ color: "#52c41a" }} />
          ) : (
            <DisconnectOutlined style={{ color: "#ff4d4f" }} />
          )}
        </Space>
      }
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
      bodyStyle={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        padding: "16px 24px",
      }}
    >
      {/* Connection Error */}
      {connectionError && (
        <Alert
          message="Connection Error"
          description={connectionError}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
        />
      )}

      {/* Messages List */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        style={{
          flex: 1,
          overflowY: "auto",
          paddingRight: 8,
          marginBottom: 16,
        }}
      >
        {displayMessages.length === 0 ? (
          <Empty
            description="No messages yet. Start a conversation!"
            style={{ marginTop: 100 }}
          />
        ) : (
          <>
            {displayMessages.map((message, index) => (
              <ChatMessage
                key={message.id || index}
                message={message}
                isStreaming={
                  isStreaming &&
                  index === displayMessages.length - 1 &&
                  message.role === "assistant"
                }
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <ChatInput
        onSend={sendMessage}
        onCancel={cancelGeneration}
        isStreaming={isStreaming}
        isConnected={isConnected}
      />
    </Card>
  );
}
