"""Rate limiting service using Redis sliding window algorithm."""
import logging
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from redis.asyncio import Redis

from src.core.redis import get_redis
from src.core.rate_limit_config import (
    get_plan_limits,
    get_endpoint_limit,
    UNAUTHENTICATED_LIMIT,
)
from src.models.organization import OrganizationPlan

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp
    retry_after: Optional[int] = None  # Seconds until retry allowed

    @property
    def headers(self) -> dict:
        """Get rate limit headers for response."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(self.reset_at),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class RateLimitService:
    """Service for rate limiting using Redis sliding window."""

    # Key prefixes
    PREFIX_TENANT_HOUR = "ratelimit:sw:tenant:{tenant_id}:hour"
    PREFIX_TENANT_MINUTE = "ratelimit:sw:tenant:{tenant_id}:minute"
    PREFIX_IP = "ratelimit:sw:ip:{ip}:minute"
    PREFIX_ENDPOINT = "ratelimit:sw:endpoint:{path}:ip:{ip}"
    PREFIX_PLAN_CACHE = "ratelimit:meta:{tenant_id}:plan"

    # Window sizes in seconds
    WINDOW_HOUR = 3600
    WINDOW_MINUTE = 60

    def __init__(self, redis: Redis):
        """Initialize service with Redis client.

        Args:
            redis: Redis client instance
        """
        self.redis = redis

    async def check_rate_limit(
        self,
        tenant_id: Optional[str],
        ip: str,
        path: str,
        plan: Optional[OrganizationPlan] = None,
        is_super_admin: bool = False,
    ) -> RateLimitResult:
        """Check if request is within rate limits.

        Checks in order:
        1. Endpoint-specific limits (by IP)
        2. Tenant limits (by plan, hourly + per-minute)
        3. IP limits (for unauthenticated requests)

        Args:
            tenant_id: Organization tenant ID (None if unauthenticated)
            ip: Client IP address
            path: Request path
            plan: Organization's subscription plan
            is_super_admin: Whether user is super admin (bypass if enabled)

        Returns:
            RateLimitResult indicating if request is allowed
        """
        from src.config import settings

        # Check super admin bypass
        if is_super_admin and settings.RATE_LIMIT_BYPASS_SUPER_ADMIN:
            return RateLimitResult(
                allowed=True,
                limit=0,
                remaining=0,
                reset_at=0,
            )

        # 1. Check endpoint-specific limits
        endpoint_limit = get_endpoint_limit(path)
        if endpoint_limit:
            result = await self._check_sliding_window(
                key=self.PREFIX_ENDPOINT.format(path=path.replace("/", "_"), ip=ip),
                limit=endpoint_limit.requests_per_minute,
                window=self.WINDOW_MINUTE,
            )
            if not result.allowed:
                return result

        # 2. Check tenant limits (if authenticated)
        if tenant_id and plan:
            plan_limits = get_plan_limits(plan)

            # Check per-minute limit first (more restrictive)
            minute_result = await self._check_sliding_window(
                key=self.PREFIX_TENANT_MINUTE.format(tenant_id=tenant_id),
                limit=plan_limits.requests_per_minute,
                window=self.WINDOW_MINUTE,
            )
            if not minute_result.allowed:
                return minute_result

            # Check hourly limit
            hour_result = await self._check_sliding_window(
                key=self.PREFIX_TENANT_HOUR.format(tenant_id=tenant_id),
                limit=plan_limits.requests_per_hour,
                window=self.WINDOW_HOUR,
            )
            if not hour_result.allowed:
                return hour_result

            # Return the most restrictive remaining count
            if minute_result.remaining < hour_result.remaining:
                return minute_result
            return hour_result

        # 3. Check unauthenticated IP limits
        return await self._check_sliding_window(
            key=self.PREFIX_IP.format(ip=ip),
            limit=UNAUTHENTICATED_LIMIT.requests_per_minute,
            window=self.WINDOW_MINUTE,
        )

    async def _check_sliding_window(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm with Redis sorted sets.

        The sliding window algorithm:
        1. Remove all entries older than the window
        2. Count remaining entries
        3. If under limit, add new entry with current timestamp
        4. Return result

        Args:
            key: Redis key for this rate limit
            limit: Maximum requests allowed in window
            window: Window size in seconds

        Returns:
            RateLimitResult with current status
        """
        now = time.time()
        window_start = now - window
        reset_at = int(now + window)

        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current entries
        pipe.zcard(key)

        # Execute pipeline
        results = await pipe.execute()
        current_count = results[1]

        remaining = limit - current_count

        if current_count >= limit:
            # Rate limit exceeded
            # Get oldest entry to calculate retry_after
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(oldest_time + window - now) + 1
            else:
                retry_after = window

            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        # Add current request
        await self.redis.zadd(key, {f"{now}": now})
        # Set expiry to prevent memory leaks
        await self.redis.expire(key, window + 60)

        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining - 1,  # Account for current request
            reset_at=reset_at,
        )

    async def get_tenant_usage(
        self,
        tenant_id: str,
    ) -> Tuple[int, int]:
        """Get current usage for a tenant.

        Args:
            tenant_id: Organization tenant ID

        Returns:
            Tuple of (hour_usage, minute_usage)
        """
        now = time.time()

        pipe = self.redis.pipeline()

        # Clean and count hourly
        hour_key = self.PREFIX_TENANT_HOUR.format(tenant_id=tenant_id)
        pipe.zremrangebyscore(hour_key, 0, now - self.WINDOW_HOUR)
        pipe.zcard(hour_key)

        # Clean and count minute
        minute_key = self.PREFIX_TENANT_MINUTE.format(tenant_id=tenant_id)
        pipe.zremrangebyscore(minute_key, 0, now - self.WINDOW_MINUTE)
        pipe.zcard(minute_key)

        results = await pipe.execute()

        return results[1], results[3]

    async def reset_tenant_limits(self, tenant_id: str) -> None:
        """Reset rate limits for a tenant (admin function).

        Args:
            tenant_id: Organization tenant ID
        """
        keys = [
            self.PREFIX_TENANT_HOUR.format(tenant_id=tenant_id),
            self.PREFIX_TENANT_MINUTE.format(tenant_id=tenant_id),
        ]
        if keys:
            await self.redis.delete(*keys)
        logger.info(f"Rate limits reset for tenant {tenant_id}")


async def get_rate_limit_service() -> RateLimitService:
    """Get rate limit service instance.

    Returns:
        RateLimitService with Redis client
    """
    redis = await get_redis()
    return RateLimitService(redis)
