"""SQLAlchemy model for User authentication and authorization."""

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base, SoftDeleteMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """User role enumeration for RBAC."""

    ADMIN = "admin"
    USER = "user"


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and authorization.

    Stores user credentials, roles, and namespace access controls.
    """

    __tablename__ = "users"

    # Primary key using UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Unique username
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # Email address
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # Hashed password (never store plain text)
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # User role for RBAC
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.USER,
    )

    # Default namespace for the user
    default_namespace: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="default",
    )

    # Whether the user account is active
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role.value})>"
