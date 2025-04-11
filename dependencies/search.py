"""
Search dependencies for FastAPI.
"""
from fastapi import Depends
import config
from dependencies.database import get_db
from services.search import get_search_service, SearchInterface

async def get_search(db=Depends(get_db)) -> SearchInterface:
    """
    Dependency to get the search service.
    Used in route functions that need search capabilities.
    
    Args:
        db: MongoDB database dependency
        
    Returns:
        SearchInterface: The search service
    """
    # Create search service based on configuration
    search_service = get_search_service(
        use_elasticsearch=config.USE_ELASTICSEARCH,
        es_host=config.ES_HOST,
        db=db
    )
    
    try:
        yield search_service
    finally:
        await search_service.close()
