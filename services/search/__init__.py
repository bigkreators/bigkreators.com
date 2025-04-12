# File: services/search/__init__.py
"""
Search services package for the Kryptopedia application.
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from .base import SearchInterface
from .mongo import MongoSearch
from .elasticsearch import ElasticsearchSearch

__all__ = ['SearchInterface', 'MongoSearch', 'ElasticsearchSearch']

def get_search_service(use_elasticsearch: bool = False, **kwargs) -> SearchInterface:
    """
    Factory function to get the appropriate search service based on configuration.
    
    Args:
        use_elasticsearch: Whether to use Elasticsearch (True) or MongoDB text search (False)
        **kwargs: Additional configuration parameters
        
    Returns:
        SearchInterface: An instance of the appropriate search service
        
    Raises:
        ImportError: If Elasticsearch is requested but not available
        ValueError: If MongoDB database is required but not provided
    """
    if use_elasticsearch:
        try:
            # Check if elasticsearch is available
            import elasticsearch
            
            # Get Elasticsearch connection parameters
            es_host = kwargs.get("es_host", "http://localhost:9200")
            
            return ElasticsearchSearch(es_host=es_host)
        except ImportError:
            print("Elasticsearch package not available. Falling back to MongoDB search.")
    
    # Fall back to MongoDB search
    # Fix: Don't use boolean evaluation on db
    db = kwargs.get("db")
    if db is None:
        raise ValueError("MongoDB database connection required for search")
    
    # Type check to ensure db is the right type
    if not isinstance(db, AsyncIOMotorDatabase):
        raise ValueError("Database connection must be an AsyncIOMotorDatabase instance")
    
    return MongoSearch(db=db)
