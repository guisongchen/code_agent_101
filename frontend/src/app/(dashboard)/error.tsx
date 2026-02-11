/** Dashboard Error Page
 *
 * Next.js error.tsx for handling errors in the dashboard route group
 * Provides a more contextual error UI for dashboard-specific errors
 */

"use client";

import { useEffect } from "react";
import { Result, Button, Space, Card, Typography } from "antd";
import {
  ReloadOutlined,
  DashboardOutlined,
  AlertOutlined,
} from "@ant-design/icons";

const { Text, Paragraph } = Typography;

// =============================================================================
// Props
// =============================================================================

interface DashboardErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

// =============================================================================
// Dashboard Error Component
// =============================================================================

export default function DashboardError({ error, reset }: DashboardErrorProps) {
  useEffect(() => {
    // Log the error to console for debugging
    console.error("Dashboard error page caught error:", error);
  }, [error]);

  return (
    <div style={{ padding: "24px" }}>
      <Card>
        <Result
          status="warning"
          icon={<AlertOutlined />}
          title="Dashboard Error"
          subTitle="Something went wrong while loading the dashboard content."
          extra={
            <Space wrap>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={reset}
              >
                Try Again
              </Button>
              <Button
                icon={<DashboardOutlined />}
                href="/"
              >
                Go to Dashboard
              </Button>
            </Space>
          }
        >
          <div style={{ textAlign: "left", maxWidth: 600, margin: "0 auto" }}>
            <Paragraph>
              <Text strong>Error Message:</Text>
              <br />
              <Text type="danger">{error.message || "Unknown error"}</Text>
            </Paragraph>
            {error.digest && (
              <Paragraph>
                <Text type="secondary">Error ID: {error.digest}</Text>
              </Paragraph>
            )}
            <Paragraph type="secondary">
              If this problem persists, please try refreshing the page or
              contact support.
            </Paragraph>
          </div>
        </Result>
      </Card>
    </div>
  );
}
