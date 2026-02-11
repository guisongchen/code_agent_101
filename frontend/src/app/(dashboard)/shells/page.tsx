/** Shells Management Page
 *
 * CRUD interface for Shell resources
 */

"use client";

import React, { useState } from "react";
import { Typography, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { ResourceList, ResourceForm, ResourceFormData } from "@/components/resources";
import { useResources } from "@/hooks/useResources";
import { shellApi } from "@/services/resources";
import type { ShellResponse, ShellCreateRequest } from "@/types";

const { Text } = Typography;

interface ShellListItem {
  id: string;
  name: string;
  namespace: string;
  kind: string;
  type: string;
  image: string;
  description: string;
}

export default function ShellsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingShell, setEditingShell] = useState<ShellResponse | null>(null);

  const {
    resources,
    loading,
    total,
    currentNamespace,
    namespaces,
    fetchResources,
    createResource,
    updateResource,
    deleteResource,
    setCurrentNamespace,
  } = useResources<ShellResponse>({
    listFn: shellApi.list,
    createFn: shellApi.create,
    updateFn: shellApi.update,
    deleteFn: shellApi.delete,
  });

  const shellListItems: ShellListItem[] = resources.map((shell) => ({
    id: shell.id,
    name: shell.metadata.name,
    namespace: shell.metadata.namespace,
    kind: "Shell",
    type: shell.spec.type || "chat",
    image: shell.spec.image || "default",
    description: shell.spec.description || "-",
  }));

  const columns: ColumnsType<ShellListItem> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: "Namespace",
      dataIndex: "namespace",
      key: "namespace",
      render: (text) => <Tag>{text}</Tag>,
    },
    {
      title: "Type",
      dataIndex: "type",
      key: "type",
      render: (text) => <Tag color="green">{text}</Tag>,
    },
    {
      title: "Image",
      dataIndex: "image",
      key: "image",
      ellipsis: true,
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
  ];

  const handleCreate = () => {
    setEditingShell(null);
    setFormOpen(true);
  };

  const handleEdit = (item: ShellListItem) => {
    const shell = resources.find((s) => s.metadata.name === item.name);
    if (shell) {
      setEditingShell(shell);
      setFormOpen(true);
    }
  };

  const handleDelete = async (item: ShellListItem) => {
    await deleteResource(item.name, item.namespace);
  };

  const handleSubmit = async (values: ResourceFormData) => {
    const data: ShellCreateRequest = {
      metadata: values.metadata,
      spec: values.spec as unknown as ShellCreateRequest["spec"],
    };
    if (editingShell) {
      await updateResource(
        editingShell.metadata.name,
        data,
        editingShell.metadata.namespace
      );
    } else {
      await createResource(data);
    }
    setFormOpen(false);
    await fetchResources();
  };

  const formInitialData: ResourceFormData | undefined = editingShell
    ? {
        metadata: {
          name: editingShell.metadata.name,
          namespace: editingShell.metadata.namespace,
          description: editingShell.spec.description,
        },
        spec: editingShell.spec as unknown as Record<string, unknown>,
      }
    : undefined;

  return (
    <div>
      <ResourceList<ShellListItem>
        title="Shells"
        resources={shellListItems}
        loading={loading}
        total={total}
        currentNamespace={currentNamespace}
        namespaces={namespaces}
        columns={columns}
        onCreate={handleCreate}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onNamespaceChange={setCurrentNamespace}
        createButtonText="Create Shell"
      />

      <ResourceForm
        title={editingShell ? "Edit Shell" : "Create Shell"}
        open={formOpen}
        resource={formInitialData}
        namespaces={namespaces}
        onSubmit={handleSubmit}
        onCancel={() => setFormOpen(false)}
      />
    </div>
  );
}
