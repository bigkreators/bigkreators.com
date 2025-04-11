"""
Search services package for the Cryptopedia application.
"""
from .base import SearchInterface
from .mongo import MongoSearch
from .elasticsearch import ElasticsearchSearch

__all__ = ['SearchInterface', 'MongoSearch', 'ElasticsearchSearch']

def get_search_service(use_elasticsearch: bool = False, **kwargs):
    """
    Factory function to get the appropriate search service based on configuration.
    
    Args:
        use_elasticsearch: Whether to use Elasticsearch (True) or MongoDB text search (False)
        **kwargs: Additional configuration parameters
        
    Returns:
        SearchInterface: An instance of the appropriate search service
        
    Raises:
        ImportError: If Elasticsearch is requested but not available
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
    db = kwargs.get("db")
    if not db:
        raise ValueError("MongoDB database connection required for search")
    
    return MongoSearch(db=db)
