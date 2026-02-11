/** Chat Page with HTTP Polling
 *
 * Simplified chat interface using polling instead of WebSocket
 */

"use client";

import React, { useEffect, useState, useRef, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Select,
  Empty,
  message,
  Tag,
} from "antd";
import { SendOutlined, LoadingOutlined } from "@ant-design/icons";
import type { Task, MessageRole } from "@/types";
import { listTasks, getTaskMessages, sendMessage } from "@/services/tasks";

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
}

function ChatPageContent() {
  const searchParams = useSearchParams();
  const initialTaskId = searchParams.get("task");

  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(initialTaskId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load tasks on mount
  useEffect(() => {
    async function loadTasks() {
      try {
        const data = await listTasks();
        setTasks(data);
      } catch (error) {
        console.error("Failed to load tasks:", error);
      }
    }
    loadTasks();
  }, []);

  // Poll for messages when a task is selected
  const pollMessages = useCallback(async () => {
    if (!selectedTaskId) return;

    try {
      const data = await getTaskMessages(selectedTaskId);
      const formattedMessages: ChatMessage[] = data.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        createdAt: m.createdAt,
      }));
      setMessages((prev) => {
        // Only update if there are new messages
        if (formattedMessages.length !== prev.length) {
          return formattedMessages;
        }
        return prev;
      });
    } catch (error) {
      console.error("Failed to poll messages:", error);
    }
  }, [selectedTaskId]);

  // Start polling when task is selected
  useEffect(() => {
    if (selectedTaskId) {
      // Initial load
      pollMessages();
      // Start polling every 2 seconds
      pollIntervalRef.current = setInterval(pollMessages, 2000);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [selectedTaskId, pollMessages]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!inputValue.trim()) return;

    if (!selectedTaskId) {
      message.error("Please select a task first");
      return;
    }

    try {
      setSending(true);
      // Optimistically add message
      const tempMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: inputValue,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempMessage]);
      setInputValue("");

      // Send to server
      await sendMessage(selectedTaskId, inputValue);

      // Poll immediately for response
      await pollMessages();
    } catch (error) {
      console.error("Failed to send message:", error);
      message.error("Failed to send message");
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const selectedTask = tasks.find((t) => t.id === selectedTaskId);

  return (
    <div style={{ height: "calc(100vh - 140px)", display: "flex", flexDirection: "column" }}>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Title level={2} style={{ margin: 0 }}>Chat</Title>
        <Select
          placeholder="Select a task"
          value={selectedTaskId}
          onChange={setSelectedTaskId}
          style={{ width: 300 }}
          allowClear
        >
          {tasks.map((task) => (
            <Option key={task.id} value={task.id}>
              {task.name}
            </Option>
          ))}
        </Select>
      </div>

      {!selectedTaskId ? (
        <Empty description="Select a task to start chatting" style={{ marginTop: 100 }} />
      ) : (
        <Card
          style={{ flex: 1, display: "flex", flexDirection: "column" }}
          bodyStyle={{ flex: 1, display: "flex", flexDirection: "column", padding: 16 }}
          title={
            <Space>
              <span>{selectedTask?.name}</span>
              <Tag color={selectedTask?.status === "running" ? "processing" : "default"}>
                {selectedTask?.status}
              </Tag>
            </Space>
          }
        >
          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "0 8px",
              marginBottom: 16,
            }}
          >
            {messages.length === 0 ? (
              <Empty description="No messages yet. Start a conversation!" style={{ marginTop: 100 }} />
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    marginBottom: 16,
                    display: "flex",
                    justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      maxWidth: "70%",
                      padding: "12px 16px",
                      borderRadius: 12,
                      backgroundColor: msg.role === "user" ? "#1890ff" : "#f0f0f0",
                      color: msg.role === "user" ? "white" : "#333",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    <Text style={{ color: "inherit" }}>{msg.content}</Text>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{ display: "flex", gap: 8 }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              style={{ flex: 1 }}
              disabled={sending}
            />
            <Button
              type="primary"
              icon={sending ? <LoadingOutlined /> : <SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim() || sending}
            >
              Send
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<Empty description="Loading..." style={{ marginTop: 100 }} />}>
      <ChatPageContent />
    </Suspense>
  );
}
