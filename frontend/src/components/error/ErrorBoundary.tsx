/** Error Boundary Component
 *
 * Catches JavaScript errors in child components and displays a fallback UI
 * instead of crashing the entire application.
 */

"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Result, Button, Typography, Space, Card } from "antd";
import {
  ReloadOutlined,
  HomeOutlined,
  BugOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";

const { Text, Paragraph } = Typography;

// =============================================================================
// Types
// =============================================================================

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

// =============================================================================
// Error Boundary Component
// =============================================================================

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error details
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Call optional error handler
    this.props.onError?.(error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    this.props.onReset?.();
  };

  handleGoHome = (): void => {
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };

  handleReload = (): void => {
    if (typeof window !== "undefined") {
      window.location.reload();
    }
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // Custom fallback UI if provided
      if (fallback) {
        return fallback;
      }

      // Default error UI
      return (
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
            title="Something went wrong"
            subTitle="We're sorry, but an unexpected error has occurred."
            extra={
              <Space wrap>
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={this.handleReset}
                >
                  Try Again
                </Button>
                <Button icon={<HomeOutlined />} onClick={this.handleGoHome}>
                  Go Home
                </Button>
                <Button onClick={this.handleReload}>Reload Page</Button>
              </Space>
            }
          >
            <Card
              size="small"
              title={
                <Space>
                  <BugOutlined />
                  <span>Error Details</span>
                </Space>
              }
              style={{ marginTop: 16, textAlign: "left" }}
            >
              <Paragraph>
                <Text strong>Error:</Text>
                <br />
                <Text code>{error?.toString()}</Text>
              </Paragraph>
              {errorInfo && (
                <Paragraph>
                  <Text strong>Stack Trace:</Text>
                  <pre
                    style={{
                      marginTop: 8,
                      padding: 12,
                      background: "#f0f0f0",
                      borderRadius: 4,
                      overflow: "auto",
                      maxHeight: 200,
                      fontSize: 12,
                    }}
                  >
                    {errorInfo.componentStack}
                  </pre>
                </Paragraph>
              )}
            </Card>
          </Result>
        </div>
      );
    }

    return children;
  }
}

// =============================================================================
// Higher-Order Component for Easy Usage
// =============================================================================

export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, "children">
): React.ComponentType<P> {
  return function WithErrorBoundaryWrapper(props: P) {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}

export default ErrorBoundary;
