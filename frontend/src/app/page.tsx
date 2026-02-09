/** Dashboard Home Page
 *
 * Main dashboard showing overview of resources
 */

"use client";

import React from "react";
import { Card, Row, Col, Statistic, Typography } from "antd";
import {
  FileTextOutlined,
  CloudOutlined,
  CodeOutlined,
  RobotOutlined,
  TeamOutlined,
  ToolOutlined,
} from "@ant-design/icons";

const { Title, Text } = Typography;

export default function DashboardPage() {
  return (
    <div>
      <Title level={2}>Dashboard</Title>
      <Text type="secondary">
        Welcome to Wegent - Manage your AI agents and resources
      </Text>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Ghosts"
              value={0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Models"
              value={0}
              prefix={<CloudOutlined />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Shells"
              value={0}
              prefix={<CodeOutlined />}
              valueStyle={{ color: "#faad14" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Bots"
              value={0}
              prefix={<RobotOutlined />}
              valueStyle={{ color: "#722ed1" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Teams"
              value={0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: "#eb2f96" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Skills"
              value={0}
              prefix={<ToolOutlined />}
              valueStyle={{ color: "#13c2c2" }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
