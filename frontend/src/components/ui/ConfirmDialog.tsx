/** Confirm Dialog Component
 *
 * Reusable confirmation dialog for destructive actions like delete operations.
 * Provides consistent UI and behavior for confirmation prompts.
 */

import React, { useState, useCallback } from "react";
import { Modal, Button, Space, Typography, Alert } from "antd";
import {
  ExclamationCircleOutlined,
  DeleteOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from "@ant-design/icons";

const { Text } = Typography;

// =============================================================================
// Types
// =============================================================================

export type ConfirmVariant = "danger" | "warning" | "info" | "confirm";

export interface ConfirmDialogOptions {
  title: string;
  content?: React.ReactNode;
  variant?: ConfirmVariant;
  confirmText?: string;
  cancelText?: string;
  confirmLoading?: boolean;
  okButtonProps?: React.ComponentProps<typeof Button>;
  cancelButtonProps?: React.ComponentProps<typeof Button>;
  width?: number | string;
  centered?: boolean;
  closable?: boolean;
  maskClosable?: boolean;
  keyboard?: boolean;
}

export interface ConfirmDialogResult {
  confirmed: boolean;
}

// =============================================================================
// Confirm Dialog Hook
// =============================================================================

export function useConfirmDialog() {
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState<ConfirmDialogOptions | null>(null);
  const [resolveRef, setResolveRef] = useState<
    ((value: ConfirmDialogResult) => void) | null
  >(null);

  const showConfirm = useCallback(
    (dialogOptions: ConfirmDialogOptions): Promise<ConfirmDialogResult> => {
      return new Promise((resolve) => {
        setOptions(dialogOptions);
        setVisible(true);
        setResolveRef(() => resolve);
      });
    },
    []
  );

  const handleConfirm = useCallback(async () => {
    if (options?.confirmLoading) {
      setLoading(true);
      // Wait for the parent to handle the async operation
      // The parent should call hide() when done
    }

    resolveRef?.({ confirmed: true });

    if (!options?.confirmLoading) {
      setVisible(false);
      setOptions(null);
    }
  }, [options?.confirmLoading, resolveRef]);

  const handleCancel = useCallback(() => {
    resolveRef?.({ confirmed: false });
    setVisible(false);
    setLoading(false);
    setOptions(null);
  }, [resolveRef]);

  const hide = useCallback(() => {
    setVisible(false);
    setLoading(false);
    setOptions(null);
  }, []);

  const ConfirmDialogComponent = useCallback(() => {
    if (!options) return null;

    const {
      title,
      content,
      variant = "confirm",
      confirmText,
      cancelText = "Cancel",
      okButtonProps,
      cancelButtonProps,
      width = 420,
      centered = true,
      closable = true,
      maskClosable = false,
      keyboard = true,
    } = options;

    const config = getVariantConfig(variant);
    const finalConfirmText = confirmText || config.confirmText;

    return (
      <Modal
        open={visible}
        title={
          <Space>
            {config.icon}
            <span>{title}</span>
          </Space>
        }
        width={width}
        centered={centered}
        closable={closable}
        maskClosable={maskClosable}
        keyboard={keyboard}
        onCancel={handleCancel}
        footer={
          <Space>
            <Button onClick={handleCancel} {...cancelButtonProps}>
              {cancelText}
            </Button>
            <Button
              type={config.buttonType}
              danger={config.danger}
              loading={loading}
              onClick={handleConfirm}
              {...okButtonProps}
            >
              {finalConfirmText}
            </Button>
          </Space>
        }
      >
        {content}
      </Modal>
    );
  }, [options, visible, loading, handleConfirm, handleCancel]);

  return {
    showConfirm,
    hide,
    ConfirmDialog: ConfirmDialogComponent,
  };
}

// =============================================================================
// Static Confirm Function (similar to Ant Design Modal.confirm)
// =============================================================================

export function confirm(options: ConfirmDialogOptions): Promise<boolean> {
  return new Promise((resolve) => {
    const {
      title,
      content,
      variant = "confirm",
      confirmText,
      cancelText = "Cancel",
      okButtonProps,
      cancelButtonProps,
      width = 420,
      centered = true,
      closable = true,
      maskClosable = false,
      keyboard = true,
    } = options;

    const config = getVariantConfig(variant);
    const finalConfirmText = confirmText || config.confirmText;

    Modal.confirm({
      title: (
        <Space>
          {config.icon}
          <span>{title}</span>
        </Space>
      ),
      content,
      width,
      centered,
      closable,
      maskClosable,
      keyboard,
      okText: finalConfirmText,
      cancelText,
      okButtonProps: {
        danger: config.danger,
        type: config.buttonType,
        ...okButtonProps,
      },
      cancelButtonProps,
      onOk: () => {
        resolve(true);
      },
      onCancel: () => {
        resolve(false);
      },
    });
  });
}

// =============================================================================
// Convenience Functions
// =============================================================================

export function confirmDelete(
  itemName: string,
  options: Partial<ConfirmDialogOptions> = {}
): Promise<boolean> {
  return confirm({
    title: "Delete Confirmation",
    content: (
      <Space direction="vertical" style={{ width: "100%" }}>
        <Text>
          Are you sure you want to delete <strong>{itemName}</strong>?
        </Text>
        <Alert
          message="This action cannot be undone."
          type="warning"
          showIcon
          banner
          style={{ marginTop: 8 }}
        />
      </Space>
    ),
    variant: "danger",
    confirmText: "Delete",
    ...options,
  });
}

export function confirmDangerousAction(
  action: string,
  options: Partial<ConfirmDialogOptions> = {}
): Promise<boolean> {
  return confirm({
    title: "Confirm Action",
    content: (
      <Text>
        Are you sure you want to <strong>{action}</strong>?
      </Text>
    ),
    variant: "danger",
    ...options,
  });
}

export function confirmUnsavedChanges(
  options: Partial<ConfirmDialogOptions> = {}
): Promise<boolean> {
  return confirm({
    title: "Unsaved Changes",
    content: (
      <Text>
        You have unsaved changes. Are you sure you want to leave without saving?
      </Text>
    ),
    variant: "warning",
    confirmText: "Leave",
    cancelText: "Stay",
    ...options,
  });
}

// =============================================================================
// Helper Functions
// =============================================================================

interface VariantConfig {
  icon: React.ReactNode;
  buttonType: "primary" | "default" | "dashed" | "link" | "text";
  danger: boolean;
  confirmText: string;
}

function getVariantConfig(variant: ConfirmVariant): VariantConfig {
  switch (variant) {
    case "danger":
      return {
        icon: <DeleteOutlined style={{ color: "#ff4d4f" }} />,
        buttonType: "primary",
        danger: true,
        confirmText: "Delete",
      };
    case "warning":
      return {
        icon: <WarningOutlined style={{ color: "#faad14" }} />,
        buttonType: "primary",
        danger: true,
        confirmText: "Continue",
      };
    case "info":
      return {
        icon: <InfoCircleOutlined style={{ color: "#1890ff" }} />,
        buttonType: "primary",
        danger: false,
        confirmText: "OK",
      };
    case "confirm":
    default:
      return {
        icon: <ExclamationCircleOutlined style={{ color: "#1890ff" }} />,
        buttonType: "primary",
        danger: false,
        confirmText: "Confirm",
      };
  }
}

// =============================================================================
// Confirm Dialog Component (for direct usage)
// =============================================================================

export interface ConfirmDialogProps extends ConfirmDialogOptions {
  open: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  content,
  variant = "confirm",
  confirmText,
  cancelText = "Cancel",
  confirmLoading = false,
  onConfirm,
  onCancel,
  okButtonProps,
  cancelButtonProps,
  width = 420,
  centered = true,
  closable = true,
  maskClosable = false,
  keyboard = true,
}: ConfirmDialogProps) {
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    if (confirmLoading) {
      setLoading(true);
    }

    try {
      await onConfirm();
    } finally {
      if (confirmLoading) {
        setLoading(false);
      }
    }
  };

  const config = getVariantConfig(variant);
  const finalConfirmText = confirmText || config.confirmText;

  return (
    <Modal
      open={open}
      title={
        <Space>
          {config.icon}
          <span>{title}</span>
        </Space>
      }
      width={width}
      centered={centered}
      closable={closable}
      maskClosable={maskClosable}
      keyboard={keyboard}
      onCancel={onCancel}
      footer={
        <Space>
          <Button onClick={onCancel} {...cancelButtonProps}>
            {cancelText}
          </Button>
          <Button
            type={config.buttonType}
            danger={config.danger}
            loading={loading}
            onClick={handleConfirm}
            {...okButtonProps}
          >
            {finalConfirmText}
          </Button>
        </Space>
      }
    >
      {content}
    </Modal>
  );
}

export default {
  useConfirmDialog,
  confirm,
  confirmDelete,
  confirmDangerousAction,
  confirmUnsavedChanges,
  ConfirmDialog,
};
