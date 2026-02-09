"""
Pytest configuration and fixtures for ISORA API tests.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32chars"
os.environ["SECRET_KEY"] = "test-app-secret-key-for-testing-32chars"

from src.main import app
from src.db.database import Base, get_db
from src.models.user import User
from src.models.organization import Organization, OrganizationMember, OrganizationMemberRole, OrganizationStatus, OrganizationPlan
from src.core.security import create_access_token
from src.services.auth_service import AuthService


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async database engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sync_client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create synchronous test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# =============================================================================
# Organization Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization (tenant)."""
    org = Organization(
        id=str(uuid4()),
        name="Test Organization",
        slug="test-org",
        status=OrganizationStatus.ACTIVE,
        plan=OrganizationPlan.PROFESSIONAL,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


# =============================================================================
# User Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a test user with organization membership."""
    from src.models.user import UserRole
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        full_name="Test User",
        hashed_password=AuthService.hash_password("testpassword123"),
        role=UserRole.ANALYST,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()

    # Create organization membership
    membership = OrganizationMember(
        id=str(uuid4()),
        organization_id=test_organization.id,
        user_id=user.id,
        org_role=OrganizationMemberRole.MEMBER,
        is_default=True,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)

    # Store tenant_id on user for easy access in tests
    user.tenant_id = test_organization.id
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create an admin test user with organization membership."""
    from src.models.user import UserRole
    user = User(
        id=str(uuid4()),
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=AuthService.hash_password("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()

    # Create organization membership as admin
    membership = OrganizationMember(
        id=str(uuid4()),
        organization_id=test_organization.id,
        user_id=user.id,
        org_role=OrganizationMemberRole.ADMIN,
        is_default=True,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)

    # Store tenant_id on user for easy access in tests
    user.tenant_id = test_organization.id
    return user


@pytest_asyncio.fixture
async def lead_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a lead test user with organization membership."""
    from src.models.user import UserRole
    user = User(
        id=str(uuid4()),
        email="lead@example.com",
        full_name="Lead User",
        hashed_password=AuthService.hash_password("leadpassword123"),
        role=UserRole.LEAD,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()

    # Create organization membership
    membership = OrganizationMember(
        id=str(uuid4()),
        organization_id=test_organization.id,
        user_id=user.id,
        org_role=OrganizationMemberRole.MEMBER,
        is_default=True,
        joined_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)

    # Store tenant_id on user for easy access in tests
    user.tenant_id = test_organization.id
    return user


# =============================================================================
# Auth Fixtures
# =============================================================================

@pytest.fixture
def test_token(test_user: User) -> str:
    """Create access token for test user with tenant context."""
    return create_access_token(data={
        "sub": test_user.id,
        "role": test_user.role.value,
        "tenant_id": test_user.tenant_id,
        "org_role": "member",
        "available_tenants": [test_user.tenant_id],
    })


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create access token for admin user with tenant context."""
    return create_access_token(data={
        "sub": admin_user.id,
        "role": admin_user.role.value,
        "tenant_id": admin_user.tenant_id,
        "org_role": "admin",
        "available_tenants": [admin_user.tenant_id],
    })


@pytest.fixture
def lead_token(lead_user: User) -> str:
    """Create access token for lead user with tenant context."""
    return create_access_token(data={
        "sub": lead_user.id,
        "role": lead_user.role.value,
        "tenant_id": lead_user.tenant_id,
        "org_role": "member",
        "available_tenants": [lead_user.tenant_id],
    })


def auth_headers(token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Incident Fixtures
# =============================================================================

@pytest.fixture
def sample_incident_data() -> dict:
    """Sample incident data for tests."""
    return {
        "title": "Test Ransomware Incident",
        "description": "A test ransomware incident for testing purposes",
        "severity": "high",
        "incident_type": "ransomware",
        "affected_systems": [
            {
                "name": "Server-01",
                "type": "server",
                "criticality": "high",
                "ip_address": "192.168.1.10",
            }
        ],
    }


@pytest.fixture
def sample_evidence_data() -> dict:
    """Sample evidence data for tests."""
    return {
        "entry_type": "observation",
        "phase": "detection",
        "description": "Observed suspicious network traffic to known C2 server",
        "tags": ["network", "c2", "suspicious"],
    }


# =============================================================================
# Compliance Fixtures
# =============================================================================

@pytest.fixture
def sample_compliance_frameworks() -> list:
    """List of compliance frameworks for testing."""
    return ["bsi", "nist", "iso27001", "owasp"]


@pytest.fixture
def sample_ioc_data() -> dict:
    """Sample IOC data for testing."""
    return {
        "ioc_type": "ip",
        "value": "192.168.1.100",
    }


# =============================================================================
# Helper Functions
# =============================================================================

def assert_datetime_recent(dt: datetime, max_age_seconds: int = 60) -> None:
    """Assert that a datetime is recent (within max_age_seconds of now)."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = abs((now - dt).total_seconds())
    assert diff < max_age_seconds, f"Datetime {dt} is not recent (diff: {diff}s)"
