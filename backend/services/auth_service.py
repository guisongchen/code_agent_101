"""Authentication service for user management.

Epic 11: Authentication & Authorization
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_password_hash, verify_password
from backend.models.user import User, UserRole
from backend.schemas.auth import RegisterRequest, UserCreateRequest, UserResponse


class AuthService:
    """Service for authentication and user management operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the auth service with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.

        Args:
            username: The username to look up.

        Returns:
            The User if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(
                User.username == username,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.

        Args:
            email: The email to look up.

        Returns:
            The User if found, None otherwise.
        """
        result = await self.session.execute(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID.

        Args:
            user_id: The user ID to look up.

        Returns:
            The User if found, None otherwise.
        """
        from uuid import UUID

        result = await self.session.execute(
            select(User).where(
                User.id == UUID(user_id),
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password.

        Args:
            username: The username to authenticate.
            password: The plain text password to verify.

        Returns:
            The User if authentication succeeds, None otherwise.
        """
        user = await self.get_user_by_username(username)

        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def create_user(self, request: RegisterRequest) -> User:
        """Create a new user.

        Args:
            request: The user registration request.

        Returns:
            The created User.

        Raises:
            ValueError: If username or email already exists.
        """
        # Check for existing username
        existing_user = await self.get_user_by_username(request.username)
        if existing_user:
            raise ValueError(f"Username '{request.username}' already exists")

        # Check for existing email
        existing_email = await self.get_user_by_email(request.email)
        if existing_email:
            raise ValueError(f"Email '{request.email}' already registered")

        # Create new user
        user = User(
            username=request.username,
            email=request.email,
            hashed_password=get_password_hash(request.password),
            default_namespace=request.default_namespace,
            role=UserRole.USER,  # Default role for new users
            is_active=True,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def create_admin_user(self, request: RegisterRequest) -> User:
        """Create a new admin user.

        Args:
            request: The user registration request.

        Returns:
            The created User with admin role.

        Raises:
            ValueError: If username or email already exists.
        """
        # Check for existing username
        existing_user = await self.get_user_by_username(request.username)
        if existing_user:
            raise ValueError(f"Username '{request.username}' already exists")

        # Check for existing email
        existing_email = await self.get_user_by_email(request.email)
        if existing_email:
            raise ValueError(f"Email '{request.email}' already registered")

        # Create new admin user
        user = User(
            username=request.username,
            email=request.email,
            hashed_password=get_password_hash(request.password),
            default_namespace=request.default_namespace,
            role=UserRole.ADMIN,
            is_active=True,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    def to_response(self, user: User) -> UserResponse:
        """Convert a User model to UserResponse schema.

        Args:
            user: The User model to convert.

        Returns:
            The UserResponse schema.
        """
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            default_namespace=user.default_namespace,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
