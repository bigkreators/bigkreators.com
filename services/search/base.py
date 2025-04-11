"""
Base interface for search services used in the Cryptopedia application.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class SearchInterface(ABC):
    """
    Abstract interface for search operations.
    Implementations should handle Elasticsearch, MongoDB text search, etc.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def search(self, index: str, query: str, fields: List[str], from_: int = 0, size: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents.
        
        Args:
            index: The index name
            query: The search query
            fields: Fields to search in
            from_: Starting offset
            size: Number of results to return
            
        Returns:
            List[Dict]: List of search results
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def delete(self, index: str, id: str) -> bool:
        """
        Delete a document from the index.
        
        Args:
            index: The index name
            id: The document ID
            
        Returns:
            bool: True if the document was deleted
        """
        pass
    
    @abstractmethod
    async def create_index(self, index: str, mappings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a search index.
        
        Args:
            index: The index name
            mappings: Optional index mappings
            
        Returns:
            bool: True if the index was created successfully
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the search service connection.
        """
        pass
