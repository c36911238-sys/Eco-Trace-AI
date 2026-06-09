"""
Pytest fixtures for EcoTrace AI+ backend tests.

Provides an async HTTP test client backed by an isolated in-memory SQLite
database. Each test function gets a clean database state.
"""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Mark this as a test run so config validators use relaxed rules
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("OCR_DRIVER", "mock")

from app.main import app
from app.db.database import Base, get_db

# ── In-Memory Test Database ──────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    """Override the real DB dependency with the isolated in-memory test DB."""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Yield an async HTTPX client pointed at the test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register a test user and return their credentials."""
    payload = {
        "email": "testuser@ecotrace.ai",
        "password": "SecurePass1",
        "full_name": "Test User",
    }
    response = await client.post("/api/v1/register", json=payload)
    assert response.status_code == 201
    return payload


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    """Log in the registered test user and return Authorization headers."""
    response = await client.post(
        "/api/v1/login/access-token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
