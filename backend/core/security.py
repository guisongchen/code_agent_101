"""Security utilities for authentication and authorization.

Epic 11: Authentication & Authorization
"""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # noqa: S105
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _base64url_encode(data: bytes) -> str:
    """Base64URL encode data."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _base64url_decode(data: str) -> bytes:
    """Base64URL decode data."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data.encode('ascii'))


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
        "exp": expire.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    })

    # JWT Header
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_encoded = _base64url_encode(json.dumps(header, separators=(',', ':')).encode())

    # JWT Payload
    payload_encoded = _base64url_encode(json.dumps(to_encode, separators=(',', ':')).encode())

    # Signature
    signing_input = f"{header_encoded}.{payload_encoded}"
    signature = hmac.new(
        SECRET_KEY.encode(),
        signing_input.encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = _base64url_encode(signature)

    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload if valid, None otherwise.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None

        header_encoded, payload_encoded, signature_encoded = parts

        # Verify signature
        signing_input = f"{header_encoded}.{payload_encoded}"
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256
        ).digest()
        expected_signature_encoded = _base64url_encode(expected_signature)

        if not secrets.compare_digest(signature_encoded, expected_signature_encoded):
            return None

        # Decode payload
        payload_bytes = _base64url_decode(payload_encoded)
        payload = json.loads(payload_bytes.decode())

        # Check expiration
        if "exp" in payload:
            exp_timestamp = payload["exp"]
            if datetime.now(timezone.utc).timestamp() > exp_timestamp:
                return None

        return payload
    except Exception:
        return None


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


def get_token_expiry_seconds() -> int:
    """Get the default token expiration time in seconds.

    Returns:
        Token expiration time in seconds.
    """
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60
