# Testing and Multi-Tenancy Documentation

This document covers the testing infrastructure and multi-tenancy implementation in CyberOps Companion.

---

## Table of Contents

1. [Multi-Tenancy Architecture](#multi-tenancy-architecture)
2. [Test Infrastructure](#test-infrastructure)
3. [SQLite Compatibility](#sqlite-compatibility)
4. [Recent Fixes](#recent-fixes)

---

## Multi-Tenancy Architecture

### Overview

CyberOps Companion uses a **tenant-per-organization** model where each organization is isolated from others. All tenant-scoped data includes a `tenant_id` foreign key to the `organizations` table.

### Key Components

#### 1. TenantMixin (`src/models/mixins.py`)

```python
class TenantMixin:
    """Mixin to add tenant_id to models for multi-tenancy isolation."""

    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        return mapped_column(
            String(36),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )
```

Models that use this mixin:
- `Incident`
- `AffectedSystem`
- `EvidenceEntry`
- `Vulnerability`
- `Risk`
- `Asset`
- All compliance assessments (NIS2, ISO27001, GDPR, NIST, COBIT, KRITIS, TISAX, BCM)

#### 2. Organization Model (`src/models/organization.py`)

```python
class Organization(Base):
    __tablename__ = "organizations"

    id: str                      # UUID primary key
    name: str                    # Organization name
    slug: str                    # URL-friendly identifier
    status: OrganizationStatus   # active, suspended, trial, cancelled
    plan: OrganizationPlan       # free, starter, professional, enterprise
    max_users: int               # User limit based on plan
```

#### 3. Organization Membership (`src/models/organization.py`)

```python
class OrganizationMember(Base):
    __tablename__ = "organization_members"

    organization_id: str         # FK to organizations
    user_id: str                 # FK to users
    org_role: OrganizationMemberRole  # owner, admin, member, viewer
    is_default: bool             # Default org for user
```

#### 4. Tenant Context (`src/core/tenant_context.py`)

```python
@dataclass
class TenantContext:
    tenant_id: str
    user_id: str
    org_role: str
    is_super_admin: bool
```

### Authentication Flow

1. User authenticates → receives JWT with `tenant_id`
2. API endpoints use `UserWithTenant` dependency
3. Dependency extracts tenant context from JWT
4. Services receive `tenant_id` and scope all operations

### JWT Token Structure

```python
{
    "sub": "user-uuid",           # User ID
    "role": "analyst",            # System role
    "tenant_id": "org-uuid",      # Current organization
    "org_role": "member",         # Role in organization
    "available_tenants": ["..."], # All accessible orgs
    "exp": 1234567890,            # Expiration
    "type": "access"              # Token type
}
```

### API Dependency Usage

```python
from src.api.deps import UserWithTenant

@router.post("/incidents")
async def create_incident(
    data: IncidentCreate,
    db: DBSession,
    user_context: UserWithTenant,  # Returns (User, TenantContext)
):
    current_user, context = user_context
    # Use context.tenant_id for tenant-scoped operations
    incident = await service.create(data, current_user.id, context.tenant_id)
```

---

## Test Infrastructure

### Configuration (`tests/conftest.py`)

#### Environment Variables

```python
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32chars"
```

#### Database Fixtures

```python
@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """In-memory SQLite database for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Cleanup
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine):
    """Database session with automatic rollback."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()
```

#### Organization Fixture

```python
@pytest_asyncio.fixture
async def test_organization(db_session) -> Organization:
    """Create test organization (tenant)."""
    org = Organization(
        id=str(uuid4()),
        name="Test Organization",
        slug="test-org",
        status=OrganizationStatus.ACTIVE,
        plan=OrganizationPlan.PROFESSIONAL,
    )
    db_session.add(org)
    await db_session.commit()
    return org
```

#### User Fixtures with Membership

```python
@pytest_asyncio.fixture
async def test_user(db_session, test_organization) -> User:
    """Create test user with organization membership."""
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        full_name="Test User",
        role=UserRole.ANALYST,
    )
    db_session.add(user)
    await db_session.flush()

    # Create membership
    membership = OrganizationMember(
        organization_id=test_organization.id,
        user_id=user.id,
        org_role=OrganizationMemberRole.MEMBER,
        is_default=True,
    )
    db_session.add(membership)
    await db_session.commit()

    # Store tenant_id for token generation
    user.tenant_id = test_organization.id
    return user
```

#### Token Fixtures

```python
@pytest.fixture
def test_token(test_user) -> str:
    """JWT token with tenant context."""
    return create_access_token(data={
        "sub": test_user.id,
        "role": test_user.role.value,
        "tenant_id": test_user.tenant_id,
        "org_role": "member",
        "available_tenants": [test_user.tenant_id],
    })
```

### Running Tests

```bash
# Run all tests
docker compose run --rm api pytest -v

# Run specific test file
docker compose run --rm api pytest tests/api/test_incidents.py -v

# Run with coverage
docker compose run --rm api pytest --cov=src --cov-report=html
```

### Test Categories

| Directory | Purpose |
|-----------|---------|
| `tests/api/` | API endpoint tests |
| `tests/integrations/` | Integration and service tests |
| `tests/unit/` | Unit tests for utilities |

---

## SQLite Compatibility

### Issue

PostgreSQL `ARRAY` type is not supported by SQLite, causing tests to fail.

### Solution

Replace `ARRAY(String)` with `JSON` for SQLite compatibility while maintaining PostgreSQL functionality.

### Affected Models

| Model | Fields Changed |
|-------|----------------|
| `threat_intel.py` | `aliases`, `tags`, `categories`, `mitre_techniques`, `target_sectors`, `target_countries`, `tools_used`, `attack_vectors`, `malware_used`, `ioc_types` |
| `risk.py` | `affected_assets`, `affected_processes`, `affected_data_types`, `compliance_frameworks`, `compliance_controls`, `tags`, `compliance_control_ids` |
| `vulnerability.py` | `services`, `open_ports`, `tags`, `cwe_ids`, `affected_cpe`, `notification_emails` |
| `cmdb.py` | `compliance_requirements`, `tags`, `changed_fields` |

### Migration Pattern

```python
# Before (PostgreSQL only)
from sqlalchemy.dialects.postgresql import ARRAY
tags = mapped_column(ARRAY(String), default=[])

# After (SQLite compatible)
from sqlalchemy import JSON
tags = mapped_column(JSON, default=[])
```

---

## Recent Fixes

### Fix 1: SQLite ARRAY Compatibility (commit: 8518405)

**Problem:** Tests failed with `Compiler can't render element of type ARRAY`

**Solution:** Changed all `ARRAY(String)` columns to `JSON` type

**Files Modified:**
- `src/models/threat_intel.py`
- `src/models/risk.py`
- `src/models/vulnerability.py`
- `src/models/cmdb.py`

### Fix 2: Import Path Corrections (commit: 8518405)

**Problem:** Various import errors after refactoring

**Fixes Applied:**

| File | Issue | Fix |
|------|-------|-----|
| Multiple API files | `from src.db.session` | `from src.db.database` |
| API files | `from src.api.v1.auth import get_current_user` | `from src.api.deps import get_current_user` |
| Model files | `from src.db.base import Base` | `from src.db.database import Base` |
| kritis.py, tisax.py | `get_tenant_id` not found | Use `current_user.tenant_id` via context |

### Fix 3: Test Tenant Context (commit: 064ea60)

**Problem:** 43 tests failed with `NOT NULL constraint failed: incidents.tenant_id`

**Root Cause:** Test fixtures didn't create organization/membership, and services didn't receive `tenant_id`

**Solution:**

1. **Test Fixtures** (`conftest.py`):
   - Added `test_organization` fixture
   - Updated user fixtures to create `OrganizationMember`
   - Added `tenant_id` to user object for token generation
   - Updated token fixtures to include tenant context

2. **Services**:
   - `incident_service.py`: Added `tenant_id` parameter to `create()` and `add_affected_system()`
   - `evidence_service.py`: Added `tenant_id` parameter to `create_entry()` and `log_decision()`

3. **API Endpoints**:
   - `incidents.py`: Changed `CurrentUser` to `UserWithTenant` for create/add_system
   - `evidence.py`: Changed `CurrentUser` to `UserWithTenant` for create
   - `decisions.py`: Changed `CurrentUser` to `UserWithTenant` for make_decision

**Pattern for Adding Tenant Support:**

```python
# Before
@router.post("/resource")
async def create_resource(
    data: ResourceCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    return await service.create(data, current_user.id)

# After
@router.post("/resource")
async def create_resource(
    data: ResourceCreate,
    db: DBSession,
    user_context: UserWithTenant,
):
    current_user, context = user_context
    return await service.create(data, current_user.id, context.tenant_id)
```

---

## Test Results

After all fixes:

```
============ 270 passed, 4 skipped, 6 warnings in 96.40s =============
```

### Warnings (Non-Critical)

FastAPI deprecation warnings for `regex` parameter (should use `pattern`):
- `cmdb.py:405`
- `iso27001.py:577, 580`
- `bcm.py:622, 1027`
- `nis2.py:402`

These are cosmetic and don't affect functionality.

---

## Best Practices

### Creating New Tenant-Scoped Models

1. Inherit from `TenantMixin`:
   ```python
   class MyModel(TenantMixin, Base):
       __tablename__ = "my_models"
   ```

2. Update service to accept `tenant_id`:
   ```python
   async def create(self, data, user_id: str, tenant_id: str):
       entity = MyModel(..., tenant_id=tenant_id)
   ```

3. Update endpoint to use `UserWithTenant`:
   ```python
   async def create(user_context: UserWithTenant):
       user, context = user_context
       await service.create(data, user.id, context.tenant_id)
   ```

### Writing Tests for Tenant-Scoped Features

1. Use fixtures that provide tenant context:
   ```python
   async def test_create(client, test_token, sample_data):
       response = await client.post(
           "/api/v1/resource",
           json=sample_data,
           headers=auth_headers(test_token),
       )
       assert response.status_code == 201
   ```

2. The `test_token` fixture automatically includes `tenant_id` from `test_organization`.

---

## Troubleshooting

### "NOT NULL constraint failed: *.tenant_id"

**Cause:** Service not receiving or passing `tenant_id`

**Fix:**
1. Check endpoint uses `UserWithTenant`
2. Check service method accepts `tenant_id` parameter
3. Check model includes `TenantMixin`

### "Compiler can't render element of type ARRAY"

**Cause:** Using PostgreSQL `ARRAY` type with SQLite

**Fix:** Change to `JSON` type:
```python
# Change this
from sqlalchemy.dialects.postgresql import ARRAY
field = mapped_column(ARRAY(String))

# To this
from sqlalchemy import JSON
field = mapped_column(JSON, default=[])
```

### Import Errors

**Common patterns:**
- `src.db.session` → `src.db.database`
- `src.db.base` → `src.db.database`
- `src.api.v1.auth.get_current_user` → `src.api.deps.get_current_user`
