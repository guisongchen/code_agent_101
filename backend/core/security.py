"""Security utilities for authentication and authorization.

Epic 11: Authentication & Authorization
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # noqa: S105
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Uses a simple hash-based approach for development.
    In production, use bcrypt via passlib.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    # Format: salt$hash
    if "$" not in hashed_password:
        return False

    salt, stored_hash = hashed_password.split("$", 1)
    computed_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
    return secrets.compare_digest(computed_hash, stored_hash)


def get_password_hash(password: str) -> str:
    """Hash a plain text password.

    Uses a simple hash-based approach for development.
    In production, use bcrypt via passlib.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password.
    """
    salt = secrets.token_hex(16)
    hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hash_value}"


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: The data to encode in the token (typically contains "sub" for subject).
        expires_delta: Optional custom expiration time. Defaults to 30 minutes.

    Returns:
        The encoded JWT token string.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_token_expiry_seconds() -> int:
    """Get the default token expiration time in seconds.

    Returns:
        Token expiration time in seconds.
    """
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60
