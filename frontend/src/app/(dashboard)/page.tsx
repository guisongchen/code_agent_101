/** Simplified Dashboard Home Page
 *
 * Simple overview of agents and tasks
 */

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Row, Col, Card, Statistic, Typography, Button, Space, Tag, List, Empty } from "antd";
import { RobotOutlined, CheckSquareOutlined, PlusOutlined, ArrowRightOutlined } from "@ant-design/icons";
import type { Agent, Task, TaskStatus } from "@/types";
import { listAgents } from "@/services/agents";
import { listTasks } from "@/services/tasks";

const { Title, Text } = Typography;

const statusColors: Record<TaskStatus, string> = {
  pending: "default",
  running: "processing",
  paused: "warning",
  completed: "success",
  failed: "error",
  cancelled: "default",
};

export default function DashboardPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [agentsData, tasksData] = await Promise.all([
          listAgents(),
          listTasks(),
        ]);
        setAgents(agentsData);
        setTasks(tasksData);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div>
      {/* Welcome Section */}
      <div style={{ marginBottom: 32 }}>
        <Title level={2}>Dashboard</Title>
        <Text type="secondary">
          Manage your AI agents and tasks
        </Text>
      </div>

      {/* Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={24} sm={12}>
          <Card>
            <Space direction="vertical" size="small" style={{ width: "100%" }}>
              <Space style={{ justifyContent: "space-between", width: "100%" }}>
                <Text strong style={{ fontSize: 16 }}>
                  Agents
                </Text>
                <RobotOutlined style={{ fontSize: 24, color: "#1890ff" }} />
              </Space>
              <Statistic
                value={agents.length}
                valueStyle={{ fontSize: 32, fontWeight: "bold", color: "#1890ff" }}
              />
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card>
            <Space direction="vertical" size="small" style={{ width: "100%" }}>
              <Space style={{ justifyContent: "space-between", width: "100%" }}>
                <Text strong style={{ fontSize: 16 }}>
                  Tasks
                </Text>
                <CheckSquareOutlined style={{ fontSize: 24, color: "#52c41a" }} />
              </Space>
              <Statistic
                value={tasks.length}
                valueStyle={{ fontSize: 32, fontWeight: "bold", color: "#52c41a" }}
              />
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Title level={4} style={{ marginBottom: 16 }}>
        Quick Actions
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={12} sm={6}>
          <Link href="/agents/new" style={{ textDecoration: "none" }}>
            <Button type="dashed" icon={<PlusOutlined />} size="large" block style={{ height: 60 }}>
              New Agent
            </Button>
          </Link>
        </Col>
        <Col xs={12} sm={6}>
          <Link href="/tasks/new" style={{ textDecoration: "none" }}>
            <Button type="dashed" icon={<PlusOutlined />} size="large" block style={{ height: 60 }}>
              New Task
            </Button>
          </Link>
        </Col>
        <Col xs={12} sm={6}>
          <Link href="/chat" style={{ textDecoration: "none" }}>
            <Button type="dashed" icon={<ArrowRightOutlined />} size="large" block style={{ height: 60 }}>
              Open Chat
            </Button>
          </Link>
        </Col>
      </Row>

      {/* Recent Tasks */}
      <Card
        title="Recent Tasks"
        extra={
          <Link href="/tasks">
            <Button type="link" icon={<ArrowRightOutlined />}>
              View All
            </Button>
          </Link>
        }
        loading={loading}
      >
        {tasks.length === 0 ? (
          <Empty description="No tasks yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <List
            dataSource={tasks.slice(0, 5)}
            renderItem={(task) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space>
                      <Link href={`/tasks/${task.id}`}>{task.name}</Link>
                      <Tag color={statusColors[task.status]}>{task.status}</Tag>
                    </Space>
                  }
                  description={
                    task.input && (
                      <Text type="secondary" ellipsis style={{ maxWidth: 300 }}>
                        {task.input}
                      </Text>
                    )
                  }
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {new Date(task.createdAt).toLocaleDateString()}
                </Text>
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
}
