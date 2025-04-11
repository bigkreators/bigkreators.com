"""
Elasticsearch search implementation for the Cryptopedia application.
"""
from typing import Any, Dict, List, Optional
from elasticsearch import AsyncElasticsearch
from .base import SearchInterface

class ElasticsearchSearch(SearchInterface):
    """
    Elasticsearch-based search implementation for production use.
    """
    
    def __init__(self, es_host: str):
        """
        Initialize Elasticsearch connection.
        
        Args:
            es_host: Elasticsearch host URL
        """
        self.es = AsyncElasticsearch([es_host])
    
    async def index(self, index: str, id: str, document: Dict[str, Any]) -> bool:
        """
        Index a document for search.
        
        Args:
            index: The index name
            id: The document ID
            document: The document to index
            
        Returns:
            bool: True if indexing was successful
        """
        try:
            await self.es.index(index=index, id=id, document=document)
            return True
        except Exception as e:
            print(f"Elasticsearch indexing error: {str(e)}")
            return False
    
    async def search(self, index: str, query: str, fields: List[str], from_: int = 0, size: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents using Elasticsearch.
        
        Args:
            index: The index name
            query: The search query
            fields: Fields to search in
            from_: Starting offset
            size: Number of results to return
            
        Returns:
            List[Dict]: List of search results
        """
        try:
            # Build the query
            search_query = {
                "from": from_,
                "size": size,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": fields
                    }
                },
                "highlight": {
                    "fields": {field: {} for field in fields}
                }
            }
            
            # Execute search
            response = await self.es.search(index=index, body=search_query)
            
            # Extract hits
            return [
                {
                    "_id": hit["_id"],
                    "_source": hit["_source"],
                    "_score": hit["_score"],
                    "highlight": hit.get("highlight", {})
                }
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            print(f"Elasticsearch search error: {str(e)}")
            return []
    
    async def update(self, index: str, id: str, document: Dict[str, Any]) -> bool:
        """
        Update an indexed document.
        
        Args:
            index: The index name
            id: The document ID
            document: The updated document fields
            
        Returns:
            bool: True if the update was successful
        """
        try:
            await self.es.update(index=index, id=id, doc=document)
            return True
        except Exception as e:
            print(f"Elasticsearch update error: {str(e)}")
            return False
    
    async def delete(self, index: str, id: str) -> bool:
        """
        Delete a document from the index.
        
        Args:
            index: The index name
            id: The document ID
            
        Returns:
            bool: True if the document was deleted
        """
        try:
            await self.es.delete(index=index, id=id)
            return True
        except Exception as e:
            print(f"Elasticsearch delete error: {str(e)}")
            return False
    
    async def create_index(self, index: str, mappings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a search index with optional mappings.
        
        Args:
            index: The index name
            mappings: Optional index mappings
            
        Returns:
            bool: True if the index was created successfully
        """
        try:
            # Check if index exists
            exists = await self.es.indices.exists(index=index)
            
            if exists:
                return True
            
            # Create index with mappings if provided
            if mappings:
                await self.es.indices.create(index=index, body={"mappings": mappings})
            else:
                await self.es.indices.create(index=index)
                
            return True
        except Exception as e:
            print(f"Elasticsearch create index error: {str(e)}")
            return False
    
    async def close(self) -> None:
        """
        Close the Elasticsearch connection.
        """
        await self.es.close()
