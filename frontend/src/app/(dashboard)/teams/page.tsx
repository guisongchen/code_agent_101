/** Teams Page
 *
 * Simple team management with inline CRUD
 */

"use client";

import React, { useEffect, useState } from "react";
import {
  Table,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { Team, TeamCreateRequest, Agent } from "@/types";
import { listTeams, createTeam, updateTeam, deleteTeam } from "@/services/teams";
import { listAgents } from "@/services/agents";

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [form] = Form.useForm();

  async function loadData() {
    try {
      setLoading(true);
      const [teamsData, agentsData] = await Promise.all([
        listTeams(),
        listAgents(),
      ]);
      setTeams(teamsData);
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
    setEditingTeam(null);
    form.resetFields();
    setModalVisible(true);
  }

  function handleEdit(team: Team) {
    setEditingTeam(team);
    form.setFieldsValue({
      name: team.name,
      description: team.description,
      agentIds: team.agentIds,
    });
    setModalVisible(true);
  }

  async function handleDelete(id: string) {
    try {
      await deleteTeam(id);
      message.success("Team deleted");
      loadData();
    } catch (error) {
      console.error("Failed to delete team:", error);
      message.error("Failed to delete team");
    }
  }

  async function handleSubmit(values: TeamCreateRequest) {
    try {
      if (editingTeam) {
        await updateTeam(editingTeam.id, values);
        message.success("Team updated");
      } else {
        await createTeam(values);
        message.success("Team created");
      }
      setModalVisible(false);
      loadData();
    } catch (error) {
      console.error("Failed to save team:", error);
      message.error("Failed to save team");
    }
  }

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Agents",
      key: "agents",
      render: (_: unknown, team: Team) => (
        <Space size="small" wrap>
          {team.agentIds.map((id) => {
            const agent = agents.find((a) => a.id === id);
            return (
              <Tag key={id}>{agent?.name || id}</Tag>
            );
          })}
        </Space>
      ),
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
      render: (_: unknown, team: Team) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => handleEdit(team)} />
          <Popconfirm
            title="Delete team?"
            onConfirm={() => handleDelete(team.id)}
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
        <Title level={2}>Teams</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          New Team
        </Button>
      </div>

      <Table
        dataSource={teams}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingTeam ? "Edit Team" : "New Team"}
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
            <Input placeholder="my-team" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Optional description" />
          </Form.Item>

          <Form.Item
            name="agentIds"
            label="Agents"
            rules={[{ required: true, message: "Please select at least one agent" }]}
          >
            <Select mode="multiple" placeholder="Select agents">
              {agents.map((agent) => (
                <Option key={agent.id} value={agent.id}>
                  {agent.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
