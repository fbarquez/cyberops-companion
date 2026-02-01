"""Rate limiting middleware for API protection."""
import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from jose import jwt, JWTError
from sqlalchemy import select

from src.config import settings
from src.core.rate_limit_config import is_path_excluded
from src.core.redis import get_redis
from src.services.rate_limit_service import RateLimitService
from src.models.organization import OrganizationPlan

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API requests.

    This middleware:
    1. Extracts client IP and tenant info from request
    2. Checks rate limits based on plan/endpoint
    3. Returns 429 if limit exceeded
    4. Adds rate limit headers to all responses
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and check rate limits."""
        # Skip if rate limiting is disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip excluded paths
        if is_path_excluded(request.url.path):
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Extract auth info from JWT
        tenant_id, plan, is_super_admin = await self._extract_auth_info(request)

        try:
            # Get rate limit service
            redis = await get_redis()
            service = RateLimitService(redis)

            # Check rate limit
            result = await service.check_rate_limit(
                tenant_id=tenant_id,
                ip=client_ip,
                path=request.url.path,
                plan=plan,
                is_super_admin=is_super_admin,
            )

            if not result.allowed:
                # Rate limit exceeded - return 429
                logger.warning(
                    f"Rate limit exceeded: ip={client_ip}, tenant={tenant_id}, path={request.url.path}"
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                            "limit": result.limit,
                            "retry_after": result.retry_after,
                            "reset_at": result.reset_at,
                        },
                    },
                    headers=result.headers,
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            for header, value in result.headers.items():
                response.headers[header] = value

            return response

        except Exception as e:
            # Log error but don't block request if rate limiting fails
            logger.error(f"Rate limit check failed: {e}")
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers or connection.

        Handles X-Forwarded-For for proxied requests.

        Args:
            request: The incoming request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP in chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    async def _extract_auth_info(
        self, request: Request
    ) -> tuple[Optional[str], Optional[OrganizationPlan], bool]:
        """Extract tenant and plan info from JWT token.

        Args:
            request: The incoming request

        Returns:
            Tuple of (tenant_id, plan, is_super_admin)
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None, None, False

        token = auth_header[7:]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )

            tenant_id = payload.get("tenant_id")
            is_super_admin = payload.get("is_super_admin", False)

            # Get plan from token or fetch from DB
            plan_str = payload.get("plan")
            if plan_str:
                try:
                    plan = OrganizationPlan(plan_str)
                except ValueError:
                    plan = OrganizationPlan.FREE
            elif tenant_id:
                # Fetch plan from database if not in token
                plan = await self._get_tenant_plan(tenant_id)
            else:
                plan = None

            return tenant_id, plan, is_super_admin

        except JWTError:
            return None, None, False

    async def _get_tenant_plan(self, tenant_id: str) -> OrganizationPlan:
        """Fetch organization plan from database.

        Uses Redis cache to avoid DB queries on every request.

        Args:
            tenant_id: Organization tenant ID

        Returns:
            Organization's subscription plan
        """
        from src.db.database import async_session_maker
        from src.models.organization import Organization

        # Check Redis cache first
        try:
            redis = await get_redis()
            cache_key = f"ratelimit:meta:{tenant_id}:plan"
            cached = await redis.get(cache_key)

            if cached:
                try:
                    return OrganizationPlan(cached)
                except ValueError:
                    pass

            # Fetch from database
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Organization.plan).where(Organization.id == tenant_id)
                )
                row = result.scalar_one_or_none()

                if row:
                    plan = row
                    # Cache for 5 minutes
                    await redis.setex(cache_key, 300, plan.value)
                    return plan

        except Exception as e:
            logger.error(f"Failed to fetch tenant plan: {e}")

        return OrganizationPlan.FREE
