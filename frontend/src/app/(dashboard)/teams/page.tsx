/** Teams Management Page
 *
 * CRUD interface for Team resources
 */

"use client";

import React, { useState } from "react";
import { Typography, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { ResourceList, ResourceForm, ResourceFormData } from "@/components/resources";
import { useResources } from "@/hooks/useResources";
import { teamApi } from "@/services/resources";
import type { TeamResponse } from "@/types";

const { Text } = Typography;

interface TeamListItem {
  id: string;
  name: string;
  namespace: string;
  members: number;
  strategy: string;
  description: string;
}

export default function TeamsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<TeamResponse | null>(null);

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
  } = useResources<TeamResponse>({
    listFn: teamApi.list,
    createFn: teamApi.create,
    updateFn: teamApi.update,
    deleteFn: teamApi.delete,
  });

  const teamListItems: TeamListItem[] = resources.map((team) => ({
    id: team.id,
    name: team.metadata.name,
    namespace: team.metadata.namespace,
    members: team.spec.members?.length || 0,
    strategy: team.spec.coordinationStrategy || "-",
    description: team.spec.description || "-",
  }));

  const columns: ColumnsType<TeamListItem> = [
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
      title: "Members",
      dataIndex: "members",
      key: "members",
      render: (count) => <Tag color="blue">{count} bots</Tag>,
    },
    {
      title: "Strategy",
      dataIndex: "strategy",
      key: "strategy",
      render: (text) => <Tag color="green">{text}</Tag>,
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
  ];

  const handleCreate = () => {
    setEditingTeam(null);
    setFormOpen(true);
  };

  const handleEdit = (item: TeamListItem) => {
    const team = resources.find((t) => t.metadata.name === item.name);
    if (team) {
      setEditingTeam(team);
      setFormOpen(true);
    }
  };

  const handleDelete = async (item: TeamListItem) => {
    await deleteResource(item.name, item.namespace);
  };

  const handleSubmit = async (values: ResourceFormData) => {
    if (editingTeam) {
      await updateResource(
        editingTeam.metadata.name,
        {
          metadata: values.metadata,
          spec: values.spec,
        },
        editingTeam.metadata.namespace
      );
    } else {
      await createResource({
        metadata: values.metadata,
        spec: values.spec,
      });
    }
    setFormOpen(false);
    await fetchResources();
  };

  const formInitialData: ResourceFormData | undefined = editingTeam
    ? {
        metadata: {
          name: editingTeam.metadata.name,
          namespace: editingTeam.metadata.namespace,
          description: editingTeam.spec.description,
        },
        spec: editingTeam.spec,
      }
    : undefined;

  return (
    <div>
      <ResourceList<TeamListItem>
        title="Teams"
        resources={teamListItems}
        loading={loading}
        total={total}
        currentNamespace={currentNamespace}
        namespaces={namespaces}
        columns={columns}
        onCreate={handleCreate}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onNamespaceChange={setCurrentNamespace}
        createButtonText="Create Team"
      />

      <ResourceForm
        title={editingTeam ? "Edit Team" : "Create Team"}
        open={formOpen}
        resource={formInitialData}
        namespaces={namespaces}
        onSubmit={handleSubmit}
        onCancel={() => setFormOpen(false)}
      />
    </div>
  );
}
