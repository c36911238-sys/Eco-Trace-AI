"""
API integration tests for EcoTrace AI+ auth and carbon endpoints.

Uses the fixtures from conftest.py: an async HTTPX client backed by
an isolated in-memory SQLite database.
"""
import io
import pytest
from httpx import AsyncClient


# ── Auth Endpoint Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAuthRegister:
    async def test_register_success(self, client: AsyncClient):
        """A valid registration should return 201 with user data."""
        response = await client.post(
            "/api/v1/register",
            json={"email": "new@ecotrace.ai", "password": "SecurePass1", "full_name": "New User"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@ecotrace.ai"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email_returns_409(self, client: AsyncClient, registered_user: dict):
        """Registering with an already-used email must return 409."""
        response = await client.post("/api/v1/register", json=registered_user)
        assert response.status_code == 409

    async def test_register_weak_password_returns_422(self, client: AsyncClient):
        """A password without uppercase/digit should fail validation."""
        response = await client.post(
            "/api/v1/register",
            json={"email": "weak@ecotrace.ai", "password": "weakpassword"},
        )
        assert response.status_code == 422

    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        """An invalid email format should be rejected."""
        response = await client.post(
            "/api/v1/register",
            json={"email": "not-an-email", "password": "SecurePass1"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAuthLogin:
    async def test_login_success_returns_token(self, client: AsyncClient, registered_user: dict):
        """Valid credentials should return an access token."""
        response = await client.post(
            "/api/v1/login/access-token",
            data={"username": registered_user["email"], "password": registered_user["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password_returns_401(self, client: AsyncClient, registered_user: dict):
        """Wrong password must return 401."""
        response = await client.post(
            "/api/v1/login/access-token",
            data={"username": registered_user["email"], "password": "WrongPass1"},
        )
        assert response.status_code == 401

    async def test_login_unknown_email_returns_401(self, client: AsyncClient):
        """Unknown email must return 401."""
        response = await client.post(
            "/api/v1/login/access-token",
            data={"username": "ghost@ecotrace.ai", "password": "SecurePass1"},
        )
        assert response.status_code == 401


# ── Carbon Log Endpoint Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
class TestCarbonLogs:
    async def test_create_log_requires_auth(self, client: AsyncClient):
        """Unauthenticated requests to create a log must return 401."""
        response = await client.post(
            "/api/v1/carbon/logs",
            json={"category": "food", "emission_amount": 5.0},
        )
        assert response.status_code == 401

    async def test_create_log_authenticated(self, client: AsyncClient, auth_headers: dict):
        """Authenticated user can create a carbon log entry."""
        response = await client.post(
            "/api/v1/carbon/logs",
            json={"category": "food", "emission_amount": 12.5},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "food"
        assert data["emission_amount"] == 12.5

    async def test_get_logs_empty_for_new_user(self, client: AsyncClient, auth_headers: dict):
        """A freshly registered user should have zero logs."""
        response = await client.get("/api/v1/carbon/logs", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_logs_returns_created_entries(self, client: AsyncClient, auth_headers: dict):
        """Created logs should appear in the GET response."""
        await client.post(
            "/api/v1/carbon/logs",
            json={"category": "electricity", "emission_amount": 50.0},
            headers=auth_headers,
        )
        response = await client.get("/api/v1/carbon/logs", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1


# ── Receipt Upload Tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestReceiptUpload:
    async def test_upload_valid_jpeg_creates_log(self, client: AsyncClient, auth_headers: dict):
        """A valid JPEG upload should create a new carbon log via OCR."""
        fake_image = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100)  # Minimal JPEG header
        response = await client.post(
            "/api/v1/carbon/receipt",
            files={"file": ("receipt.jpg", fake_image, "image/jpeg")},
            headers=auth_headers,
        )
        assert response.status_code == 201

    async def test_upload_invalid_type_returns_415(self, client: AsyncClient, auth_headers: dict):
        """A PDF upload should be rejected with 415."""
        fake_pdf = io.BytesIO(b"%PDF-1.4 content here")
        response = await client.post(
            "/api/v1/carbon/receipt",
            files={"file": ("receipt.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 415

    async def test_upload_oversized_file_returns_413(self, client: AsyncClient, auth_headers: dict):
        """A file exceeding 5MB should be rejected with 413."""
        oversized = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1))
        response = await client.post(
            "/api/v1/carbon/receipt",
            files={"file": ("big.jpg", oversized, "image/jpeg")},
            headers=auth_headers,
        )
        assert response.status_code == 413


# ── Health Endpoint ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_root_returns_200(self, client: AsyncClient):
        """Root endpoint should be reachable without authentication."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "version" in response.json()

    async def test_health_check_returns_ok(self, client: AsyncClient):
        """Health check endpoint should return status ok."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
