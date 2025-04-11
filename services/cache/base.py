"""
Base interface for caching services used in the Cryptopedia application.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

class CacheInterface(ABC):
    """
    Abstract interface for caching operations.
    Implementations should handle Redis, in-memory, etc.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            Any: The cached value, or None if not found
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if the value was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all cached values.
        
        Returns:
            bool: True if the cache was cleared successfully
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the cache connection.
        """
        pass
