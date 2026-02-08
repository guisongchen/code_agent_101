"""Pydantic schemas for authentication and authorization."""

import re
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.models.user import UserRole


# =============================================================================
# Token Schemas
# =============================================================================


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    expires_in: int = Field(..., alias="expiresIn", description="Token expiration time in seconds")

    model_config = ConfigDict(populate_by_name=True)


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: Optional[str] = None  # Subject (user id)
    exp: Optional[int] = None  # Expiration timestamp
    iat: Optional[int] = None  # Issued at timestamp
    role: Optional[str] = None  # User role


# =============================================================================
# User Schemas
# =============================================================================


def validate_email(email: str) -> str:
    """Simple email validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return email


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=255)
    email: str
    default_namespace: str = Field(default="default", alias="defaultNamespace")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


class UserCreateRequest(BaseModel):
    """User registration request schema."""

    username: str = Field(..., min_length=3, max_length=255)
    email: str
    password: str = Field(..., min_length=8, max_length=255)
    default_namespace: str = Field(default="default", alias="defaultNamespace")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


class UserResponse(UserBase):
    """User response schema (excludes sensitive fields)."""

    id: uuid.UUID
    role: UserRole
    is_active: bool = Field(alias="isActive")
    created_at: Optional[str] = Field(None, alias="createdAt")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class UserInDB(UserBase):
    """User schema as stored in database (includes hashed password)."""

    id: uuid.UUID
    hashed_password: str = Field(alias="hashedPassword")
    role: UserRole
    is_active: bool = Field(alias="isActive")
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


# =============================================================================
# Auth Request Schemas
# =============================================================================


class LoginRequest(BaseModel):
    """User login request schema."""

    username: str
    password: str


class RegisterRequest(BaseModel):
    """User registration request schema."""

    username: str = Field(..., min_length=3, max_length=255)
    email: str
    password: str = Field(..., min_length=8, max_length=255)
    default_namespace: str = Field(default="default", alias="defaultNamespace")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        return validate_email(v)


# =============================================================================
# Current User Schema
# =============================================================================


class CurrentUser(BaseModel):
    """Current authenticated user information."""

    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    default_namespace: str = Field(alias="defaultNamespace")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
