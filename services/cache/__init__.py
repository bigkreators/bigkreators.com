"""
Cache services package for the Kryptopedia application.
"""
from .base import CacheInterface
from .memory import InMemoryCache
from .redis import RedisCache

__all__ = ['CacheInterface', 'InMemoryCache', 'RedisCache']

def get_cache_service(use_redis: bool = False, **kwargs) -> CacheInterface:
    """
    Factory function to get the appropriate cache service based on configuration.
    
    Args:
        use_redis: Whether to use Redis (True) or in-memory cache (False)
        **kwargs: Additional configuration parameters
        
    Returns:
        CacheInterface: An instance of the appropriate cache service
    """
    if use_redis:
        # Get Redis connection parameters
        host = kwargs.get("redis_host", "localhost")
        port = kwargs.get("redis_port", 6379)
        password = kwargs.get("redis_password")
        db = kwargs.get("redis_db", 0)
        
        return RedisCache(host=host, port=port, password=password, db=db)
    else:
        # Use in-memory cache
        return InMemoryCache()
