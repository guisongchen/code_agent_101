/** Models Page
 *
 * Manage Model resources (AI model configurations)
 */

"use client";

import React from "react";
import { Typography } from "antd";

const { Title, Text } = Typography;

export default function ModelsPage() {
  return (
    <div>
      <Title level={2}>Models</Title>
      <Text type="secondary">
        Manage AI model configurations and API settings
      </Text>
    </div>
  );
}
