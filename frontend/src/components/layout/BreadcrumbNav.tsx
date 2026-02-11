/** Breadcrumb Navigation Component
 *
 * Breadcrumb navigation based on current route
 */

"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Breadcrumb } from "antd";
import { HomeOutlined } from "@ant-design/icons";

// Route to breadcrumb name mapping
const routeNames: Record<string, string> = {
  "/": "Dashboard",
  "/tasks": "Tasks",
  "/chat": "Chat",
  "/ghosts": "Ghosts",
  "/models": "Models",
  "/shells": "Shells",
  "/bots": "Bots",
  "/teams": "Teams",
  "/skills": "Skills",
};

export function BreadcrumbNav() {
  const pathname = usePathname();

  // Generate breadcrumb items from pathname
  const pathSegments = pathname.split("/").filter(Boolean);

  // Build breadcrumb items
  const items = [
    {
      title: (
        <Link href="/">
          <HomeOutlined />
        </Link>
      ),
    },
  ];

  let currentPath = "";
  pathSegments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const isLast = index === pathSegments.length - 1;

    // Check if it's a UUID (task ID, etc.)
    const isUuid =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        segment
      );

    const title = isUuid
      ? "Details"
      : routeNames[currentPath] || segment.charAt(0).toUpperCase() + segment.slice(1);

    items.push({
      title: isLast ? (
        <span>{title}</span>
      ) : (
        <Link href={currentPath}>{title}</Link>
      ),
    });
  });

  return <Breadcrumb items={items} style={{ marginBottom: 16 }} />;
}
