/** Skills Page
 *
 * Manage Skill resources (reusable capabilities)
 */

"use client";

import React from "react";
import { Typography } from "antd";

const { Title, Text } = Typography;

export default function SkillsPage() {
  return (
    <div>
      <Title level={2}>Skills</Title>
      <Text type="secondary">
        Manage reusable capabilities that can be attached to bots
      </Text>
    </div>
  );
}
