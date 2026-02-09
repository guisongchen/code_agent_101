/** Bots Page
 *
 * Manage Bot resources (AI agents)
 */

"use client";

import React from "react";
import { Typography } from "antd";

const { Title, Text } = Typography;

export default function BotsPage() {
  return (
    <div>
      <Title level={2}>Bots</Title>
      <Text type="secondary">
        Manage AI agents that combine Ghost, Model, and Shell configurations
      </Text>
    </div>
  );
}
