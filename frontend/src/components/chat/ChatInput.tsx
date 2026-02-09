/** Chat Input Component
 *
 * Input area for sending chat messages with send and cancel functionality
 */

import React, { useState, useRef, useEffect } from "react";
import { Input, Button, Space, Tooltip } from "antd";
import {
  SendOutlined,
  StopOutlined,
  LoadingOutlined,
} from "@ant-design/icons";

const { TextArea } = Input;

interface ChatInputProps {
  onSend: (message: string) => void;
  onCancel?: () => void;
  isStreaming?: boolean;
  isConnected?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  onCancel,
  isStreaming,
  isConnected,
  placeholder = "Type a message...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !isStreaming) {
      onSend(message.trim());
      setMessage("");
      // Focus back on textarea after sending
      setTimeout(() => textareaRef.current?.focus(), 0);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCancel = () => {
    onCancel?.();
  };

  return (
    <div
      style={{
        borderTop: "1px solid #f0f0f0",
        padding: "16px 0",
        background: "#fff",
      }}
    >
      <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
        <TextArea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isConnected ? placeholder : "Connecting..."}
          disabled={!isConnected || isStreaming}
          autoSize={{ minRows: 1, maxRows: 6 }}
          style={{ flex: 1 }}
        />
        <Space>
          {isStreaming ? (
            <Tooltip title="Cancel generation">
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleCancel}
                size="large"
              />
            </Tooltip>
          ) : (
            <Tooltip title="Send message (Enter)">
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                disabled={!message.trim() || !isConnected}
                size="large"
              />
            </Tooltip>
          )}
        </Space>
      </div>
      <div style={{ marginTop: 8, textAlign: "right" }}>
        {isStreaming ? (
          <span style={{ color: "#1890ff", fontSize: 12 }}>
            <LoadingOutlined /> AI is generating...
          </span>
        ) : (
          <span style={{ color: "#999", fontSize: 12 }}>
            Press Enter to send, Shift+Enter for new line
          </span>
        )}
      </div>
    </div>
  );
}
