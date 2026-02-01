"""Tenant context management using contextvars.

This module provides thread-safe, async-safe storage for the current
tenant context. The context is set by middleware and accessed by services.
"""
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional


@dataclass
class TenantContext:
    """Container for current tenant context information."""
    tenant_id: str
    user_id: str
    org_role: str = "member"
    is_super_admin: bool = False


# Thread-safe context variable for storing tenant context
_tenant_context: ContextVar[Optional[TenantContext]] = ContextVar(
    'tenant_context',
    default=None
)


def get_current_tenant() -> Optional[TenantContext]:
    """Get the current tenant context.

    Returns:
        TenantContext if set, None otherwise.
    """
    return _tenant_context.get()


def get_current_tenant_id() -> Optional[str]:
    """Get just the current tenant ID.

    Returns:
        Tenant ID string if context is set, None otherwise.
    """
    ctx = _tenant_context.get()
    return ctx.tenant_id if ctx else None


def set_tenant_context(context: TenantContext) -> None:
    """Set the tenant context for the current request.

    Args:
        context: TenantContext instance with tenant details.
    """
    _tenant_context.set(context)


def clear_tenant_context() -> None:
    """Clear the tenant context.

    Should be called at the end of each request to prevent context leakage.
    """
    _tenant_context.set(None)
