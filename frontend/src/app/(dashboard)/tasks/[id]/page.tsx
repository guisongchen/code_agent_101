/** Task Detail Page
 *
 * Task detail view with execution logs and status tracking
 */

"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Typography,
  Divider,
  Timeline,
  Spin,
  Alert,
  Badge,
} from "antd";
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  StopOutlined,
  DeleteOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  PauseCircleOutlined,
} from "@ant-design/icons";
import { taskApi } from "@/services/tasks";
import type { TaskResponse, TaskStatus } from "@/types";

const { Title, Text } = Typography;

const statusColors: Record<TaskStatus, string> = {
  pending: "default",
  running: "processing",
  paused: "warning",
  completed: "success",
  failed: "error",
  cancelled: "default",
};

const statusLabels: Record<TaskStatus, string> = {
  pending: "Pending",
  running: "Running",
  paused: "Paused",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.id as string;

  const [task, setTask] = useState<TaskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchTask = async () => {
    try {
      setLoading(true);
      const data = await taskApi.get(taskId);
      setTask(data);
      setError(null);
    } catch (err) {
      setError("Failed to load task details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (taskId) {
      fetchTask();
    }
  }, [taskId]);

  // Auto-refresh for running tasks
  useEffect(() => {
    if (task?.status === "running") {
      const interval = setInterval(fetchTask, 3000);
      return () => clearInterval(interval);
    }
  }, [task?.status]);

  const handleExecute = async () => {
    try {
      setActionLoading(true);
      await taskApi.execute(taskId);
      await fetchTask();
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    try {
      setActionLoading(true);
      await taskApi.cancel(taskId);
      await fetchTask();
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      setActionLoading(true);
      await taskApi.delete(taskId);
      router.push("/tasks");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "50px" }}>
        <Spin size="large" />
        <p>Loading task details...</p>
      </div>
    );
  }

  if (error || !task) {
    return (
      <Alert
        message="Error"
        description={error || "Task not found"}
        type="error"
        showIcon
        action={
          <Button onClick={() => router.push("/tasks")}>
            Back to Tasks
          </Button>
        }
      />
    );
  }

  // Build execution timeline
  const timelineItems = [
    {
      dot: <ClockCircleOutlined />,
      color: "blue",
      children: (
        <div>
          <Text strong>Created</Text>
          <div>{new Date(task.createdAt).toLocaleString()}</div>
        </div>
      ),
    },
  ];

  if (task.startedAt) {
    timelineItems.push({
      dot: <PlayCircleOutlined style={{ color: "#52c41a" }} />,
      color: "green",
      children: (
        <div>
          <Text strong>Started</Text>
          <div>{new Date(task.startedAt).toLocaleString()}</div>
        </div>
      ),
    });
  }

  if (task.status === "completed" && task.completedAt) {
    timelineItems.push({
      dot: <CheckCircleOutlined style={{ color: "#52c41a" }} />,
      color: "green",
      children: (
        <div>
          <Text strong>Completed</Text>
          <div>{new Date(task.completedAt).toLocaleString()}</div>
        </div>
      ),
    });
  } else if (task.status === "failed") {
    timelineItems.push({
      dot: <CloseCircleOutlined style={{ color: "#ff4d4f" }} />,
      color: "red",
      children: (
        <div>
          <Text strong>Failed</Text>
          {task.completedAt && (
            <div>{new Date(task.completedAt).toLocaleString()}</div>
          )}
        </div>
      ),
    });
  } else if (task.status === "cancelled") {
    timelineItems.push({
      dot: <PauseCircleOutlined style={{ color: "#faad14" }} />,
      color: "orange",
      children: (
        <div>
          <Text strong>Cancelled</Text>
          {task.completedAt && (
            <div>{new Date(task.completedAt).toLocaleString()}</div>
          )}
        </div>
      ),
    });
  } else if (task.status === "running") {
    timelineItems.push({
      dot: <Spin size="small" />,
      color: "blue",
      children: (
        <div>
          <Text strong>Running</Text>
          <div>Task is currently executing...</div>
        </div>
      ),
    });
  }

  return (
    <div>
      {/* Header */}
      <div
        style={{
          marginBottom: 24,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => router.push("/tasks")}>
            Back
          </Button>
          <Title level={3} style={{ margin: 0 }}>
            Task: {task.name}
          </Title>
          <Badge
            status={
              task.status === "running"
                ? "processing"
                : task.status === "completed"
                ? "success"
                : task.status === "failed"
                ? "error"
                : "default"
            }
          />
          <Tag color={statusColors[task.status]}>
            {statusLabels[task.status]}
          </Tag>
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchTask}>
            Refresh
          </Button>
          {task.status === "pending" && (
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleExecute}
              loading={actionLoading}
            >
              Execute
            </Button>
          )}
          {task.status === "running" && (
            <Button
              danger
              icon={<StopOutlined />}
              onClick={handleCancel}
              loading={actionLoading}
            >
              Cancel
            </Button>
          )}
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={handleDelete}
            loading={actionLoading}
          >
            Delete
          </Button>
        </Space>
      </div>

      {/* Task Info */}
      <Card title="Task Information" style={{ marginBottom: 24 }}>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="Name">{task.name}</Descriptions.Item>
          <Descriptions.Item label="Namespace">
            <Tag>{task.namespace}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={statusColors[task.status]}>
              {statusLabels[task.status]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Team ID">
            {task.teamId ? (
              <Text code>{task.teamId}</Text>
            ) : (
              <Text type="secondary">-</Text>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="Created By">
            {task.createdBy || <Text type="secondary">-</Text>}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Execution Timeline */}
      <Card title="Execution Timeline" style={{ marginBottom: 24 }}>
        <Timeline items={timelineItems} />
      </Card>

      {/* Task Input */}
      {task.input && (
        <Card title="Task Input" style={{ marginBottom: 24 }}>
          <pre
            style={{
              background: "#f5f5f5",
              padding: 16,
              borderRadius: 4,
              overflow: "auto",
            }}
          >
            {task.input}
          </pre>
        </Card>
      )}

      {/* Task Output */}
      {task.output && (
        <Card title="Task Output" style={{ marginBottom: 24 }}>
          <pre
            style={{
              background: "#f6ffed",
              padding: 16,
              borderRadius: 4,
              overflow: "auto",
              border: "1px solid #b7eb8f",
            }}
          >
            {task.output}
          </pre>
        </Card>
      )}

      {/* Error Output */}
      {task.error && (
        <Card title="Error" style={{ marginBottom: 24 }}>
          <Alert
            message="Task Execution Error"
            description={
              <pre
                style={{
                  background: "#fff2f0",
                  padding: 16,
                  borderRadius: 4,
                  overflow: "auto",
                  margin: 0,
                }}
              >
                {task.error}
              </pre>
            }
            type="error"
            showIcon
          />
        </Card>
      )}

      {/* Task Spec */}
      {task.spec && Object.keys(task.spec).length > 0 && (
        <Card title="Task Spec">
          <pre
            style={{
              background: "#f5f5f5",
              padding: 16,
              borderRadius: 4,
              overflow: "auto",
            }}
          >
            {JSON.stringify(task.spec, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}
