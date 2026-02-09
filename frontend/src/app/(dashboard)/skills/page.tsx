/** Skills Management Page
 *
 * CRUD interface for Skill resources
 */

"use client";

import React, { useState } from "react";
import { Typography, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { ResourceList, ResourceForm, ResourceFormData } from "@/components/resources";
import { useResources } from "@/hooks/useResources";
import { skillApi } from "@/services/resources";
import type { SkillResponse } from "@/types";

const { Text } = Typography;

interface SkillListItem {
  id: string;
  name: string;
  namespace: string;
  version: string;
  author: string;
  tools: number;
  description: string;
}

export default function SkillsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState<SkillResponse | null>(null);

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
  } = useResources<SkillResponse>({
    listFn: skillApi.list,
    createFn: skillApi.create,
    updateFn: skillApi.update,
    deleteFn: skillApi.delete,
  });

  const skillListItems: SkillListItem[] = resources.map((skill) => ({
    id: skill.id,
    name: skill.metadata.name,
    namespace: skill.metadata.namespace,
    version: skill.spec.version || "-",
    author: skill.spec.author || "-",
    tools: skill.spec.tools?.length || 0,
    description: skill.spec.description || "-",
  }));

  const columns: ColumnsType<SkillListItem> = [
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
      title: "Version",
      dataIndex: "version",
      key: "version",
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: "Author",
      dataIndex: "author",
      key: "author",
    },
    {
      title: "Tools",
      dataIndex: "tools",
      key: "tools",
      render: (count) => <Tag color="green">{count} tools</Tag>,
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
  ];

  const handleCreate = () => {
    setEditingSkill(null);
    setFormOpen(true);
  };

  const handleEdit = (item: SkillListItem) => {
    const skill = resources.find((s) => s.metadata.name === item.name);
    if (skill) {
      setEditingSkill(skill);
      setFormOpen(true);
    }
  };

  const handleDelete = async (item: SkillListItem) => {
    await deleteResource(item.name, item.namespace);
  };

  const handleSubmit = async (values: ResourceFormData) => {
    if (editingSkill) {
      await updateResource(
        editingSkill.metadata.name,
        {
          metadata: values.metadata,
          spec: values.spec,
        },
        editingSkill.metadata.namespace
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

  const formInitialData: ResourceFormData | undefined = editingSkill
    ? {
        metadata: {
          name: editingSkill.metadata.name,
          namespace: editingSkill.metadata.namespace,
          description: editingSkill.spec.description,
        },
        spec: editingSkill.spec,
      }
    : undefined;

  return (
    <div>
      <ResourceList<SkillListItem>
        title="Skills"
        resources={skillListItems}
        loading={loading}
        total={total}
        currentNamespace={currentNamespace}
        namespaces={namespaces}
        columns={columns}
        onCreate={handleCreate}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onNamespaceChange={setCurrentNamespace}
        createButtonText="Create Skill"
      />

      <ResourceForm
        title={editingSkill ? "Edit Skill" : "Create Skill"}
        open={formOpen}
        resource={formInitialData}
        namespaces={namespaces}
        onSubmit={handleSubmit}
        onCancel={() => setFormOpen(false)}
      />
    </div>
  );
}
