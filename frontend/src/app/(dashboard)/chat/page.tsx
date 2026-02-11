/** Chat Page
 *
 * Chat interface for task-based communication
 */

"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Row, Col, Select, Card, Typography, Empty, Spin } from "antd";
import { MessageOutlined } from "@ant-design/icons";
import { ChatContainer } from "@/components/chat/ChatContainer";
import { useTasks } from "@/hooks/useTasks";
import { useAuth } from "@/context/auth-context";

const { Title, Text } = Typography;
const { Option } = Select;

export default function ChatPage() {
  const searchParams = useSearchParams();
  const initialTaskId = searchParams.get("task");
  const { token } = useAuth();

  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(
    initialTaskId
  );

  const { tasks, loading } = useTasks();

  // Filter tasks that are suitable for chat (running or completed)
  const chatTasks = tasks.filter(
    (task) => task.status === "running" || task.status === "completed" || task.status === "pending"
  );

  const selectedTask = chatTasks.find((task) => task.id === selectedTaskId);

  return (
    <div style={{ height: "calc(100vh - 140px)" }}>
      <Row gutter={[16, 16]} style={{ height: "100%" }}>
        {/* Task Selector */}
        <Col span={24}>
          <Card size="small">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
              }}
            >
              <MessageOutlined style={{ fontSize: 20, color: "#1890ff" }} />
              <div style={{ flex: 1 }}>
                <Text strong>Select Task:</Text>
                <Select
                  style={{ width: 400, marginLeft: 16 }}
                  placeholder="Select a task to chat with"
                  value={selectedTaskId || undefined}
                  onChange={setSelectedTaskId}
                  loading={loading}
                  showSearch
                  optionFilterProp="children"
                >
                  {chatTasks.map((task) => (
                    <Option key={task.id} value={task.id}>
                      {task.name} ({task.status}) - {task.namespace}
                    </Option>
                  ))}
                </Select>
              </div>
              {selectedTask && (
                <div>
                  <Text type="secondary">
                    Task: <Text strong>{selectedTask.name}</Text> | Status:{" "}
                    <Text
                      strong
                      style={{
                        color:
                          selectedTask.status === "running"
                            ? "#1890ff"
                            : selectedTask.status === "completed"
                            ? "#52c41a"
                            : undefined,
                      }}
                    >
                      {selectedTask.status}
                    </Text>
                  </Text>
                </div>
              )}
            </div>
          </Card>
        </Col>

        {/* Chat Area */}
        <Col span={24} style={{ height: "calc(100% - 60px)" }}>
          {selectedTaskId ? (
            <ChatContainer
              taskId={selectedTaskId}
              token={token?.accessToken}
              title={`Chat: ${selectedTask?.name || "Task"}`}
            />
          ) : (
            <Card
              style={{
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Empty
                image={<MessageOutlined style={{ fontSize: 64, color: "#d9d9d9" }} />}
                description={
                  <div style={{ textAlign: "center" }}>
                    <Title level={4}>Select a Task to Start Chatting</Title>
                    <Text type="secondary">
                      Choose a task from the dropdown above to start a
                      conversation with the AI assistant.
                    </Text>
                  </div>
                }
              />
            </Card>
          )}
        </Col>
      </Row>
    </div>
  );
}
