"""
In-memory cache implementation for the Cryptopedia application.
"""
from datetime import datetime, timedelta
import copy
import json
from typing import Any, Dict, Optional
from .base import CacheInterface

class InMemoryCache(CacheInterface):
    """
    Simple in-memory cache implementation for development or small deployments.
    """
    # Class level storage to persist across instances
    _cache = {}
    _expiry = {}
    
    def __init__(self):
        """
        Initialize the in-memory cache.
        """
        # Use class-level variables for storage
        # This allows the cache to persist across instances
        pass
    
    async def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            Any: The cached value, or None if not found/expired
        """
        if key in self._cache:
            # Check if expired
            if key in self._expiry and self._expiry[key] < datetime.now():
                # Expired, remove and return None
                await self.delete(key)
                return None
                
            # Try to deserialize JSON strings
            value = self._cache[key]
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Not JSON, return as is
                    return value
            
            # Make a deep copy to avoid modifying the cached value
            return copy.deepcopy(value)
            
        return None
    
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
        # Try to serialize non-primitive types to JSON
        if isinstance(value, (dict, list, tuple, set)):
            try:
                value = json.dumps(value)
            except (TypeError, ValueError):
                # If serialization fails, store as is
                pass
        
        self._cache[key] = value
        
        if expiration:
            self._expiry[key] = datetime.now() + timedelta(seconds=expiration)
        elif key in self._expiry:
            # Remove expiration if no longer needed
            del self._expiry[key]
        
        return True
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if the value was deleted, False if key not found
        """
        if key in self._cache:
            del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
            
        return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if the key exists and is not expired
        """
        if key in self._cache:
            # Check if expired
            if key in self._expiry and self._expiry[key] < datetime.now():
                await self.delete(key)
                return False
            return True
            
        return False
    
    async def clear(self) -> bool:
        """
        Clear all cached values.
        
        Returns:
            bool: True always
        """
        self._cache.clear()
        self._expiry.clear()
        return True
    
    async def close(self) -> None:
        """
        Close the cache connection.
        For in-memory cache, this is a no-op.
        """
        pass
    
    async def cleanup_expired(self) -> int:
        """
        Delete all expired keys.
        
        Returns:
            int: Number of keys deleted
        """
        now = datetime.now()
        expired_keys = [k for k, exp in self._expiry.items() if exp < now]
        
        count = 0
        for key in expired_keys:
            if await self.delete(key):
                count += 1
                
        return count
