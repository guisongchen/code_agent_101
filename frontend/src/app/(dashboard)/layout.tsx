/** Simplified Dashboard Layout
 *
 * No authentication, simpler navigation
 */

"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Layout, Menu, Typography, theme } from "antd";
import {
  DashboardOutlined,
  RobotOutlined,
  TeamOutlined,
  CheckSquareOutlined,
  MessageOutlined,
} from "@ant-design/icons";

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const navigationItems = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: <Link href="/">Dashboard</Link>,
  },
  {
    key: "/agents",
    icon: <RobotOutlined />,
    label: <Link href="/agents">Agents</Link>,
  },
  {
    key: "/tasks",
    icon: <CheckSquareOutlined />,
    label: <Link href="/tasks">Tasks</Link>,
  },
  {
    key: "/chat",
    icon: <MessageOutlined />,
    label: <Link href="/chat">Chat</Link>,
  },
  {
    key: "/teams",
    icon: <TeamOutlined />,
    label: <Link href="/teams">Teams</Link>,
  },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        theme="light"
        breakpoint="lg"
        collapsedWidth="80"
        style={{
          boxShadow: "2px 0 8px rgba(0,0,0,0.06)",
          zIndex: 10,
        }}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          <Text strong style={{ fontSize: 18, color: "#1890ff" }}>
            Wegent
          </Text>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={navigationItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: colorBgContainer,
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
            zIndex: 9,
          }}
        >
          <Text type="secondary">Personal Mode</Text>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            minHeight: 280,
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
