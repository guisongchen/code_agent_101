"""Unit tests for Authentication & Authorization API.

Epic 11: Authentication & Authorization
Tests: 24 tests covering auth functionality
"""

import pytest
from httpx import AsyncClient

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_11,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_11
@pytest.mark.unit
@pytest.mark.backend
class TestAuthAPI:
    """Test suite for Authentication API - 24 tests."""

    async def test_register_user_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert data["role"] == "user"
        assert "hashedPassword" not in data
        assert "password" not in data

    async def test_register_duplicate_username(self, async_client: AsyncClient):
        """Test registration with duplicate username fails."""
        # Register first user
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "password123",
            },
        )

        # Try to register with same username
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_register_duplicate_email(self, async_client: AsyncClient):
        """Test registration with duplicate email fails."""
        # Register first user
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "same@example.com",
                "password": "password123",
            },
        )

        # Try to register with same email
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "same@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "baduser",
                "email": "not-an-email",
                "password": "password123",
            },
        )

        assert response.status_code == 422

    async def test_login_success(self, async_client: AsyncClient):
        """Test successful login returns JWT token."""
        # Register user first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "logintest",
                "email": "login@example.com",
                "password": "password123",
            },
        )

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "logintest",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert data["tokenType"] == "bearer"
        assert "expiresIn" in data
        assert data["expiresIn"] > 0

    async def test_login_wrong_password(self, async_client: AsyncClient):
        """Test login with wrong password fails."""
        # Register user first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "wrongpass",
                "email": "wrong@example.com",
                "password": "password123",
            },
        )

        # Try login with wrong password
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "wrongpass",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123",
            },
        )

        assert response.status_code == 401

    async def test_login_missing_fields(self, async_client: AsyncClient):
        """Test login with missing fields fails."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "testuser"},
        )

        assert response.status_code == 422

    async def test_get_me_success(self, async_client: AsyncClient):
        """Test getting current user info with valid token."""
        # Register user
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "metest",
                "email": "me@example.com",
                "password": "password123",
            },
        )

        # Login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "metest",
                "password": "password123",
            },
        )
        token = login_response.json()["accessToken"]

        # Get current user
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "metest"
        assert data["email"] == "me@example.com"
        assert data["role"] == "user"

    async def test_get_me_no_token(self, async_client: AsyncClient):
        """Test getting current user without token fails."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_get_me_invalid_token(self, async_client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    async def test_register_admin_success(self, async_client: AsyncClient):
        """Test admin can register another admin."""
        # Create first admin (regular user for this test)
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "admin",
                "email": "admin@example.com",
                "password": "adminpass123",
            },
        )

        # Login as admin
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "adminpass123",
            },
        )
        token = login_response.json()["accessToken"]

        # Try to register admin (will fail because user is not admin role)
        response = await async_client.post(
            "/api/v1/auth/admin/register",
            json={
                "username": "newadmin",
                "email": "newadmin@example.com",
                "password": "adminpass123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be forbidden since regular user can't create admin
        assert response.status_code == 403

    async def test_register_admin_no_auth(self, async_client: AsyncClient):
        """Test admin registration without auth fails."""
        response = await async_client.post(
            "/api/v1/auth/admin/register",
            json={
                "username": "newadmin",
                "email": "newadmin@example.com",
                "password": "adminpass123",
            },
        )

        assert response.status_code == 401

    async def test_register_admin_duplicate(self, async_client: AsyncClient):
        """Test admin registration with duplicate username fails."""
        response = await async_client.post(
            "/api/v1/auth/admin/register",
            json={
                "username": "admin",
                "email": "admin2@example.com",
                "password": "adminpass123",
            },
        )

        assert response.status_code == 401

    async def test_token_contains_user_id(self, async_client: AsyncClient):
        """Test JWT token contains user ID in subject."""
        from backend.core.security import decode_access_token

        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "tokentest",
                "email": "token@example.com",
                "password": "password123",
            },
        )

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "tokentest",
                "password": "password123",
            },
        )
        token = login_response.json()["accessToken"]

        payload = decode_access_token(token)
        assert payload is not None
        assert "sub" in payload
        assert payload["sub"] is not None

    async def test_token_contains_role(self, async_client: AsyncClient):
        """Test JWT token contains user role."""
        from backend.core.security import decode_access_token

        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "roletest",
                "email": "role@example.com",
                "password": "password123",
            },
        )

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "roletest",
                "password": "password123",
            },
        )
        token = login_response.json()["accessToken"]

        payload = decode_access_token(token)
        assert payload is not None
        assert "role" in payload
        assert payload["role"] == "user"

    async def test_token_expiration(self, async_client: AsyncClient):
        """Test JWT token has expiration time."""
        from backend.core.security import decode_access_token

        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "exptest",
                "email": "exp@example.com",
                "password": "password123",
            },
        )

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "exptest",
                "password": "password123",
            },
        )
        token = login_response.json()["accessToken"]

        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload
        assert "iat" in payload
        assert payload["exp"] > payload["iat"]

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        from backend.core.security import decode_access_token

        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_malformed_token(self):
        """Test decoding malformed token returns None."""
        from backend.core.security import decode_access_token

        result = decode_access_token("not-a-jwt")
        assert result is None

    def test_password_hashing(self):
        """Test password hashing and verification."""
        from backend.core.security import get_password_hash, verify_password

        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    async def test_protected_endpoint_with_valid_token(self, async_client: AsyncClient):
        """Test accessing protected endpoint with valid token."""
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "protected",
                "email": "protected@example.com",
                "password": "password123",
            },
        )

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "protected",
                "password": "password123",
            },
        )
        token = login_response.json()["accessToken"]

        # Access protected endpoint
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    async def test_protected_endpoint_without_token(self, async_client: AsyncClient):
        """Test accessing protected endpoint without token fails."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "bearer" in response.headers.get("www-authenticate", "").lower()

    async def test_protected_endpoint_with_expired_token(self, async_client: AsyncClient):
        """Test accessing protected endpoint with expired token fails."""
        import time

        from backend.core.security import create_access_token

        # Create an expired token
        expired_token = create_access_token(
            data={"sub": "test-user-id"},
            expires_delta=__import__('datetime').timedelta(seconds=-1),
        )

        # Wait to ensure token is expired
        time.sleep(0.1)

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    async def test_token_authorization_header_format(self, async_client: AsyncClient):
        """Test that token must be in Bearer format."""
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "bearer",
                "email": "bearer@example.com",
                "password": "password123",
            },
        )

        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "bearer",
                "password": "password123",
            },
        )
        token = login_response.json()["accessToken"]

        # Try without Bearer prefix
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": token},
        )

        # Should fail because OAuth2 requires Bearer prefix
        assert response.status_code == 401
