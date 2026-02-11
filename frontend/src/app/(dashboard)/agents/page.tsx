/** Agents Page
 *
 * Simple agent management with inline CRUD
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
  Slider,
  Switch,
  message,
  Popconfirm,
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { Agent, AgentCreateRequest } from "@/types";
import { listAgents, createAgent, updateAgent, deleteAgent } from "@/services/agents";

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const modelProviders = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" },
  { value: "ollama", label: "Ollama" },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [form] = Form.useForm();

  async function loadAgents() {
    try {
      setLoading(true);
      const data = await listAgents();
      setAgents(data);
    } catch (error) {
      console.error("Failed to load agents:", error);
      message.error("Failed to load agents");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAgents();
  }, []);

  function handleCreate() {
    setEditingAgent(null);
    form.resetFields();
    setModalVisible(true);
  }

  function handleEdit(agent: Agent) {
    setEditingAgent(agent);
    form.setFieldsValue({
      name: agent.name,
      description: agent.description,
      modelProvider: agent.modelProvider,
      modelName: agent.modelName,
      apiKey: agent.apiKey,
      systemPrompt: agent.systemPrompt,
      temperature: agent.temperature ?? 0.7,
      autoInvokeTools: agent.autoInvokeTools ?? false,
      maxIterations: agent.maxIterations ?? 10,
    });
    setModalVisible(true);
  }

  async function handleDelete(id: string) {
    try {
      await deleteAgent(id);
      message.success("Agent deleted");
      loadAgents();
    } catch (error) {
      console.error("Failed to delete agent:", error);
      message.error("Failed to delete agent");
    }
  }

  async function handleSubmit(values: AgentCreateRequest) {
    try {
      if (editingAgent) {
        await updateAgent(editingAgent.id, values);
        message.success("Agent updated");
      } else {
        await createAgent(values);
        message.success("Agent created");
      }
      setModalVisible(false);
      loadAgents();
    } catch (error) {
      console.error("Failed to save agent:", error);
      message.error("Failed to save agent");
    }
  }

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string, agent: Agent) => (
        <Link href={`/agents/${agent.id}`}>{name}</Link>
      ),
    },
    {
      title: "Model",
      key: "model",
      render: (_: unknown, agent: Agent) => `${agent.modelProvider} / ${agent.modelName}`,
    },
    {
      title: "Temperature",
      dataIndex: "temperature",
      key: "temperature",
      render: (temp: number) => temp?.toFixed(1) ?? "0.7",
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
      render: (_: unknown, agent: Agent) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => handleEdit(agent)} />
          <Popconfirm
            title="Delete agent?"
            onConfirm={() => handleDelete(agent.id)}
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
        <Title level={2}>Agents</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          New Agent
        </Button>
      </div>

      <Table
        dataSource={agents}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingAgent ? "Edit Agent" : "New Agent"}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            modelProvider: "openai",
            modelName: "gpt-4",
            temperature: 0.7,
            autoInvokeTools: false,
            maxIterations: 10,
            systemPrompt: "You are a helpful AI assistant.",
          }}
        >
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: "Please enter a name" }]}
          >
            <Input placeholder="my-agent" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Optional description" />
          </Form.Item>

          <Form.Item
            name="modelProvider"
            label="Provider"
            rules={[{ required: true }]}
          >
            <Select>
              {modelProviders.map((p) => (
                <Option key={p.value} value={p.value}>
                  {p.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="modelName"
            label="Model"
            rules={[{ required: true, message: "Please enter a model name" }]}
          >
            <Input placeholder="gpt-4, claude-3-opus, etc." />
          </Form.Item>

          <Form.Item name="apiKey" label="API Key">
            <Input.Password placeholder="Optional - uses default if not set" />
          </Form.Item>

          <Form.Item
            name="systemPrompt"
            label="System Prompt"
            rules={[{ required: true }]}
          >
            <TextArea rows={4} />
          </Form.Item>

          <Form.Item name="temperature" label="Temperature">
            <Slider min={0} max={2} step={0.1} />
          </Form.Item>

          <Form.Item name="autoInvokeTools" valuePropName="checked">
            <Switch checkedChildren="Auto Tools" unCheckedChildren="Manual Tools" />
          </Form.Item>

          <Form.Item name="maxIterations" label="Max Iterations">
            <Input type="number" min={1} max={50} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
