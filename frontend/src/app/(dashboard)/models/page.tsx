/** Models Management Page
 *
 * CRUD interface for Model resources
 */

"use client";

import React, { useState } from "react";
import { Typography, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { ResourceList, ResourceForm, ResourceFormData } from "@/components/resources";
import { useResources } from "@/hooks/useResources";
import { modelApi } from "@/services/resources";
import type { ModelResponse, ModelCreateRequest } from "@/types";

const { Text } = Typography;

interface ModelListItem {
  id: string;
  name: string;
  namespace: string;
  kind: string;
  provider: string;
  modelName: string;
  description: string;
}

export default function ModelsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelResponse | null>(null);

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
  } = useResources<ModelResponse>({
    listFn: modelApi.list,
    createFn: modelApi.create,
    updateFn: modelApi.update,
    deleteFn: modelApi.delete,
  });

  const modelListItems: ModelListItem[] = resources.map((model) => ({
    id: model.id,
    name: model.metadata.name,
    namespace: model.metadata.namespace,
    kind: "Model",
    provider: model.spec.config?.provider || "-",
    modelName: model.spec.config?.modelName || "-",
    description: model.spec.description || "-",
  }));

  const columns: ColumnsType<ModelListItem> = [
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
      title: "Provider",
      dataIndex: "provider",
      key: "provider",
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: "Model",
      dataIndex: "modelName",
      key: "modelName",
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
  ];

  const handleCreate = () => {
    setEditingModel(null);
    setFormOpen(true);
  };

  const handleEdit = (item: ModelListItem) => {
    const model = resources.find((m) => m.metadata.name === item.name);
    if (model) {
      setEditingModel(model);
      setFormOpen(true);
    }
  };

  const handleDelete = async (item: ModelListItem) => {
    await deleteResource(item.name, item.namespace);
  };

  const handleSubmit = async (values: ResourceFormData) => {
    const data: ModelCreateRequest = {
      metadata: values.metadata,
      spec: values.spec as unknown as ModelCreateRequest["spec"],
    };
    if (editingModel) {
      await updateResource(
        editingModel.metadata.name,
        data,
        editingModel.metadata.namespace
      );
    } else {
      await createResource(data);
    }
    setFormOpen(false);
    await fetchResources();
  };

  const formInitialData: ResourceFormData | undefined = editingModel
    ? {
        metadata: {
          name: editingModel.metadata.name,
          namespace: editingModel.metadata.namespace,
          description: editingModel.spec.description,
        },
        spec: editingModel.spec as unknown as Record<string, unknown>,
      }
    : undefined;

  return (
    <div>
      <ResourceList<ModelListItem>
        title="Models"
        resources={modelListItems}
        loading={loading}
        total={total}
        currentNamespace={currentNamespace}
        namespaces={namespaces}
        columns={columns}
        onCreate={handleCreate}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onNamespaceChange={setCurrentNamespace}
        createButtonText="Create Model"
      />

      <ResourceForm
        title={editingModel ? "Edit Model" : "Create Model"}
        open={formOpen}
        resource={formInitialData}
        namespaces={namespaces}
        onSubmit={handleSubmit}
        onCancel={() => setFormOpen(false)}
      />
    </div>
  );
}
