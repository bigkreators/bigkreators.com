"""
Redis cache implementation for the Cryptopedia application.
"""
import json
from typing import Any, Optional, Union
import redis.asyncio as redis
from .base import CacheInterface

class RedisCache(CacheInterface):
    """
    Redis-based cache implementation for production use.
    """
    
    def __init__(self, host: str, port: int, password: Optional[str] = None, db: int = 0):
        """
        Initialize the Redis cache.
        
        Args:
            host: Redis server host
            port: Redis server port
            password: Optional Redis password
            db: Redis database number
        """
        self.redis = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=False  # Keep binary data as is
        )
    
    async def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            Any: The cached value, or None if not found
        """
        value = await self.redis.get(key)
        
        if value is None:
            return None
        
        # Try to decode as UTF-8 string
        try:
            value = value.decode('utf-8')
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Not JSON, return as is
                return value
                
        except UnicodeDecodeError:
            # Binary data, return as is
            return value
    
    async def set(self, key: str, value: Any, expiration: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            expiration: Optional expiration time in seconds
            
        Returns:
            bool: True if the value was set successfully
        """
        # Serialize complex types to JSON
        if isinstance(value, (dict, list, tuple, set)):
            try:
                value = json.dumps(value)
            except (TypeError, ValueError):
                # If serialization fails, convert to string
                value = str(value)
        
        # If value is a string, encode to bytes
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        # Set in Redis with optional expiration
        result = await self.redis.set(key, value, ex=expiration)
        return result is True
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if the value was deleted, False if key not found
        """
        result = await self.redis.delete(key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if the key exists
        """
        result = await self.redis.exists(key)
        return result > 0
    
    async def clear(self) -> bool:
        """
        Clear all cached values.
        WARNING: This will flush the entire Redis database.
        
        Returns:
            bool: True if the operation was successful
        """
        result = await self.redis.flushdb()
        return result is True
    
    async def close(self) -> None:
        """
        Close the Redis connection.
        """
        await self.redis.close()
