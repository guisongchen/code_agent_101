/** Register Page
 *
 * User registration page
 */

"use client";

import React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Alert,
  Space,
  Divider,
} from "antd";
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  UserAddOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/context/auth-context";

const { Title, Text } = Typography;

interface RegisterFormValues {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  defaultNamespace?: string;
}

export default function RegisterPage() {
  const { register, isLoading, error, isAuthenticated } = useAuth();
  const router = useRouter();
  const [form] = Form.useForm();
  const [localError, setLocalError] = React.useState<string | null>(null);

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (values: RegisterFormValues) => {
    setLocalError(null);

    // Validate passwords match
    if (values.password !== values.confirmPassword) {
      setLocalError("Passwords do not match");
      return;
    }

    // Validate password length
    if (values.password.length < 8) {
      setLocalError("Password must be at least 8 characters");
      return;
    }

    try {
      await register({
        username: values.username,
        email: values.email,
        password: values.password,
        defaultNamespace: values.defaultNamespace || "default",
      });
    } catch {
      // Error is handled by auth context
    }
  };

  const displayError = error || localError;

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f0f2f5",
        padding: 24,
      }}
    >
      <Card
        style={{
          width: "100%",
          maxWidth: 420,
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 8, color: "#1890ff" }}>
            Wegent
          </Title>
          <Text type="secondary">Create your account</Text>
        </div>

        {displayError && (
          <Alert
            message={displayError}
            type="error"
            showIcon
            style={{ marginBottom: 24 }}
            closable
            onClose={() => setLocalError(null)}
          />
        )}

        <Form
          form={form}
          name="register"
          onFinish={handleSubmit}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: "Please enter your username" },
              { min: 3, message: "Username must be at least 3 characters" },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Username"
              size="large"
              autoFocus
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: "Please enter your email" },
              { type: "email", message: "Please enter a valid email" },
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="Email"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: "Please enter your password" },
              { min: 8, message: "Password must be at least 8 characters" },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            rules={[
              { required: true, message: "Please confirm your password" },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Confirm Password"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="defaultNamespace"
            initialValue="default"
            rules={[
              { required: true, message: "Please enter a default namespace" },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Default Namespace"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              icon={<UserAddOutlined />}
              loading={isLoading}
            >
              Create Account
            </Button>
          </Form.Item>
        </Form>

        <Divider />

        <Space direction="vertical" style={{ width: "100%", textAlign: "center" }}>
          <Text type="secondary">
            Already have an account?{" "}
            <Link href="/login">Sign in</Link>
          </Text>
        </Space>
      </Card>
    </div>
  );
}
