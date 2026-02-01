"""Redis connection pool for rate limiting and caching."""
import logging
from typing import Optional

from redis.asyncio import Redis, ConnectionPool

from src.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Manages Redis connection pool for the application."""

    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None

    @classmethod
    async def get_client(cls, db: int = 0) -> Redis:
        """Get Redis client with connection pool.

        Args:
            db: Redis database number (default 0, rate limiting uses 1)

        Returns:
            Redis client instance
        """
        if cls._client is None:
            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                db=db,
                max_connections=50,
                decode_responses=True,
            )
            cls._client = Redis(connection_pool=cls._pool)
            logger.info(f"Redis connection pool initialized (db={db})")

        return cls._client

    @classmethod
    async def get_rate_limit_client(cls) -> Redis:
        """Get Redis client specifically for rate limiting (uses separate DB).

        Returns:
            Redis client for rate limiting
        """
        return await cls.get_client(db=settings.RATE_LIMIT_REDIS_DB)

    @classmethod
    async def close(cls) -> None:
        """Close Redis connection pool."""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Redis connection pool closed")

        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None


# Convenience function for getting rate limit client
async def get_redis() -> Redis:
    """Get Redis client for rate limiting."""
    return await RedisManager.get_rate_limit_client()
