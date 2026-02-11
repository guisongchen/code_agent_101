/** Form Validation Utilities
 *
 * Reusable validation rules and error message formatting for form validation.
 * Provides consistent validation across the application.
 */

// =============================================================================
// Types
// =============================================================================

export type ValidationRule = (value: unknown) => string | undefined;

export interface ValidationRules {
  required?: boolean | string;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: RegExp;
  email?: boolean;
  url?: boolean;
  match?: string; // Field name to match (for password confirmation)
  custom?: ValidationRule;
}

export interface FieldValidation {
  field: string;
  rules: ValidationRules;
}

export interface ValidationError {
  field: string;
  message: string;
}

// =============================================================================
// Validation Messages
// =============================================================================

const defaultMessages = {
  required: (field: string) => `${field} is required`,
  minLength: (field: string, min: number) =>
    `${field} must be at least ${min} characters`,
  maxLength: (field: string, max: number) =>
    `${field} must be at most ${max} characters`,
  min: (field: string, min: number) => `${field} must be at least ${min}`,
  max: (field: string, max: number) => `${field} must be at most ${max}`,
  pattern: (field: string) => `${field} format is invalid`,
  email: () => "Please enter a valid email address",
  url: () => "Please enter a valid URL",
  match: (field: string, matchField: string) =>
    `${field} must match ${matchField}`,
};

// =============================================================================
// Validation Functions
// =============================================================================

/**
 * Validates a single value against a set of rules
 */
export function validateValue(
  value: unknown,
  rules: ValidationRules,
  fieldName: string,
  allValues?: Record<string, unknown>
): string | undefined {
  // Required check
  if (rules.required) {
    const isEmpty =
      value === undefined ||
      value === null ||
      (typeof value === "string" && value.trim() === "") ||
      (Array.isArray(value) && value.length === 0);

    if (isEmpty) {
      return typeof rules.required === "string"
        ? rules.required
        : defaultMessages.required(fieldName);
    }
  }

  // Skip other validations if value is empty and not required
  if (
    value === undefined ||
    value === null ||
    (typeof value === "string" && value.trim() === "")
  ) {
    return undefined;
  }

  const stringValue = String(value);

  // Min length check
  if (rules.minLength !== undefined && stringValue.length < rules.minLength) {
    return defaultMessages.minLength(fieldName, rules.minLength);
  }

  // Max length check
  if (rules.maxLength !== undefined && stringValue.length > rules.maxLength) {
    return defaultMessages.maxLength(fieldName, rules.maxLength);
  }

  // Min value check (for numbers)
  if (rules.min !== undefined) {
    const numValue = typeof value === "number" ? value : parseFloat(stringValue);
    if (!isNaN(numValue) && numValue < rules.min) {
      return defaultMessages.min(fieldName, rules.min);
    }
  }

  // Max value check (for numbers)
  if (rules.max !== undefined) {
    const numValue = typeof value === "number" ? value : parseFloat(stringValue);
    if (!isNaN(numValue) && numValue > rules.max) {
      return defaultMessages.max(fieldName, rules.max);
    }
  }

  // Pattern check
  if (rules.pattern && !rules.pattern.test(stringValue)) {
    return defaultMessages.pattern(fieldName);
  }

  // Email check
  if (rules.email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(stringValue)) {
      return defaultMessages.email();
    }
  }

  // URL check
  if (rules.url) {
    try {
      new URL(stringValue);
    } catch {
      return defaultMessages.url();
    }
  }

  // Match check
  if (rules.match && allValues) {
    const matchValue = allValues[rules.match];
    if (value !== matchValue) {
      return defaultMessages.match(fieldName, rules.match);
    }
  }

  // Custom validation
  if (rules.custom) {
    return rules.custom(value);
  }

  return undefined;
}

/**
 * Validates multiple fields at once
 */
export function validateForm(
  values: Record<string, unknown>,
  validations: FieldValidation[]
): ValidationError[] {
  const errors: ValidationError[] = [];

  for (const { field, rules } of validations) {
    const error = validateValue(values[field], rules, field, values);
    if (error) {
      errors.push({ field, message: error });
    }
  }

  return errors;
}

/**
 * Creates a validation rule function for use with Ant Design Form
 */
