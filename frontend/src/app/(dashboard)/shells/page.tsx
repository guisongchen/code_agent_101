/** Shells Page
 *
 * Manage Shell resources (runtime environments)
 */

"use client";

import React from "react";
import { Typography } from "antd";

const { Title, Text } = Typography;

export default function ShellsPage() {
  return (
    <div>
      <Title level={2}>Shells</Title>
      <Text type="secondary">
        Manage runtime environments for executing tasks
      </Text>
    </div>
  );
}
