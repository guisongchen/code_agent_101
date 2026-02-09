/** useResources Hook
 *
 * Custom hook for managing CRD resources (list, create, edit, delete)
 */

import { useState, useCallback, useEffect } from "react";
import { message } from "antd";
import type { ResourceListResponse } from "@/types";

interface UseResourcesOptions<T> {
  listFn: (options: { namespace?: string }) => Promise<ResourceListResponse<T>>;
  createFn: (data: unknown) => Promise<T>;
  updateFn: (name: string, data: unknown, namespace?: string) => Promise<T>;
  deleteFn: (name: string, namespace?: string) => Promise<void>;
}

interface UseResourcesReturn<T> {
  resources: T[];
  loading: boolean;
  total: number;
  currentNamespace: string;
  namespaces: string[];
  fetchResources: () => Promise<void>;
  createResource: (data: unknown) => Promise<void>;
  updateResource: (name: string, data: unknown, namespace?: string) => Promise<void>;
  deleteResource: (name: string, namespace?: string) => Promise<void>;
  setCurrentNamespace: (namespace: string) => void;
}

export function useResources<T extends { name: string; namespace: string }>({
  listFn,
  createFn,
  updateFn,
  deleteFn,
}: UseResourcesOptions<T>): UseResourcesReturn<T> {
  const [resources, setResources] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentNamespace, setCurrentNamespace] = useState("");
  const [namespaces, setNamespaces] = useState<string[]>([
    "default",
    "production",
    "staging",
  ]);

  const fetchResources = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listFn({
        namespace: currentNamespace || undefined,
      });
      setResources(response.items);
      setTotal(response.total);

      // Extract unique namespaces from resources
      const uniqueNamespaces = Array.from(
        new Set(response.items.map((r) => r.namespace))
      );
      if (uniqueNamespaces.length > 0) {
        setNamespaces((prev) =
          Array.from(new Set([...prev, ...uniqueNamespaces]))
        );
      }
    } catch (error) {
      message.error("Failed to fetch resources");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [listFn, currentNamespace]);

  const createResource = useCallback(
    async (data: unknown) => {
      try {
        await createFn(data);
        message.success("Resource created successfully");
        await fetchResources();
      } catch (error) {
        message.error("Failed to create resource");
        throw error;
      }
    },
    [createFn, fetchResources]
  );

  const updateResource = useCallback(
    async (name: string, data: unknown, namespace?: string) => {
      try {
        await updateFn(name, data, namespace);
        message.success("Resource updated successfully");
        await fetchResources();
      } catch (error) {
        message.error("Failed to update resource");
        throw error;
      }
    },
    [updateFn, fetchResources]
  );

  const deleteResource = useCallback(
    async (name: string, namespace?: string) => {
      try {
        await deleteFn(name, namespace);
        message.success("Resource deleted successfully");
        await fetchResources();
      } catch (error) {
        message.error("Failed to delete resource");
        throw error;
      }
    },
    [deleteFn, fetchResources]
  );

  useEffect(() => {
    fetchResources();
  }, [fetchResources]);

  return {
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
  };
}
