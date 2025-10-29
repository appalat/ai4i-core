"""
Redis caching utilities.

Following the pattern from services/api-gateway-service/main.py
"""

import logging
import json
from typing import Any, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheService:
    """Redis caching utilities."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize cache service with Redis client."""
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache, deserialize JSON."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get from cache {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Store value in cache with TTL, serialize to JSON."""
        try:
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Remove key from cache."""
        try:
            await self.redis.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete from cache {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
                logger.debug(f"Cache delete pattern: {pattern} ({len(keys)} keys)")
                return len(keys)
            return 0
        except Exception as e:
            logger.warning(f"Failed to delete pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Failed to check existence of {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        try:
            ttl = await self.redis.ttl(key)
            return ttl
        except Exception as e:
            logger.warning(f"Failed to get TTL for {key}: {e}")
            return None
    
    async def set_if_not_exists(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set only if key doesn't exist (for distributed locking)."""
        try:
            serialized = json.dumps(value)
            result = await self.redis.set(key, serialized, ex=ttl, nx=True)
            if result:
                logger.debug(f"Cache set (NX): {key}")
            return result
        except Exception as e:
            logger.warning(f"Failed to set_if_not_exists {key}: {e}")
            return False

