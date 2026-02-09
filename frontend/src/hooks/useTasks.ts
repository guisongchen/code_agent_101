/** useTasks Hook
 *
 * Custom hook for managing tasks with real-time updates
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { message } from "antd";
import type { TaskResponse, TaskStatus, TaskCreateRequest } from "@/types";
import { taskApi } from "@/services/tasks";

interface UseTasksOptions {
  namespace?: string;
  status?: TaskStatus;
  teamId?: string;
  enableRealtime?: boolean;
}

interface UseTasksReturn {
  tasks: TaskResponse[];
  loading: boolean;
  total: number;
  currentNamespace: string;
  namespaces: string[];
  statusFilter: TaskStatus | undefined;
  fetchTasks: () => Promise<void>;
  createTask: (data: TaskCreateRequest) => Promise<TaskResponse | undefined>;
  cancelTask: (taskId: string) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  executeTask: (taskId: string, botName?: string) => Promise<TaskResponse | undefined>;
  setCurrentNamespace: (namespace: string) => void;
  setStatusFilter: (status: TaskStatus | undefined) => void;
  isTaskRunning: (taskId: string) => boolean;
}

export function useTasks(options: UseTasksOptions = {}): UseTasksReturn {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentNamespace, setCurrentNamespace] = useState(options.namespace || "");
  const [namespaces, setNamespaces] = useState<string[]>(["default", "production", "staging"]);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | undefined>(options.status);

  // Track running tasks for real-time status
  const runningTasksRef = useRef<Set<string>>(new Set());

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const response = await taskApi.list({
        namespace: currentNamespace || undefined,
        status: statusFilter,
        teamId: options.teamId,
      });
      setTasks(response);
      setTotal(response.length);

      // Extract unique namespaces from tasks
      const uniqueNamespaces = Array.from(
        new Set(response.map((t) => t.namespace))
      );
      if (uniqueNamespaces.length > 0) {
        setNamespaces((prev) =>
          Array.from(new Set([...prev, ...uniqueNamespaces]))
        );
      }

      // Update running tasks tracking
      runningTasksRef.current = new Set(
        response.filter((t) => t.status === "running").map((t) => t.id)
      );
    } catch (error) {
      message.error("Failed to fetch tasks");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [currentNamespace, statusFilter, options.teamId]);

  const createTask = useCallback(
    async (data: TaskCreateRequest): Promise<TaskResponse | undefined> => {
      try {
        const result = await taskApi.create(data);
        message.success("Task created successfully");
        await fetchTasks();
        return result;
      } catch (error) {
        message.error("Failed to create task");
        throw error;
      }
    },
    [fetchTasks]
  );

  const cancelTask = useCallback(
    async (taskId: string) => {
      try {
        await taskApi.cancel(taskId);
        message.success("Task cancelled");
        await fetchTasks();
      } catch (error) {
        message.error("Failed to cancel task");
        throw error;
      }
    },
    [fetchTasks]
  );

  const deleteTask = useCallback(
    async (taskId: string) => {
      try {
        await taskApi.delete(taskId);
        message.success("Task deleted successfully");
        await fetchTasks();
      } catch (error) {
        message.error("Failed to delete task");
        throw error;
      }
    },
    [fetchTasks]
  );

  const executeTask = useCallback(
    async (taskId: string, botName?: string): Promise<TaskResponse | undefined> => {
      try {
        const result = await taskApi.execute(taskId, { botName });
        message.success("Task execution started");
        await fetchTasks();
        return result;
      } catch (error) {
        message.error("Failed to execute task");
        throw error;
      }
    },
    [fetchTasks]
  );

  const isTaskRunning = useCallback((taskId: string): boolean => {
    return runningTasksRef.current.has(taskId);
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Real-time polling for running tasks
  useEffect(() => {
    if (!options.enableRealtime) return;

    const intervalId = setInterval(() => {
      if (runningTasksRef.current.size > 0) {
        fetchTasks();
      }
    }, 3000); // Poll every 3 seconds for running tasks

    return () => clearInterval(intervalId);
  }, [fetchTasks, options.enableRealtime]);

  return {
    tasks,
    loading,
    total,
    currentNamespace,
    namespaces,
    statusFilter,
    fetchTasks,
    createTask,
    cancelTask,
    deleteTask,
    executeTask,
    setCurrentNamespace,
    setStatusFilter,
    isTaskRunning,
  };
}
