/** Bots Management Page
 *
 * CRUD interface for Bot resources
 */

"use client";

import React, { useState } from "react";
import { Typography, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { ResourceList, ResourceForm, ResourceFormData } from "@/components/resources";
import { useResources } from "@/hooks/useResources";
import { botApi } from "@/services/resources";
import type { BotResponse, BotCreateRequest } from "@/types";

const { Text } = Typography;

interface BotListItem {
  id: string;
  name: string;
  namespace: string;
  kind: string;
  ghost: string;
  model: string;
  shell: string;
  description: string;
}

export default function BotsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingBot, setEditingBot] = useState<BotResponse | null>(null);

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
  } = useResources<BotResponse>({
    listFn: botApi.list,
    createFn: botApi.create,
    updateFn: botApi.update,
    deleteFn: botApi.delete,
  });

  const botListItems: BotListItem[] = resources.map((bot) => ({
    id: bot.id,
    name: bot.metadata.name,
    namespace: bot.metadata.namespace,
    kind: "Bot",
    ghost: bot.spec.ghostRef?.name || "-",
    model: bot.spec.modelRef?.name || "-",
    shell: bot.spec.shellRef?.name || "-",
    description: bot.spec.description || "-",
  }));

  const columns: ColumnsType<BotListItem> = [
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
      title: "Ghost",
      dataIndex: "ghost",
      key: "ghost",
      render: (text) => <Tag color="purple">{text}</Tag>,
    },
    {
      title: "Model",
      dataIndex: "model",
      key: "model",
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: "Shell",
      dataIndex: "shell",
      key: "shell",
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
    setEditingBot(null);
    setFormOpen(true);
  };

  const handleEdit = (item: BotListItem) => {
    const bot = resources.find((b) => b.metadata.name === item.name);
    if (bot) {
      setEditingBot(bot);
      setFormOpen(true);
    }
  };

  const handleDelete = async (item: BotListItem) => {
    await deleteResource(item.name, item.namespace);
  };

  const handleSubmit = async (values: ResourceFormData) => {
    const data: BotCreateRequest = {
      metadata: values.metadata,
      spec: values.spec as unknown as BotCreateRequest["spec"],
    };
    if (editingBot) {
      await updateResource(
        editingBot.metadata.name,
        data,
        editingBot.metadata.namespace
      );
    } else {
      await createResource(data);
    }
    setFormOpen(false);
    await fetchResources();
  };

  const formInitialData: ResourceFormData | undefined = editingBot
    ? {
        metadata: {
          name: editingBot.metadata.name,
          namespace: editingBot.metadata.namespace,
          description: editingBot.spec.description,
        },
        spec: editingBot.spec as unknown as Record<string, unknown>,
      }
    : undefined;

  return (
    <div>
      <ResourceList<BotListItem>
        title="Bots"
        resources={botListItems}
        loading={loading}
        total={total}
        currentNamespace={currentNamespace}
        namespaces={namespaces}
        columns={columns}
        onCreate={handleCreate}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onNamespaceChange={setCurrentNamespace}
        createButtonText="Create Bot"
      />

      <ResourceForm
        title={editingBot ? "Edit Bot" : "Create Bot"}
        open={formOpen}
        resource={formInitialData}
        namespaces={namespaces}
        onSubmit={handleSubmit}
        onCancel={() => setFormOpen(false)}
      />
    </div>
  );
}
