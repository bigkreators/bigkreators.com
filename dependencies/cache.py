"""
Cache dependencies for FastAPI.
"""
import config
from services.cache import get_cache_service, CacheInterface

# Create cache service based on configuration
cache_service = get_cache_service(
    use_redis=config.USE_REDIS,
    redis_host=config.REDIS_HOST,
    redis_port=config.REDIS_PORT
)

async def get_cache() -> CacheInterface:
    """
    Dependency to get the cache service.
    Used in route functions that need caching.
    
    Returns:
        CacheInterface: The cache service
    """
    return cache_service
