/** Tasks Page
 *
 * Simple task management with inline CRUD
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Table,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  message,
  Popconfirm,
} from "antd";
import { PlusOutlined, PlayCircleOutlined, DeleteOutlined } from "@ant-design/icons";
import type { Task, TaskCreateRequest, TaskStatus, Agent } from "@/types";
import { listTasks, createTask, deleteTask } from "@/services/tasks";
import { listAgents } from "@/services/agents";

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const statusColors: Record<TaskStatus, string> = {
  pending: "default",
  running: "processing",
  paused: "warning",
  completed: "success",
  failed: "error",
  cancelled: "default",
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  async function loadData() {
    try {
      setLoading(true);
      const [tasksData, agentsData] = await Promise.all([
        listTasks(),
        listAgents(),
      ]);
      setTasks(tasksData);
      setAgents(agentsData);
    } catch (error) {
      console.error("Failed to load data:", error);
      message.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function handleCreate() {
    form.resetFields();
    setModalVisible(true);
  }

  async function handleDelete(id: string) {
    try {
      await deleteTask(id);
      message.success("Task deleted");
      loadData();
    } catch (error) {
      console.error("Failed to delete task:", error);
      message.error("Failed to delete task");
    }
  }

  async function handleSubmit(values: TaskCreateRequest) {
    try {
      await createTask(values);
      message.success("Task created");
      setModalVisible(false);
      loadData();
    } catch (error) {
      console.error("Failed to create task:", error);
      message.error("Failed to create task");
    }
  }

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, task: Task) => (
        <Link href={`/tasks/${task.id}`}>{name}</Link>
      ),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status: TaskStatus) => (
        <Tag color={statusColors[status]}>{status}</Tag>
      ),
    },
    {
      title: "Agent",
      key: "agent",
      render: (_: unknown, task: Task) => {
        const agent = agents.find((a) => a.id === task.agentId);
        return agent?.name || task.agentId;
      },
    },
    {
      title: "Input",
      dataIndex: "input",
      key: "input",
      ellipsis: true,
      render: (input: string) => input || "-",
    },
    {
      title: "Created",
      dataIndex: "createdAt",
      key: "createdAt",
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, task: Task) => (
        <Space>
          <Link href={`/tasks/${task.id}`}>
            <Button icon={<PlayCircleOutlined />}>Open</Button>
          </Link>
          <Popconfirm
            title="Delete task?"
            onConfirm={() => handleDelete(task.id)}
          >
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between" }}>
        <Title level={2}>Tasks</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          New Task
        </Button>
      </div>

      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="New Task"
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => setModalVisible(false)}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: "Please enter a name" }]}
          >
            <Input placeholder="my-task" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Optional description" />
          </Form.Item>

          <Form.Item
            name="agentId"
            label="Agent"
            rules={[{ required: true, message: "Please select an agent" }]}
          >
            <Select placeholder="Select an agent">
              {agents.map((agent) => (
                <Option key={agent.id} value={agent.id}>
                  {agent.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="input" label="Initial Input">
            <TextArea rows={4} placeholder="Optional initial message" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
