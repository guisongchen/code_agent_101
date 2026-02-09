/** Task Create Modal
 *
 * Modal form for creating new tasks with team selection
 */

import React from "react";
import { Modal, Form, Input, Select, Button, Space } from "antd";
import type { TeamResponse } from "@/types";

const { TextArea } = Input;
const { Option } = Select;

interface TaskCreateModalProps {
  open: boolean;
  teams: TeamResponse[];
  namespaces: string[];
  onSubmit: (values: {
    name: string;
    namespace: string;
    teamId?: string;
    input?: string;
  }) => void;
  onCancel: () => void;
}

export function TaskCreateModal({
  open,
  teams,
  namespaces,
  onSubmit,
  onCancel,
}: TaskCreateModalProps) {
  const [form] = Form.useForm();

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      onSubmit(values);
      form.resetFields();
    } catch (error) {
      // Validation failed
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="Create New Task"
      open={open}
      onCancel={handleCancel}
      footer={
        <Space>
          <Button onClick={handleCancel}>Cancel</Button>
          <Button type="primary" onClick={handleSubmit}>
            Create Task
          </Button>
        </Space>
      }
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ namespace: "default" }}
      >
        <Form.Item
          name="name"
          label="Task Name"
          rules={[{ required: true, message: "Please enter a task name" }]}
        >
          <Input placeholder="Enter task name" />
        </Form.Item>

        <Form.Item
          name="namespace"
          label="Namespace"
          rules={[{ required: true, message: "Please select a namespace" }]}
        >
          <Select placeholder="Select namespace">
            {namespaces.map((ns) => (
              <Option key={ns} value={ns}>
                {ns}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="teamId" label="Team (Optional)">
          <Select
            placeholder="Select a team"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {teams.map((team) => (
              <Option key={team.id} value={team.id}>
                {team.metadata.name} ({team.metadata.namespace})
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="input" label="Task Input (Optional)">
          <TextArea
            rows={4}
            placeholder="Enter task input or instructions..."
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
