/** Not Found Page
 *
 * Next.js not-found.tsx for handling 404 Not Found errors
 * Displayed when users access non-existent routes or resources
 */

"use client";

import Link from "next/link";
import { Result, Button, Space } from "antd";
import {
  HomeOutlined,
  SearchOutlined,
  ArrowLeftOutlined,
} from "@ant-design/icons";

// =============================================================================
// Not Found Page Component
// =============================================================================

export default function NotFoundPage() {
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
        status="404"
        title="404"
        subTitle="Sorry, the page you visited does not exist."
        extra={
          <Space wrap>
            <Link href="/" passHref>
              <Button type="primary" icon={<HomeOutlined />}>
                Back to Dashboard
              </Button>
            </Link>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => {
                if (typeof window !== "undefined") {
                  window.history.back();
                }
              }}
            >
              Go Back
            </Button>
            <Link href="/tasks" passHref>
              <Button icon={<SearchOutlined />}>View Tasks</Button>
            </Link>
          </Space>
        }
      />
    </div>
  );
}
