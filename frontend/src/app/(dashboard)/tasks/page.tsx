/** Tasks Management Page
 *
 * Task creation, monitoring, and management interface
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Typography,
  Tag,
  Button,
  Space,
  Select,
  Input,
  Popconfirm,
  Tooltip,
  Progress,
  Badge,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  PlusOutlined,
  PlayCircleOutlined,
  StopOutlined,
  EyeOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useTasks } from "@/hooks/useTasks";
import { useTeams } from "@/hooks/useTeams";
import { TaskCreateModal } from "@/components/tasks/TaskCreateModal";
import { ResourceList } from "@/components/resources";
import type { TaskResponse, TaskStatus } from "@/types";

const { Text } = Typography;
const { Option } = Select;

interface TaskListItem {
  id: string;
  name: string;
  namespace: string;
  status: TaskStatus;
  teamId?: string;
  teamName?: string;
  input?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

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

export default function TasksPage() {
  const router = useRouter();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [searchText, setSearchText] = useState("");

  const {
    tasks,
    loading,
    total,
    currentNamespace,
    namespaces,
    statusFilter,
    fetchTasks,
    createTask,
    cancelTask,
    deleteTask,
    executeTask,
    setCurrentNamespace,
    setStatusFilter,
  } = useTasks({ enableRealtime: true });

  const { teams } = useTeams();

  // Create team name lookup map
  const teamMap = React.useMemo(() => {
    const map = new Map<string, string>();
    teams.forEach((team) => {
      map.set(team.id, team.metadata.name);
    });
    return map;
  }, [teams]);

  // Filter tasks by search text
  const filteredTasks = React.useMemo(() => {
    if (!searchText) return tasks;
    return tasks.filter(
      (task) =>
        task.name.toLowerCase().includes(searchText.toLowerCase()) ||
        task.input?.toLowerCase().includes(searchText.toLowerCase())
    );
  }, [tasks, searchText]);

  const taskListItems: TaskListItem[] = filteredTasks.map((task) => ({
    id: task.id,
    name: task.name,
    namespace: task.namespace,
    status: task.status,
    teamId: task.teamId,
    teamName: task.teamId ? teamMap.get(task.teamId) : undefined,
    input: task.input,
    createdAt: task.createdAt,
    startedAt: task.startedAt,
    completedAt: task.completedAt,
  }));

  const handleCreate = async (values: {
    name: string;
    namespace: string;
    teamId?: string;
    input?: string;
  }) => {
    await createTask({
      name: values.name,
      namespace: values.namespace,
      teamId: values.teamId,
      input: values.input,
    });
    setCreateModalOpen(false);
  };

  const handleExecute = async (task: TaskListItem) => {
    await executeTask(task.id);
  };

  const handleCancel = async (task: TaskListItem) => {
    await cancelTask(task.id);
  };

  const handleDelete = async (task: TaskListItem) => {
    await deleteTask(task.id);
  };

  const handleView = (task: TaskListItem) => {
    router.push(`/tasks/${task.id}`);
  };

  const columns: ColumnsType<TaskListItem> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.id.slice(0, 8)}...
          </Text>
        </Space>
      ),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: TaskStatus) => (
        <Badge
          status={
            status === "running"
              ? "processing"
              : status === "completed"
              ? "success"
              : status === "failed"
              ? "error"
              : status === "pending"
              ? "warning"
              : "default"
          }
          text={<Tag color={statusColors[status]}>{statusLabels[status]}</Tag>}
        />
      ),
    },
    {
      title: "Namespace",
      dataIndex: "namespace",
      key: "namespace",
      width: 120,
      render: (text) => <Tag>{text}</Tag>,
    },
    {
      title: "Team",
      dataIndex: "teamName",
      key: "teamName",
      width: 150,
      render: (teamName, record) =>
        teamName ? (
          <Tag color="blue">{teamName}</Tag>
        ) : record.teamId ? (
          <Tag color="blue">{record.teamId.slice(0, 8)}...</Tag>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: "Input",
      dataIndex: "input",
      key: "input",
      ellipsis: true,
      render: (text) =>
        text ? (
          <Text ellipsis style={{ maxWidth: 300 }}>
            {text}
          </Text>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: "Created",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: "Actions",
      key: "actions",
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          {record.status === "pending" && (
            <Tooltip title="Execute">
              <Button
                type="text"
                icon={<PlayCircleOutlined style={{ color: "#52c41a" }} />}
                onClick={() => handleExecute(record)}
              />
            </Tooltip>
          )}
          {record.status === "running" && (
            <Tooltip title="Cancel">
              <Popconfirm
                title="Cancel Task"
                description="Are you sure you want to cancel this running task?"
                onConfirm={() => handleCancel(record)}
                okText="Yes"
                cancelText="No"
              >
                <Button
                  type="text"
                  icon={<StopOutlined style={{ color: "#faad14" }} />}
                />
              </Popconfirm>
            </Tooltip>
          )}
          <Tooltip title="Delete">
            <Popconfirm
              title="Delete Task"
              description="Are you sure you want to delete this task?"
              onConfirm={() => handleDelete(record)}
              okText="Yes"
              cancelText="No"
              okButtonProps={{ danger: true }}
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Status filter options
  const statusOptions: { label: string; value: TaskStatus | "all" }[] = [
    { label: "All Status", value: "all" },
    { label: "Pending", value: "pending" },
    { label: "Running", value: "running" },
    { label: "Completed", value: "completed" },
    { label: "Failed", value: "failed" },
    { label: "Cancelled", value: "cancelled" },
  ];

  return (
    <div>
      {/* Custom toolbar with status filter */}
      <div
        style={{
          marginBottom: 16,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Space>
          <Select
            placeholder="Filter by Status"
            value={statusFilter || "all"}
            onChange={(value) =>
              setStatusFilter(value === "all" ? undefined : (value as TaskStatus))
            }
            style={{ width: 150 }}
          >
            {statusOptions.map((option) => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
          <Input
            placeholder="Search tasks..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
            allowClear
          />
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchTasks}>
            Refresh
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalOpen(true)}
          >
            Create Task
          </Button>
        </Space>
      </div>

      <ResourceList<TaskListItem>
        title="Tasks"
        resources={taskListItems}
        loading={loading}
        total={total}
        currentNamespace={currentNamespace}
        namespaces={namespaces}
        columns={columns}
        onCreate={() => setCreateModalOpen(true)}
        onEdit={() => {}} // Tasks don't have edit, use view instead
        onDelete={() => {}} // Handled inline
        onNamespaceChange={setCurrentNamespace}
        createButtonText="Create Task"
      />

      <TaskCreateModal
        open={createModalOpen}
        teams={teams}
        namespaces={namespaces}
        onSubmit={handleCreate}
        onCancel={() => setCreateModalOpen(false)}
      />
    </div>
  );
}
