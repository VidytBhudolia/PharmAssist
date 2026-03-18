"""Simple TTL cache layer with optional Redis fallback."""

import time
from typing import Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class CacheLayer:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, redis_client=None):
        """
        Initialize cache layer.
        
        Args:
            redis_client: Optional Redis client for distributed caching
        """
        self._cache = {}
        self._expiry = {}
        self._redis = redis_client
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        # Try Redis first if available
        if self._redis:
            try:
                value = self._redis.get(key)
                if value:
                    logger.debug(f"Cache hit (Redis): {key}")
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Try in-memory cache
        if key in self._cache:
            expiry_time = self._expiry.get(key, 0)
            if time.time() < expiry_time:
                logger.debug(f"Cache hit (memory): {key}")
                return self._cache[key]
            else:
                # Expired, clean up
                del self._cache[key]
                del self._expiry[key]
                logger.debug(f"Cache expired: {key}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 600):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default 600 = 10 minutes)
        """
        # Store in Redis if available
        if self._redis:
            try:
                self._redis.setex(key, ttl_seconds, json.dumps(value))
                logger.debug(f"Cached to Redis: {key} (TTL: {ttl_seconds}s)")
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        
        # Always store in memory as fallback
        self._cache[key] = value
        self._expiry[key] = time.time() + ttl_seconds
        logger.debug(f"Cached to memory: {key} (TTL: {ttl_seconds}s)")
    
    def clear(self, key: Optional[str] = None):
        """
        Clear cache entry or all entries.
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            if self._redis:
                try:
                    self._redis.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete failed: {e}")
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            logger.debug(f"Cleared cache: {key}")
        else:
            if self._redis:
                try:
                    self._redis.flushdb()
                except Exception as e:
                    logger.warning(f"Redis flush failed: {e}")
            self._cache.clear()
            self._expiry.clear()
            logger.debug("Cleared all cache")


# Global cache instance
_global_cache = CacheLayer()


def get_cache() -> CacheLayer:
    """Get the global cache instance."""
    return _global_cache


def get(key: str) -> Optional[Any]:
    """Get value from global cache."""
    return _global_cache.get(key)


def set(key: str, value: Any, ttl_seconds: int = 600):
    """Set value in global cache."""
    _global_cache.set(key, value, ttl_seconds)


def clear(key: Optional[str] = None):
    """Clear global cache entry or all entries."""
    _global_cache.clear(key)
