/** Ghosts Page
 *
 * Manage Ghost resources (AI system prompts and personalities)
 */

"use client";

import React from "react";
import { Typography } from "antd";

const { Title, Text } = Typography;

export default function GhostsPage() {
  return (
    <div>
      <Title level={2}>Ghosts</Title>
      <Text type="secondary">
        Manage AI system prompts and personalities
      </Text>
    </div>
  );
}
