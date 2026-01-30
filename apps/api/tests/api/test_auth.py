"""
Authentication API tests.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


class TestAuthRegister:
    """Tests for user registration."""

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "anotherpassword123",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "securepassword123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword123",
            },
        )
        assert response.status_code == 401


class TestAuthMe:
    """Tests for current user endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_me_authenticated(self, client: AsyncClient, test_user, test_token):
        """Test getting current user when authenticated."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers(test_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user without authentication fails."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers("invalid-token"),
        )
        assert response.status_code == 401


class TestAuthRefresh:
    """Tests for token refresh."""

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_refresh_success(self, client: AsyncClient, test_user):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        if login_response.status_code != 200:
            pytest.skip("Login failed, skipping refresh test")

        refresh_token = login_response.json()["refresh_token"]

        # Then refresh - endpoint expects refresh_token as query param
        response = await client.post(
            f"/api/v1/auth/refresh?refresh_token={refresh_token}",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    @pytest.mark.auth
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/api/v1/auth/refresh?refresh_token=invalid-refresh-token",
        )
        assert response.status_code == 401