export function createValidationRule(
  rules: ValidationRules,
  fieldName: string
) {
  return {
    validator(_: unknown, value: unknown) {
      const error = validateValue(value, rules, fieldName);
      if (error) {
        return Promise.reject(new Error(error));
      }
      return Promise.resolve();
    },
  };
}

// =============================================================================
// Predefined Validation Rules
// =============================================================================

export const validators = {
  /**
   * Required field validation
   */
  required: (message?: string) => ({
    required: true,
    message: message || "This field is required",
  }),

  /**
   * Minimum length validation
   */
  minLength: (min: number, message?: string) => ({
    min,
    message: message || `Must be at least ${min} characters`,
  }),

  /**
   * Maximum length validation
   */
  maxLength: (max: number, message?: string) => ({
    max,
    message: message || `Must be at most ${max} characters`,
  }),

  /**
   * Email validation
   */
  email: (message?: string) => ({
    type: "email" as const,
    message: message || "Please enter a valid email address",
  }),

  /**
   * URL validation
   */
  url: (message?: string) => ({
    type: "url" as const,
    message: message || "Please enter a valid URL",
  }),

  /**
   * Pattern validation
   */
  pattern: (pattern: RegExp, message: string) => ({
    pattern,
    message,
  }),

  /**
   * Range validation (min/max for numbers)
   */
  range: (min: number, max: number, message?: string) => ({
    min,
    max,
    message: message || `Must be between ${min} and ${max}`,
  }),

  /**
   * Whitespace validation (no leading/trailing whitespace)
   */
  noWhitespace: (message?: string) => ({
    pattern: /^\S.*\S$|^\S$/,
    message: message || "Cannot start or end with whitespace",
  }),

  /**
   * Alphanumeric validation
   */
  alphanumeric: (message?: string) => ({
    pattern: /^[a-zA-Z0-9]+$/,
    message: message || "Only letters and numbers are allowed",
  }),

  /**
   * Kubernetes name validation (DNS subdomain name)
   */
  k8sName: (message?: string) => ({
    pattern: /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/,
    message:
      message ||
      "Must consist of lowercase alphanumeric characters or '-', and must start and end with an alphanumeric character",
  }),
};

// =============================================================================
// Common Validation Presets
// =============================================================================

export const validationPresets = {
  /**
   * Username validation
   */
  username: [
    validators.required("Username is required"),
    validators.minLength(3, "Username must be at least 3 characters"),
    validators.maxLength(32, "Username must be at most 32 characters"),
    validators.noWhitespace("Username cannot contain whitespace"),
  ],

  /**
   * Password validation
   */
  password: [
    validators.required("Password is required"),
    validators.minLength(8, "Password must be at least 8 characters"),
    validators.pattern(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain at least one uppercase letter, one lowercase letter, and one number"
    ),
  ],

  /**
   * Email validation
   */
  email: [validators.required("Email is required"), validators.email()],

  /**
   * Resource name validation (for CRD resources)
   */
  resourceName: [
    validators.required("Name is required"),
    validators.minLength(1, "Name must be at least 1 character"),
    validators.maxLength(253, "Name must be at most 253 characters"),
    validators.k8sName(),
  ],

  /**
   * Namespace validation
   */
  namespace: [
    validators.required("Namespace is required"),
    validators.minLength(1, "Namespace must be at least 1 character"),
    validators.maxLength(63, "Namespace must be at most 63 characters"),
    validators.k8sName(),
  ],

  /**
   * URL validation
   */
  url: [validators.required("URL is required"), validators.url()],

  /**
   * Description validation (optional field)
   */
  description: [validators.maxLength(1000, "Description must be at most 1000 characters")],
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Formats validation errors for display
 */
export function formatValidationErrors(errors: ValidationError[]): string {
  return errors.map((e) => e.message).join("\n");
}

/**
 * Gets the first error for a specific field
 */
export function getFieldError(
  errors: ValidationError[],
  field: string
): string | undefined {
  return errors.find((e) => e.field === field)?.message;
}

/**
 * Checks if a field has any validation errors
 */
export function hasFieldError(errors: ValidationError[], field: string): boolean {
  return errors.some((e) => e.field === field);
}

export default {
  validateValue,
  validateForm,
  createValidationRule,
  validators,
  validationPresets,
  formatValidationErrors,
  getFieldError,
  hasFieldError,
};
