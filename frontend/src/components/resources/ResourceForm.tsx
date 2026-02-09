/** Resource Form Component
 *
 * Reusable form component for creating/editing CRD resources
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  Space,
  Tabs,
  message,
} from "antd";
import { SaveOutlined, CodeOutlined, FileTextOutlined } from "@ant-design/icons";

const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

export interface ResourceFormData {
  metadata: {
    name: string;
    namespace: string;
    description?: string;
  };
  spec: Record<string, unknown>;
}

interface ResourceFormProps {
  title: string;
  open: boolean;
  resource?: ResourceFormData | null;
  namespaces: string[];
  onSubmit: (values: ResourceFormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  specFields?: React.ReactNode;
}

export function ResourceForm({
  title,
  open,
  resource,
  namespaces,
  onSubmit,
  onCancel,
  loading = false,
  specFields,
}: ResourceFormProps) {
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState("basic");
  const [yamlValue, setYamlValue] = useState("");
  const isEditing = !!resource;

  useEffect(() => {
    if (open) {
      if (resource) {
        form.setFieldsValue({
          metadata: resource.metadata,
          spec: resource.spec,
        });
        // Convert spec to YAML-like format for display
        setYamlValue(JSON.stringify(resource.spec, null, 2));
      } else {
        form.resetFields();
        form.setFieldsValue({
          metadata: { namespace: "default" },
          spec: {},
        });
        setYamlValue("{}");
      }
    }
  }, [open, resource, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await onSubmit(values as ResourceFormData);
      message.success(
        isEditing ? "Resource updated successfully" : "Resource created successfully"
      );
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message);
      }
    }
  };

  const handleYamlChange = (value: string) => {
    setYamlValue(value);
    try {
      const parsed = JSON.parse(value);
      form.setFieldValue("spec", parsed);
    } catch {
      // Invalid JSON, don't update form
    }
  };

  return (
    <Modal
      title={title}
      open={open}
      onCancel={onCancel}
      width={800}
      footer={null}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          metadata: { namespace: "default" },
          spec: {},
        }}
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <FileTextOutlined />
                Basic Info
              </span>
            }
            key="basic"
          >
            <Form.Item
              name={["metadata", "name"]}
              label="Name"
              rules={[
                { required: true, message: "Please enter resource name" },
                {
                  pattern: /^[a-z0-9-]+$/,
                  message:
                    "Name must contain only lowercase letters, numbers, and hyphens",
                },
              ]}
            >
              <Input
                placeholder="e.g., my-resource"
                disabled={isEditing}
              />
            </Form.Item>

            <Form.Item
              name={["metadata", "namespace"]}
              label="Namespace"
              rules={[{ required: true, message: "Please select namespace" }]}
            >
              <Select placeholder="Select namespace">
                {namespaces.map((ns) => (
                  <Option key={ns} value={ns}>
                    {ns}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name={["metadata", "description"]} label="Description">
              <TextArea
                rows={3}
                placeholder="Optional description..."
              />
            </Form.Item>
          </TabPane>

          <TabPane
            tab={
              <span>
                <CodeOutlined />
                Spec
              </span>
            }
            key="spec"
          >
            {specFields || (
              <Form.Item name="spec" label="Spec (JSON)">
                <TextArea
                  rows={15}
                  value={yamlValue}
                  onChange={(e) => handleYamlChange(e.target.value)}
                  placeholder="Enter resource spec as JSON..."
                  style={{ fontFamily: "monospace" }}
                />
              </Form.Item>
            )}
          </TabPane>
        </Tabs>

        <Form.Item style={{ marginBottom: 0, textAlign: "right" }}>
          <Space>
            <Button onClick={onCancel}>Cancel</Button>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
            >
              {isEditing ? "Update" : "Create"}
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
