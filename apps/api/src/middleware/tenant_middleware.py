"""Tenant middleware for extracting and setting tenant context."""
from typing import Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from jose import jwt, JWTError

from src.config import settings
from src.core.tenant_context import TenantContext, set_tenant_context, clear_tenant_context


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant information from JWT and set context.

    This middleware:
    1. Extracts the JWT token from the Authorization header
    2. Decodes tenant_id and other context from the token
    3. Sets the TenantContext for the request
    4. Clears context after request completes
    """

    # Paths that don't require tenant context
    EXCLUDED_PATHS: Set[str] = {
        "/health",
        "/",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/sso",
    }

    # Path prefixes that don't require tenant context
    EXCLUDED_PREFIXES: tuple = (
        "/api/v1/auth/sso/",
    )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and set tenant context."""
        # Clear any existing context
        clear_tenant_context()

        # Check if path is excluded
        if not self._is_excluded(request.url.path):
            tenant_context = await self._extract_tenant_context(request)
            if tenant_context:
                set_tenant_context(tenant_context)

        try:
            response = await call_next(request)
            return response
        finally:
            # Always clear context after request
            clear_tenant_context()

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from tenant context requirement."""
        if path in self.EXCLUDED_PATHS:
            return True

        for prefix in self.EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    async def _extract_tenant_context(self, request: Request) -> Optional[TenantContext]:
        """Extract tenant context from JWT token.

        Args:
            request: The incoming request.

        Returns:
            TenantContext if token is valid and contains tenant info, None otherwise.
        """
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Decode JWT without full validation (deps.py will validate)
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Extract tenant info from token
            tenant_id = payload.get("tenant_id")
            user_id = payload.get("sub")
            org_role = payload.get("org_role", "member")
            is_super_admin = payload.get("is_super_admin", False)

            # Super admin can override tenant via header
            if is_super_admin:
                header_tenant = request.headers.get("X-Tenant-ID")
                if header_tenant:
                    tenant_id = header_tenant

            # Require tenant_id for context
            if not tenant_id or not user_id:
                return None

            return TenantContext(
                tenant_id=tenant_id,
                user_id=user_id,
                org_role=org_role,
                is_super_admin=is_super_admin
            )

        except JWTError:
            # Invalid token - let deps.py handle auth errors
            return None
