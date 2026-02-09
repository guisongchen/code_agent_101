/** Chat Message Component
 *
 * Displays a single chat message with role-based styling
 */

import React from "react";
import { Avatar, Typography, Card, Tag, Space, Collapse } from "antd";
import {
  UserOutlined,
  RobotOutlined,
  ToolOutlined,
  InfoCircleOutlined,
  CodeOutlined,
} from "@ant-design/icons";
import type { MessageResponse } from "@/types";

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface ChatMessageProps {
  message: MessageResponse;
  isStreaming?: boolean;
}

const roleConfig = {
  user: {
    icon: <UserOutlined />,
    color: "#1890ff",
    bgColor: "#e6f7ff",
    label: "You",
    align: "right" as const,
  },
  assistant: {
    icon: <RobotOutlined />,
    color: "#52c41a",
    bgColor: "#f6ffed",
    label: "Assistant",
    align: "left" as const,
  },
  system: {
    icon: <InfoCircleOutlined />,
    color: "#faad14",
    bgColor: "#fffbe6",
    label: "System",
    align: "left" as const,
  },
  tool: {
    icon: <ToolOutlined />,
    color: "#722ed1",
    bgColor: "#f9f0ff",
    label: "Tool",
    align: "left" as const,
  },
};

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const config = roleConfig[message.role];
  const isToolCall = message.messageType === "tool_call";
  const isToolResult = message.messageType === "tool_result";

  // Format timestamp
  const timestamp = message.createdAt
    ? new Date(message.createdAt).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  // Render tool call content
  if (isToolCall) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "flex-start",
          marginBottom: 16,
        }}
      >
        <Card
          size="small"
          style={{
            maxWidth: "80%",
            background: config.bgColor,
            borderColor: config.color,
          }}
        >
          <Space>
            <Avatar
              size="small"
              icon={config.icon}
              style={{ backgroundColor: config.color }}
            />
            <Tag color={config.color}>{config.label}</Tag>
            <Text strong>{message.toolName || "Tool"}</Text>
          </Space>
          <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
            <pre
              style={{
                background: "rgba(0,0,0,0.05)",
                padding: 8,
                borderRadius: 4,
                fontSize: 12,
                overflow: "auto",
                maxHeight: 200,
              }}
            >
              {JSON.stringify(message.meta, null, 2)}
            </pre>
          </Paragraph>
          {timestamp && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {timestamp}
            </Text>
          )}
        </Card>
      </div>
    );
  }

  // Render tool result content
  if (isToolResult) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "flex-start",
          marginBottom: 16,
        }}
      >
        <Card
          size="small"
          style={{
            maxWidth: "80%",
            background: "#f5f5f5",
            borderColor: "#d9d9d9",
          }}
        >
          <Space>
            <CodeOutlined style={{ color: "#595959" }} />
            <Tag>Tool Result</Tag>
          </Space>
          <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
            <pre
              style={{
                background: "rgba(0,0,0,0.05)",
                padding: 8,
                borderRadius: 4,
                fontSize: 12,
                overflow: "auto",
                maxHeight: 200,
              }}
            >
              {typeof message.content === "string"
                ? message.content
                : JSON.stringify(message.meta, null, 2)}
            </pre>
          </Paragraph>
          {timestamp && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {timestamp}
            </Text>
          )}
        </Card>
      </div>
    );
  }

  // Render regular message
  return (
    <div
      style={{
        display: "flex",
        justifyContent: config.align === "right" ? "flex-end" : "flex-start",
        marginBottom: 16,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: config.align === "right" ? "row-reverse" : "row",
          alignItems: "flex-start",
          maxWidth: "80%",
          gap: 12,
        }}
      >
        <Avatar
          size="large"
          icon={config.icon}
          style={{
            backgroundColor: config.color,
            flexShrink: 0,
          }}
        />
        <div style={{ flex: 1 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 4,
              flexDirection:
                config.align === "right" ? "row-reverse" : "row",
            }}
          >
            <Text strong style={{ color: config.color }}>
              {config.label}
            </Text>
            {timestamp && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {timestamp}
              </Text>
            )}
            {isStreaming && (
              <Tag color="processing" style={{ margin: 0 }}>
                Typing...
              </Tag>
            )}
          </div>
          <Card
            size="small"
            style={{
              background: config.bgColor,
              borderColor: config.color,
            }}
          >
            <Paragraph style={{ margin: 0, whiteSpace: "pre-wrap" }}>
              {message.content}
            </Paragraph>
          </Card>

          {/* Show thinking if available */}
          {message.meta?.thinking && (
            <Collapse ghost style={{ marginTop: 8 }}>
              <Panel
                header={<Text type="secondary">Thinking Process</Text>}
                key="1"
              >
                <Paragraph
                  type="secondary"
                  style={{
                    margin: 0,
                    fontSize: 12,
                    fontStyle: "italic",
                  }}
                >
                  {message.meta.thinking as string}
                </Paragraph>
              </Panel>
            </Collapse>
          )}
        </div>
      </div>
    </div>
  );
}
