# Role-Based Access Control (RBAC)

**Status:** ✅ Implemented
**Date:** 2026-01-31
**Location:** `apps/api/src/api/deps.py`, `apps/api/src/models/user.py`

---

## Overview

Hierarchical role-based access control system using FastAPI dependencies. Roles have a hierarchy where higher roles inherit permissions of lower roles.

---

## Role Hierarchy

```
ADMIN (4)      ─── Full system access
    │
MANAGER (3)   ─── Team management, view all data
    │
LEAD (2)      ─── Incident management, approve decisions
    │
ANALYST (1)   ─── Create and work on incidents
```

---

## Role Definitions

| Role | Level | Description |
|------|-------|-------------|
| `ADMIN` | 4 | Full access to all features and settings |
| `MANAGER` | 3 | View all data, manage team members |
| `LEAD` | 2 | Manage incidents, approve decisions |
| `ANALYST` | 1 | Create and work on assigned incidents |

---

## Usage

### Typed Dependencies

```python
from src.api.deps import AdminUser, ManagerUser, LeadUser, CurrentUser

# Admin-only endpoint
@router.post("/admin-action")
async def admin_only(current_user: AdminUser):
    # Only admins can access
    pass

# Manager+ endpoint
@router.get("/team-stats")
async def manager_plus(current_user: ManagerUser):
    # Managers and admins can access
    pass

# Lead+ endpoint
@router.delete("/incident/{id}")
async def lead_plus(current_user: LeadUser):
    # Leads, managers, and admins can access
    pass

# Any authenticated user
@router.get("/my-profile")
async def any_user(current_user: CurrentUser):
    # Any authenticated user can access
    pass
```

### Inline Permission Check

```python
from src.models.user import UserRole

@router.get("/conditional")
async def conditional_access(current_user: CurrentUser):
    if current_user.has_permission(UserRole.MANAGER):
        # Show manager data
        return {"data": "manager_data"}
    else:
        # Show limited data
        return {"data": "limited_data"}
```

---

## Protected Endpoints

### Admin Only (AdminUser)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/send` | POST | Send notification to user |
| `/notifications/cleanup` | POST | Clean old notifications |
| `/notifications/email/test` | POST | Test email configuration |
| `/notifications/email/status` | GET | Check email status |
| `/integrations` | POST | Create integration |
| `/integrations/{id}` | PUT | Update integration |
| `/integrations/{id}` | DELETE | Delete integration |
| `/integrations/{id}/enable` | POST | Enable integration |
| `/integrations/{id}/disable` | POST | Disable integration |
| `/integrations/test-connection` | POST | Test connection |
| `/integrations/templates/seed` | POST | Seed templates |
| `/reporting/templates/seed` | POST | Seed report templates |
| `/users/{id}` | PUT | Update user |
| `/users/{id}/deactivate` | POST | Deactivate user |
| `/users/{id}/activate` | POST | Activate user |
| `/users/teams` | POST | Create team |
| `/users/teams/{id}` | PUT/DELETE | Update/delete team |
| `/users/roles` | POST | Create role |
| `/users/roles/{id}` | PUT/DELETE | Update/delete role |
| `/users/invitations` | POST | Create invitation |
| `/users/permissions/seed` | POST | Seed permissions |
| `/users/activity/list` | GET | View activity logs |

### Manager+ (ManagerUser)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/integrations/{id}/sync` | POST | Trigger sync |
| `/reporting/templates` | POST | Create template |
| `/reporting/templates/{id}` | PUT | Update template |
| `/reporting/schedules` | POST | Create schedule |
| `/users` | GET | List users |
| `/users/stats` | GET | User statistics |

### Lead+ (LeadUser)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/incidents/{id}` | DELETE | Delete incident |

---

## Implementation Details

### deps.py

```python
from typing import Annotated
from fastapi import Depends
from src.models.user import User, UserRole

def require_role(required_role: UserRole):
    """Dependency factory for role-based access."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role.value} or higher required"
            )
        return current_user
    return role_checker

# Pre-defined type aliases
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
ManagerUser = Annotated[User, Depends(require_role(UserRole.MANAGER))]
LeadUser = Annotated[User, Depends(require_role(UserRole.LEAD))]
CurrentUser = Annotated[User, Depends(get_current_user)]
```

### user.py

```python
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    LEAD = "lead"
    ANALYST = "analyst"

class User(Base):
    # ...
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.ANALYST
    )

    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher."""
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.MANAGER: 3,
            UserRole.LEAD: 2,
            UserRole.ANALYST: 1,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
```

---

## Files

| File | Purpose |
|------|---------|
| `api/deps.py` | Role dependencies and type aliases |
| `models/user.py` | UserRole enum and permission check |
| `api/v1/*.py` | Endpoint role annotations |

---

## Error Responses

```json
{
  "detail": "Role admin or higher required"
}
```

HTTP Status: `403 Forbidden`

---

## Notes

- Default role for new users is `ANALYST`
- Role is stored in JWT token for quick validation
- Higher roles automatically have all permissions of lower roles
- Use typed dependencies for cleaner code and automatic documentation
