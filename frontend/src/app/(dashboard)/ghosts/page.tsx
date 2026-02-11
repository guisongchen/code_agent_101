/** Ghosts Management Page
 *
 * CRUD interface for Ghost resources
 */

"use client";

import React, { useState } from "react";
import { Typography, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { ResourceList, ResourceForm, ResourceFormData } from "@/components/resources";
import { useResources } from "@/hooks/useResources";
import { ghostApi } from "@/services/resources";
import type { GhostResponse, GhostCreateRequest } from "@/types";

const { Text } = Typography;

interface GhostListItem {
  id: string;
  name: string;
  namespace: string;
  kind: string;
  description: string;
  createdAt: string;
}

export default function GhostsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingGhost, setEditingGhost] = useState<GhostResponse | null>(null);

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
  } = useResources<GhostResponse>({
    listFn: ghostApi.list,
    createFn: ghostApi.create,
    updateFn: ghostApi.update,
    deleteFn: ghostApi.delete,
  });

  const ghostListItems: GhostListItem[] = resources.map((ghost) => ({
    id: ghost.id,
    name: ghost.metadata.name,
    namespace: ghost.metadata.namespace,
    kind: "Ghost",
    description: ghost.spec.description || "-",
    createdAt: ghost.metadata.createdAt || "-",
  }));

  const columns: ColumnsType<GhostListItem> = [
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
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
    {
      title: "Created",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 180,
    },
  ];

  const handleCreate = () => {
    setEditingGhost(null);
    setFormOpen(true);
  };

  const handleEdit = (item: GhostListItem) => {
    const ghost = resources.find((g) => g.metadata.name === item.name);
    if (ghost) {
      setEditingGhost(ghost);
      setFormOpen(true);
    }
  };

  const handleDelete = async (item: GhostListItem) => {
    await deleteResource(item.name, item.namespace);
  };

  const handleSubmit = async (values: ResourceFormData) => {
    const data: GhostCreateRequest = {
      metadata: values.metadata,
      spec: values.spec as unknown as GhostCreateRequest["spec"],
    };
    if (editingGhost) {
      await updateResource(
        editingGhost.metadata.name,
        data,
        editingGhost.metadata.namespace
      );
    } else {
      await createResource(data);
    }
    setFormOpen(false);
    await fetchResources();
  };

  const formInitialData: ResourceFormData | undefined = editingGhost
    ? {
        metadata: {
          name: editingGhost.metadata.name,
          namespace: editingGhost.metadata.namespace,
          description: editingGhost.spec.description,
        },
        spec: editingGhost.spec as unknown as Record<string, unknown>,
      }
    : undefined;

  return (
    <div>
      <ResourceList<GhostListItem>
        title="Ghosts"
        resources={ghostListItems}
        loading={loading}
        total={total}
        currentNamespace={currentNamespace}
        namespaces={namespaces}
        columns={columns}
        onCreate={handleCreate}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onNamespaceChange={setCurrentNamespace}
        createButtonText="Create Ghost"
      />

      <ResourceForm
        title={editingGhost ? "Edit Ghost" : "Create Ghost"}
        open={formOpen}
        resource={formInitialData}
        namespaces={namespaces}
        onSubmit={handleSubmit}
        onCancel={() => setFormOpen(false)}
      />
    </div>
  );
}
