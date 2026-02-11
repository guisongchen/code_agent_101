/** Root Error Page
 *
 * Next.js error.tsx for handling errors in the root layout
 * Catches errors that occur in the root layout and its children
 */

"use client";

import { useEffect } from "react";
import { Result, Button, Typography, Space } from "antd";
import {
  ReloadOutlined,
  HomeOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";

const { Text } = Typography;

// =============================================================================
// Props
// =============================================================================

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

// =============================================================================
// Root Error Page Component
// =============================================================================

export default function RootErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // Log the error to console for debugging
    console.error("Root error page caught error:", error);
  }, [error]);

  const handleGoHome = () => {
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };

  return (
    <html lang="en">
      <body>
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            background: "#f5f5f5",
          }}
        >
          <Result
            status="error"
            icon={<ExclamationCircleOutlined />}
            title="Application Error"
            subTitle="A critical error has occurred in the application."
            extra={
              <Space wrap>
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={reset}
                >
                  Try Again
                </Button>
                <Button icon={<HomeOutlined />} onClick={handleGoHome}>
                  Go Home
                </Button>
              </Space>
            }
          >
            <div style={{ textAlign: "left" }}>
              <Text strong>Error Details:</Text>
              <br />
              <Text code>{error.message || "Unknown error occurred"}</Text>
              {error.digest && (
                <>
                  <br />
                  <Text type="secondary">Error ID: {error.digest}</Text>
                </>
              )}
            </div>
          </Result>
        </div>
      </body>
    </html>
  );
}
