"""Rate limiting configuration by plan and endpoint."""
from dataclasses import dataclass
from typing import Dict, Optional, Set

from src.models.organization import OrganizationPlan


@dataclass(frozen=True)
class RateLimitTier:
    """Rate limit configuration for a plan tier."""
    requests_per_hour: int
    requests_per_minute: int


@dataclass(frozen=True)
class EndpointRateLimit:
    """Rate limit for specific endpoints (usually per IP)."""
    requests_per_minute: int
    by_ip: bool = True


# Plan-based rate limits
PLAN_LIMITS: Dict[OrganizationPlan, RateLimitTier] = {
    OrganizationPlan.FREE: RateLimitTier(
        requests_per_hour=1000,
        requests_per_minute=60,
    ),
    OrganizationPlan.STARTER: RateLimitTier(
        requests_per_hour=5000,
        requests_per_minute=200,
    ),
    OrganizationPlan.PROFESSIONAL: RateLimitTier(
        requests_per_hour=20000,
        requests_per_minute=500,
    ),
    OrganizationPlan.ENTERPRISE: RateLimitTier(
        requests_per_hour=100000,
        requests_per_minute=2000,
    ),
}

# Endpoint-specific rate limits (path -> limit)
ENDPOINT_LIMITS: Dict[str, EndpointRateLimit] = {
    "/api/v1/auth/login": EndpointRateLimit(requests_per_minute=5, by_ip=True),
    "/api/v1/auth/register": EndpointRateLimit(requests_per_minute=3, by_ip=True),
    "/api/v1/auth/forgot-password": EndpointRateLimit(requests_per_minute=3, by_ip=True),
    "/api/v1/auth/reset-password": EndpointRateLimit(requests_per_minute=5, by_ip=True),
}

# Rate limit for unauthenticated requests (per IP)
UNAUTHENTICATED_LIMIT = EndpointRateLimit(requests_per_minute=30, by_ip=True)

# Paths excluded from rate limiting
EXCLUDED_PATHS: Set[str] = {
    "/health",
    "/",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
}

# Path prefixes excluded from rate limiting
EXCLUDED_PREFIXES: tuple = (
    "/api/v1/ws/",  # WebSocket connections
)


def get_plan_limits(plan: OrganizationPlan) -> RateLimitTier:
    """Get rate limits for a subscription plan.

    Args:
        plan: Organization's subscription plan

    Returns:
        RateLimitTier with requests_per_hour and requests_per_minute
    """
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[OrganizationPlan.FREE])


def get_endpoint_limit(path: str) -> Optional[EndpointRateLimit]:
    """Get specific rate limit for an endpoint.

    Args:
        path: Request path

    Returns:
        EndpointRateLimit if endpoint has specific limits, None otherwise
    """
    return ENDPOINT_LIMITS.get(path)


def is_path_excluded(path: str) -> bool:
    """Check if path is excluded from rate limiting.

    Args:
        path: Request path

    Returns:
        True if path should be excluded from rate limiting
    """
    if path in EXCLUDED_PATHS:
        return True

    for prefix in EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return True

    return False
