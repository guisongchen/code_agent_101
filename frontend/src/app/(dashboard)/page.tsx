/** Dashboard Home Page
 *
 * Main dashboard with resource statistics and recent activity
 */

"use client";

import React from "react";
import Link from "next/link";
import {
  Row,
  Col,
  Card,
  Statistic,
  Typography,
  Button,
  Space,
  Tag,
  Timeline,
  List,
  Empty,
} from "antd";
import {
  FileTextOutlined,
  CloudOutlined,
  CodeOutlined,
  RobotOutlined,
  TeamOutlined,
  ToolOutlined,
  CheckSquareOutlined,
  MessageOutlined,
  PlusOutlined,
  ArrowRightOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import { useResources } from "@/hooks/useResources";
import { useTasks } from "@/hooks/useTasks";
import {
  ghostApi,
  modelApi,
  shellApi,
  botApi,
  teamApi,
  skillApi,
} from "@/services/resources";
import type { TaskStatus } from "@/types";

const { Title, Text } = Typography;

// Resource card configuration
const resourceCards = [
  {
    key: "ghosts",
    title: "Ghosts",
    icon: <FileTextOutlined style={{ fontSize: 24, color: "#1890ff" }} />,
    color: "#1890ff",
    link: "/ghosts",
  },
  {
    key: "models",
    title: "Models",
    icon: <CloudOutlined style={{ fontSize: 24, color: "#52c41a" }} />,
    color: "#52c41a",
    link: "/models",
  },
  {
    key: "shells",
    title: "Shells",
    icon: <CodeOutlined style={{ fontSize: 24, color: "#722ed1" }} />,
    color: "#722ed1",
    link: "/shells",
  },
  {
    key: "bots",
    title: "Bots",
    icon: <RobotOutlined style={{ fontSize: 24, color: "#fa8c16" }} />,
    color: "#fa8c16",
    link: "/bots",
  },
  {
    key: "teams",
    title: "Teams",
    icon: <TeamOutlined style={{ fontSize: 24, color: "#eb2f96" }} />,
    color: "#eb2f96",
    link: "/teams",
  },
  {
    key: "skills",
    title: "Skills",
    icon: <ToolOutlined style={{ fontSize: 24, color: "#13c2c2" }} />,
    color: "#13c2c2",
    link: "/skills",
  },
];

const statusColors: Record<TaskStatus, string> = {
  pending: "default",
  running: "processing",
  paused: "warning",
  completed: "success",
  failed: "error",
  cancelled: "default",
};

export default function DashboardPage() {
  // Fetch resource counts
  const ghosts = useResources({ listFn: ghostApi.list, createFn: ghostApi.create, updateFn: ghostApi.update, deleteFn: ghostApi.delete });
  const models = useResources({ listFn: modelApi.list, createFn: modelApi.create, updateFn: modelApi.update, deleteFn: modelApi.delete });
  const shells = useResources({ listFn: shellApi.list, createFn: shellApi.create, updateFn: shellApi.update, deleteFn: shellApi.delete });
  const bots = useResources({ listFn: botApi.list, createFn: botApi.create, updateFn: botApi.update, deleteFn: botApi.delete });
  const teams = useResources({ listFn: teamApi.list, createFn: teamApi.create, updateFn: teamApi.update, deleteFn: teamApi.delete });
  const skills = useResources({ listFn: skillApi.list, createFn: skillApi.create, updateFn: skillApi.update, deleteFn: skillApi.delete });

  // Fetch tasks
  const { tasks: recentTasks, loading: tasksLoading } = useTasks();

  // Resource counts
  const resourceCounts = {
    ghosts: ghosts.total,
    models: models.total,
    shells: shells.total,
    bots: bots.total,
    teams: teams.total,
    skills: skills.total,
  };

  // Quick actions
  const quickActions = [
    { label: "Create Task", icon: <CheckSquareOutlined />, link: "/tasks" },
    { label: "Open Chat", icon: <MessageOutlined />, link: "/chat" },
    { label: "New Bot", icon: <RobotOutlined />, link: "/bots" },
    { label: "New Team", icon: <TeamOutlined />, link: "/teams" },
  ];

  return (
    <div>
      {/* Welcome Section */}
      <div style={{ marginBottom: 32 }}>
        <Title level={2}>Dashboard</Title>
        <Text type="secondary">
          Welcome to Wegent - Manage your AI agents, tasks, and conversations
        </Text>
      </div>

      {/* Resource Statistics */}
      <Title level={4} style={{ marginBottom: 16 }}>
        Resources
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {resourceCards.map((card) => (
          <Col xs={24} sm={12} lg={8} xl={4} key={card.key}>
            <Link href={card.link} style={{ textDecoration: "none" }}>
              <Card
                hoverable
                style={{ borderTop: `3px solid ${card.color}` }}
              >
                <Space direction="vertical" size="small" style={{ width: "100%" }}>
                  <Space style={{ justifyContent: "space-between", width: "100%" }}>
                    <Text strong style={{ fontSize: 16 }}>
                      {card.title}
                    </Text>
                    {card.icon}
                  </Space>
                  <Statistic
                    value={resourceCounts[card.key as keyof typeof resourceCounts]}
                    valueStyle={{ fontSize: 32, fontWeight: "bold", color: card.color }}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Total {card.title}
                  </Text>
                </Space>
              </Card>
            </Link>
          </Col>
        ))}
      </Row>

      {/* Quick Actions */}
      <Title level={4} style={{ marginBottom: 16 }}>
        Quick Actions
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {quickActions.map((action) => (
          <Col xs={12} sm={6} key={action.label}>
            <Link href={action.link} style={{ textDecoration: "none" }}>
              <Button
                type="dashed"
                icon={action.icon}
                size="large"
                block
                style={{ height: 60 }}
              >
                {action.label}
              </Button>
            </Link>
          </Col>
        ))}
      </Row>

      {/* Recent Activity */}
      <Row gutter={[16, 16]}>
        {/* Recent Tasks */}
        <Col xs={24} lg={12}>
          <Card
            title="Recent Tasks"
            extra={
              <Link href="/tasks">
                <Button type="link" icon={<ArrowRightOutlined />}>
                  View All
                </Button>
              </Link>
            }
          >
            {recentTasks.length === 0 ? (
              <Empty description="No tasks yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <List
                dataSource={recentTasks.slice(0, 5)}
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
                        <Space>
                          <Text type="secondary">{task.namespace}</Text>
                          {task.input && (
                            <Text type="secondary" ellipsis style={{ maxWidth: 200 }}>
                              {task.input}
                            </Text>
                          )}
                        </Space>
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
        </Col>

        {/* Activity Timeline */}
        <Col xs={24} lg={12}>
          <Card title="Activity Timeline">
            {recentTasks.length === 0 ? (
              <Empty description="No recent activity" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <Timeline
                items={recentTasks.slice(0, 5).map((task) => ({
                  dot: <ClockCircleOutlined style={{ color: "#1890ff" }} />,
                  children: (
                    <div>
                      <Text strong>{task.name}</Text>
                      <div>
                        <Tag color={statusColors[task.status]} size="small">
                          {task.status}
                        </Tag>
                        <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                          {new Date(task.createdAt).toLocaleString()}
                        </Text>
                      </div>
                    </div>
                  ),
                }))}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
