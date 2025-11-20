"""
Redis cache configuration and helper functions.
"""

import json
from typing import Any, Optional
import redis.asyncio as redis

from app.core.config import settings

# Create Redis client
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_redis()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


async def cache_set(
    key: str,
    value: Any,
    ttl: Optional[int] = None
) -> bool:
    """
    Set value in cache.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default from settings)

    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis()
        ttl = ttl or settings.REDIS_TTL_DEFAULT
        serialized = json.dumps(value)
        await client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """
    Delete value from cache.

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


async def cache_exists(key: str) -> bool:
    """
    Check if key exists in cache.

    Args:
        key: Cache key

    Returns:
        True if key exists, False otherwise
    """
    try:
        client = await get_redis()
        return await client.exists(key) > 0
    except Exception as e:
        print(f"Cache exists error: {e}")
        return False


def cache_key(*args: str) -> str:
    """
    Generate cache key from arguments.

    Args:
        *args: Key components

    Returns:
        Cache key string
    """
    return ":".join(args)
