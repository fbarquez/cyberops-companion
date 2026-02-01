"""API dependencies."""
from typing import Annotated, Optional, Tuple

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.user import User, UserRole
from src.core.tenant_context import TenantContext, set_tenant_context, get_current_tenant
from src.services.auth_service import AuthService


security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from JWT token."""
    auth_service = AuthService(db)
    token = credentials.credentials

    payload = auth_service.decode_token(token)
    if not payload or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_user_with_tenant(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_tenant_id: Annotated[Optional[str], Header()] = None,
) -> Tuple[User, TenantContext]:
    """Get current user with tenant context.

    This dependency:
    1. Validates the JWT token
    2. Extracts tenant_id from token (or X-Tenant-ID header for super admins)
    3. Sets up the TenantContext for the request
    4. Returns both user and context

    Super admins can override the tenant via X-Tenant-ID header.
    """
    auth_service = AuthService(db)
    token = credentials.credentials

    payload = auth_service.decode_token(token)
    if not payload or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Determine tenant_id
    tenant_id = payload.tenant_id

    # Super admin can override tenant via header
    if x_tenant_id and user.is_super_admin:
        tenant_id = x_tenant_id
    elif x_tenant_id and not user.is_super_admin:
        # Non-super admin trying to use X-Tenant-ID
        if x_tenant_id not in (payload.available_tenants or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this tenant",
            )
        tenant_id = x_tenant_id

    # Create tenant context
    context = TenantContext(
        tenant_id=tenant_id or "",
        user_id=user.id,
        org_role=payload.org_role or "member",
        is_super_admin=user.is_super_admin
    )

    # Set context for this request
    set_tenant_context(context)

    return user, context


def require_role(required_role: UserRole):
    """Dependency to require a minimum role level."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role.value} or higher required",
            )
        return current_user
    return role_checker


def require_super_admin():
    """Dependency to require super admin status."""
    async def super_admin_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required",
            )
        return current_user
    return super_admin_checker


def require_org_role(required_roles: list):
    """Dependency to require specific organization roles.

    Args:
        required_roles: List of allowed org roles (e.g., ["owner", "admin"])
    """
    async def org_role_checker(
        user_context: Annotated[Tuple[User, TenantContext], Depends(get_current_user_with_tenant)]
    ) -> Tuple[User, TenantContext]:
        user, context = user_context

        # Super admin bypasses org role check
        if context.is_super_admin:
            return user, context

        if context.org_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Organization role {required_roles} required",
            )
        return user, context
    return org_role_checker


# Type aliases for common dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
ManagerUser = Annotated[User, Depends(require_role(UserRole.MANAGER))]
LeadUser = Annotated[User, Depends(require_role(UserRole.LEAD))]
SuperAdminUser = Annotated[User, Depends(require_super_admin())]
UserWithTenant = Annotated[Tuple[User, TenantContext], Depends(get_current_user_with_tenant)]
OrgAdmin = Annotated[Tuple[User, TenantContext], Depends(require_org_role(["owner", "admin"]))]
