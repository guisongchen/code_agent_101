/** Resource List Component
 *
 * Reusable table component for listing CRD resources
 */

"use client";

import React, { useState, useCallback } from "react";
import {
  Table,
  Button,
  Space,
  Tag,
  Popconfirm,
  Input,
  Select,
  Row,
  Col,
  Typography,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

const { Title } = Typography;
const { Option } = Select;

export interface ResourceListItem {
  id: string;
  name: string;
  namespace: string;
  kind: string;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface ResourceListProps<T extends ResourceListItem> {
  title: string;
  resources: T[];
  loading: boolean;
  total: number;
  currentNamespace: string;
  namespaces: string[];
  columns: ColumnsType<T>;
  onCreate: () => void;
  onEdit: (resource: T) => void;
  onDelete: (resource: T) => Promise<void>;
  onNamespaceChange: (namespace: string) => void;
  onSearch?: (keyword: string) => void;
  createButtonText?: string;
}

export function ResourceList<T extends ResourceListItem>({
  title,
  resources,
  loading,
  total,
  currentNamespace,
  namespaces,
  columns,
  onCreate,
  onEdit,
  onDelete,
  onNamespaceChange,
  onSearch,
  createButtonText = "Create",
}: ResourceListProps<T>) {
  const [searchKeyword, setSearchKeyword] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleSearch = useCallback(() => {
    onSearch?.(searchKeyword);
  }, [onSearch, searchKeyword]);

  const handleDelete = useCallback(
    async (resource: T) => {
      setDeletingId(resource.id);
      try {
        await onDelete(resource);
      } finally {
        setDeletingId(null);
      }
    },
    [onDelete]
  );

  const actionColumn: ColumnsType<T>[number] = {
    title: "Actions",
    key: "actions",
    width: 150,
    render: (_, record) => (
      <Space size="small">
        <Button
          type="text"
          icon={<EditOutlined />}
          onClick={() => onEdit(record)}
          title="Edit"
        />
        <Popconfirm
          title="Delete Resource"
          description={`Are you sure you want to delete "${record.name}"?`}
          onConfirm={() => handleDelete(record)}
          okText="Delete"
          okButtonProps={{ danger: true }}
          cancelText="Cancel"
        >
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            loading={deletingId === record.id}
            title="Delete"
          />
        </Popconfirm>
      </Space>
    ),
  };

  const allColumns = [...columns, actionColumn];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>
            {title}
          </Title>
        </Col>
        <Col>
          <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>
            {createButtonText}
          </Button>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={8}>
          <Input.Search
            placeholder="Search resources..."
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onSearch={handleSearch}
            allowClear
            prefix={<SearchOutlined />}
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Select
            style={{ width: "100%" }}
            value={currentNamespace}
            onChange={onNamespaceChange}
            placeholder="Select namespace"
          >
            <Option value="">All namespaces</Option>
            {namespaces.map((ns) => (
              <Option key={ns} value={ns}>
                {ns}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      <Table<T>
        columns={allColumns}
        dataSource={resources}
        loading={loading}
        rowKey="id"
        pagination={{
          total,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} items`,
        }}
      />
    </div>
  );
}
