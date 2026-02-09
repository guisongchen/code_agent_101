/** Dashboard Layout
 *
 * Layout with sidebar navigation and header for authenticated pages
 */

"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Space,
  Typography,
  theme,
} from "antd";
import {
  DashboardOutlined,
  RobotOutlined,
  CodeOutlined,
  CloudOutlined,
  TeamOutlined,
  ToolOutlined,
  FileTextOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  CheckSquareOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import { useAuth, ProtectedRoute } from "@/context/auth-context";

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

// =============================================================================
// Navigation Items
// =============================================================================

const navigationItems = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: <Link href="/">Dashboard</Link>,
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
    key: "/ghosts",
    icon: <FileTextOutlined />,
    label: <Link href="/ghosts">Ghosts</Link>,
  },
  {
    key: "/models",
    icon: <CloudOutlined />,
    label: <Link href="/models">Models</Link>,
  },
  {
    key: "/shells",
    icon: <CodeOutlined />,
    label: <Link href="/shells">Shells</Link>,
  },
  {
    key: "/bots",
    icon: <RobotOutlined />,
    label: <Link href="/bots">Bots</Link>,
  },
  {
    key: "/teams",
    icon: <TeamOutlined />,
    label: <Link href="/teams">Teams</Link>,
  },
  {
    key: "/skills",
    icon: <ToolOutlined />,
    label: <Link href="/skills">Skills</Link>,
  },
];

// =============================================================================
// Dashboard Layout Component
// =============================================================================

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // User dropdown menu items
  const userMenuItems = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "Profile",
    },
    {
      key: "settings",
      icon: <SettingOutlined />,
      label: "Settings",
    },
    {
      type: "divider" as const,
    },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "Logout",
      danger: true,
    },
  ];

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === "logout") {
      logout();
    }
  };

  return (
    <ProtectedRoute>
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
            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
              arrow
            >
              <Space style={{ cursor: "pointer" }}>
                <Avatar icon={<UserOutlined />} />
                <Text>{user?.username || "User"}</Text>
              </Space>
            </Dropdown>
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
    </ProtectedRoute>
  );
}
