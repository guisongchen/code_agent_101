/** Teams Page
 *
 * Manage Team resources (multi-bot teams)
 */

"use client";

import React from "react";
import { Typography } from "antd";

const { Title, Text } = Typography;

export default function TeamsPage() {
  return (
    <div>
      <Title level={2}>Teams</Title>
      <Text type="secondary">
        Manage multi-bot teams for collaborative task execution
      </Text>
    </div>
  );
}
