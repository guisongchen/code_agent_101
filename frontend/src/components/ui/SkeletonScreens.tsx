/** Skeleton Screen Components
 *
 * Loading skeletons for various UI patterns to improve perceived performance
 * and provide visual feedback during data loading.
 */

import React from "react";
import { Skeleton, Card, Space, Row, Col, Divider } from "antd";

// =============================================================================
// Table/List Skeleton
// =============================================================================

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps) {
  return (
    <Card>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Skeleton.Input active style={{ width: 200 }} />
        <div style={{ float: "right" }}>
          <Skeleton.Button active style={{ width: 120 }} />
        </div>
      </div>

      {/* Table rows */}
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <Row key={rowIndex} gutter={16} align="middle">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Col key={colIndex} span={24 / columns}>
                <Skeleton.Input
                  active
                  style={{ width: colIndex === 0 ? "80%" : "60%" }}
                />
              </Col>
            ))}
          </Row>
        ))}
      </Space>

      {/* Pagination */}
      <div style={{ marginTop: 24, textAlign: "right" }}>
        <Skeleton.Input active style={{ width: 200 }} />
      </div>
    </Card>
  );
}

// =============================================================================
// Card Grid Skeleton
// =============================================================================

interface CardGridSkeletonProps {
  count?: number;
  columns?: number;
}

export function CardGridSkeleton({ count = 6, columns = 3 }: CardGridSkeletonProps) {
  return (
    <Row gutter={[16, 16]}>
      {Array.from({ length: count }).map((_, index) => (
        <Col key={index} span={24 / columns}>
          <Card>
            <Skeleton active paragraph={{ rows: 2 }} />
          </Card>
        </Col>
      ))}
    </Row>
  );
}

// =============================================================================
// Statistics Cards Skeleton
// =============================================================================

interface StatsCardsSkeletonProps {
  count?: number;
}

export function StatsCardsSkeleton({ count = 6 }: StatsCardsSkeletonProps) {
  return (
    <Row gutter={[16, 16]}>
      {Array.from({ length: count }).map((_, index) => (
        <Col key={index} xs={24} sm={12} lg={8} xl={4}>
          <Card>
            <Skeleton active paragraph={{ rows: 1 }} title={{ width: "40%" }} />
            <div style={{ marginTop: 8 }}>
              <Skeleton.Input active style={{ width: "60%" }} size="large" />
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  );
}

// =============================================================================
// Form Skeleton
// =============================================================================

interface FormSkeletonProps {
  fields?: number;
}

export function FormSkeleton({ fields = 6 }: FormSkeletonProps) {
  return (
    <Card>
      <Space direction="vertical" style={{ width: "100%" }} size="large">
        {Array.from({ length: fields }).map((_, index) => (
          <div key={index}>
            <Skeleton.Input
              active
              style={{ width: 120, marginBottom: 8 }}
              size="small"
            />
            <br />
            <Skeleton.Input active style={{ width: "100%" }} />
          </div>
        ))}
        <div style={{ marginTop: 16 }}>
          <Skeleton.Button active size="large" />
          <Skeleton.Button active style={{ marginLeft: 8 }} size="large" />
        </div>
      </Space>
    </Card>
  );
}

// =============================================================================
// Detail View Skeleton
// =============================================================================

export function DetailSkeleton() {
  return (
    <Card>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Skeleton.Input active style={{ width: 300 }} size="large" />
        <div style={{ float: "right" }}>
          <Space>
            <Skeleton.Button active />
            <Skeleton.Button active />
          </Space>
        </div>
      </div>

      <Divider />

      {/* Content */}
      <Row gutter={24}>
        <Col span={16}>
          <Space direction="vertical" style={{ width: "100%" }} size="large">
            <div>
              <Skeleton.Input active style={{ width: 100, marginBottom: 8 }} size="small" />
              <Skeleton active paragraph={{ rows: 3 }} title={false} />
            </div>
            <div>
              <Skeleton.Input active style={{ width: 100, marginBottom: 8 }} size="small" />
              <Skeleton active paragraph={{ rows: 2 }} title={false} />
            </div>
          </Space>
        </Col>
        <Col span={8}>
          <Card size="small" title={<Skeleton.Input active style={{ width: 100 }} />}>
            <Skeleton active paragraph={{ rows: 4 }} title={false} />
          </Card>
        </Col>
      </Row>
    </Card>
  );
}

// =============================================================================
// Chat Skeleton
// =============================================================================

interface ChatSkeletonProps {
  messages?: number;
}

export function ChatSkeleton({ messages = 5 }: ChatSkeletonProps) {
  return (
    <Card style={{ height: "100%" }}>
      {/* Chat header */}
      <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: "1px solid #f0f0f0" }}>
        <Skeleton.Input active style={{ width: 200 }} />
      </div>

      {/* Messages */}
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        {Array.from({ length: messages }).map((_, index) => (
          <div
            key={index}
            style={{
              display: "flex",
              justifyContent: index % 2 === 0 ? "flex-start" : "flex-end",
            }}
          >
            <div
              style={{
                maxWidth: "70%",
                padding: 12,
                borderRadius: 8,
                background: index % 2 === 0 ? "#f5f5f5" : "#1890ff15",
              }}
            >
              <Skeleton.Input
                active
                style={{ width: `${100 + Math.random() * 200}px` }}
              />
            </div>
          </div>
        ))}
      </Space>

      {/* Input area */}
      <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #f0f0f0" }}>
        <Skeleton.Input active style={{ width: "100%" }} />
      </div>
    </Card>
  );
}

// =============================================================================
// Dashboard Skeleton
// =============================================================================

export function DashboardSkeleton() {
  return (
    <Space direction="vertical" style={{ width: "100%" }} size="large">
      {/* Stats row */}
      <StatsCardsSkeleton count={6} />

      {/* Main content */}
      <Row gutter={[16, 16]}>
        <Col span={16}>
          <Card title={<Skeleton.Input active style={{ width: 150 }} />}>
            <Skeleton active paragraph={{ rows: 4 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title={<Skeleton.Input active style={{ width: 150 }} />}>
            <Skeleton active paragraph={{ rows: 4 }} />
          </Card>
        </Col>
      </Row>
    </Space>
  );
}

// =============================================================================
// Generic Content Skeleton
// =============================================================================

interface ContentSkeletonProps {
  rows?: number;
  title?: boolean;
}

export function ContentSkeleton({ rows = 3, title = true }: ContentSkeletonProps) {
  return <Skeleton active paragraph={{ rows }} title={title} />;
}

// =============================================================================
// Page Skeleton (Full page loading state)
// =============================================================================

export function PageSkeleton() {
  return (
    <div style={{ padding: 24 }}>
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <Skeleton.Input active style={{ width: 250 }} size="large" />
        <Skeleton.Input
          active
          style={{ width: 400, marginTop: 8 }}
          size="small"
        />
      </div>

      {/* Page content */}
      <Card>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    </div>
  );
}

export default {
  Table: TableSkeleton,
  CardGrid: CardGridSkeleton,
  StatsCards: StatsCardsSkeleton,
  Form: FormSkeleton,
  Detail: DetailSkeleton,
  Chat: ChatSkeleton,
  Dashboard: DashboardSkeleton,
  Content: ContentSkeleton,
  Page: PageSkeleton,
};
