"""
MongoDB text search implementation for the Cryptopedia application.
"""
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from .base import SearchInterface

class MongoSearch(SearchInterface):
    """
    Simple search implementation using MongoDB text search.
    Used as a fallback when Elasticsearch is not available.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize MongoDB search with a database connection.
        
        Args:
            db: AsyncIOMotorDatabase instance
        """
        self.db = db
    
    async def index(self, index: str, id: str, document: Dict[str, Any]) -> bool:
        """
        Index a document for search.
        In MongoDB, this just means storing the document.
        
        Args:
            index: The collection name
            id: The document ID
            document: The document to index
            
        Returns:
            bool: True if indexing was successful
        """
        try:
            # Convert string ID to ObjectId if valid
            try:
                if ObjectId.is_valid(id):
                    document_id = ObjectId(id)
                else:
                    document_id = id
            except:
                document_id = id
            
            # Set the _id field
            document['_id'] = document_id
            
            # Try to insert, if it fails, update
            try:
                await self.db[index].insert_one(document)
            except:
                await self.db[index].replace_one({'_id': document_id}, document, upsert=True)
                
            return True
        except Exception as e:
            print(f"MongoDB indexing error: {str(e)}")
            return False
    
    async def search(self, index: str, query: str, fields: List[str], from_: int = 0, size: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents using MongoDB text search.
        
        Args:
            index: The collection name
            query: The search query
            fields: Fields to search in (ignored in MongoDB text search)
            from_: Starting offset
            size: Number of results to return
            
        Returns:
            List[Dict]: List of search results
        """
        try:
            # MongoDB text search
            cursor = self.db[index].find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).skip(from_).limit(size)
            
            results = await cursor.to_list(length=size)
            
            # Format results to match Elasticsearch-like response
            return [
                {
                    "_id": str(doc["_id"]),
                    "_source": {k: v for k, v in doc.items() if k != "_id"}
                }
                for doc in results
            ]
        except Exception as e:
            print(f"MongoDB search error: {str(e)}")
            return []
    
    async def update(self, index: str, id: str, document: Dict[str, Any]) -> bool:
        """
        Update an indexed document.
        
        Args:
            index: The collection name
            id: The document ID
            document: The updated document fields
            
        Returns:
            bool: True if the update was successful
        """
        try:
            # Convert string ID to ObjectId if valid
            try:
                if ObjectId.is_valid(id):
                    document_id = ObjectId(id)
                else:
                    document_id = id
            except:
                document_id = id
            
            # Update the document
            result = await self.db[index].update_one(
                {'_id': document_id},
                {'$set': document}
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"MongoDB update error: {str(e)}")
            return False
    
    async def delete(self, index: str, id: str) -> bool:
        """
        Delete a document from the index.
        
        Args:
            index: The collection name
            id: The document ID
            
        Returns:
            bool: True if the document was deleted
        """
        try:
            # Convert string ID to ObjectId if valid
            try:
                if ObjectId.is_valid(id):
                    document_id = ObjectId(id)
                else:
                    document_id = id
            except:
                document_id = id
            
            # Delete the document
            result = await self.db[index].delete_one({'_id': document_id})
            
            return result.deleted_count > 0
        except Exception as e:
            print(f"MongoDB delete error: {str(e)}")
            return False
    
    async def create_index(self, index: str, mappings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a text index for the collection.
        
        Args:
            index: The collection name
            mappings: Fields to include in the text index
            
        Returns:
            bool: True if the index was created successfully
        """
        try:
            if mappings and 'properties' in mappings:
                # Get text indexed fields from mappings
                text_fields = [
                    field for field, config in mappings['properties'].items()
                    if config.get('type') == 'text'
                ]
                
                # Create text index on specified fields
                if text_fields:
                    index_spec = [(field, 'text') for field in text_fields]
                    await self.db[index].create_index(index_spec)
                    return True
            
            # Default to indexing all string fields
            await self.db[index].create_index([('$**', 'text')])
            return True
        except Exception as e:
            print(f"MongoDB create index error: {str(e)}")
            return False
    
    async def close(self) -> None:
        """
        Close the search service connection.
        For MongoDB, this is a no-op as the connection is managed elsewhere.
        """
        pass
