"""Redis cache service for quote data."""
import json
from typing import Optional
from datetime import timedelta

import redis.asyncio as redis

from opa_quotes_api.config import Settings
from opa_quotes_api.logging_setup import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Redis cache service for quote data.
    
    Implements caching strategy:
    - Latest quote: TTL 5 seconds
    - History: TTL 60 seconds
    - Batch: TTL 5 seconds per ticker
    """
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize cache service with Redis client."""
        self.redis = redis_client
        self.default_ttl = 5  # seconds
        self.history_ttl = 60  # seconds
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value as string, or None if not found/expired
        """
        try:
            value = await self.redis.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return value.decode('utf-8') if isinstance(value, bytes) else value
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (JSON string)
            ttl: Time-to-live in seconds (default: 5s)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            await self.redis.setex(key, ttl, value)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key} (result: {result})")
            return result > 0
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., "quote:AAPL:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache INVALIDATE error for pattern {pattern}: {e}")
            return 0
    
    def make_latest_key(self, ticker: str) -> str:
        """Generate cache key for latest quote."""
        return f"quote:{ticker.upper()}:latest"
    
    def make_history_key(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str
    ) -> str:
        """Generate cache key for history query."""
        return f"quote:{ticker.upper()}:history:{start_date}:{end_date}:{interval}"
    
    async def close(self):
        """Close Redis connection."""
        try:
            await self.redis.close()
            logger.info("Cache service closed")
        except Exception as e:
            logger.error(f"Error closing cache service: {e}")
