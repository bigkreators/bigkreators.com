"""
Database service for the Cryptopedia application.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, TEXT
from pymongo.errors import DuplicateKeyError
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class Database:
    """
    Database service for MongoDB operations.
    """
    def __init__(self, mongo_uri: str, db_name: str):
        """
        Initialize database connection.
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
        """
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.mongo_uri = mongo_uri
        self.db_name = db_name
    
    async def connect(self):
        """
        Connect to the MongoDB database.
        """
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            logger.info(f"Connected to MongoDB database: {self.db_name}")
            
            # Create indices when connecting
            await self.create_indices()
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise
    
    async def close(self):
        """
        Close the MongoDB connection.
        """
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    async def create_indices(self):
        """
        Create necessary indices for the application.
        """
        try:
            # Articles collection indices
            await self.db["articles"].create_index([("title", TEXT), ("content", TEXT), ("summary", TEXT)])
            await self.db["articles"].create_index([("slug", ASCENDING)], unique=True)
            await self.db["articles"].create_index([("status", ASCENDING)])
            await self.db["articles"].create_index([("createdAt", ASCENDING)])
            await self.db["articles"].create_index([("categories", ASCENDING)])
            await self.db["articles"].create_index([("tags", ASCENDING)])
            
            # Users collection indices
            await self.db["users"].create_index([("username", ASCENDING)], unique=True)
            await self.db["users"].create_index([("email", ASCENDING)], unique=True)
            
            # Revisions collection indices
            await self.db["revisions"].create_index([("articleId", ASCENDING)])
            await self.db["revisions"].create_index([("createdAt", ASCENDING)])
            
            # Proposals collection indices
            await self.db["proposals"].create_index([("articleId", ASCENDING)])
            await self.db["proposals"].create_index([("status", ASCENDING)])
            
            # Media collection indices
            await self.db["media"].create_index([("filename", ASCENDING)], unique=True)
            
            # Rewards collection indices
            await self.db["rewards"].create_index([("articleId", ASCENDING)])
            
            logger.info("Created MongoDB indices")
        except Exception as e:
            logger.error(f"Error creating MongoDB indices: {str(e)}")
            raise
    
    async def get_random_article(self) -> Optional[Dict[str, Any]]:
        """
        Get a random published article.
        
        Returns:
            Dict or None: A random article document or None if no articles exist
        """
        # Use MongoDB aggregation to get a random article
        pipeline = [
            {"$match": {"status": "published"}},
            {"$sample": {"size": 1}}
        ]
        
        # Execute pipeline
        results = await self.db["articles"].aggregate(pipeline).to_list(length=1)
        
        if not results:
            return None
        
        return results[0]
    
    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document in a collection.
        
        Args:
            collection: Collection name
            query: Query dictionary
            
        Returns:
            Dict or None: The found document or None
        """
        return await self.db[collection].find_one(query)
    
    async def find_many(self, 
                       collection: str, 
                       query: Dict[str, Any], 
                       skip: int = 0, 
                       limit: int = 100, 
                       sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """
        Find multiple documents in a collection.
        
        Args:
            collection: Collection name
            query: Query dictionary
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: Sort specification [(field, direction), ...]
            
        Returns:
            List: List of found documents
        """
        cursor = self.db[collection].find(query).skip(skip).limit(limit)
        
        if sort:
            cursor = cursor.sort(sort)
        
        return await cursor.to_list(length=limit)
    
    async def count(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Count documents in a collection.
        
        Args:
            collection: Collection name
            query: Query dictionary
            
        Returns:
            int: Count of matching documents
        """
        return await self.db[collection].count_documents(query)
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a document into a collection.
        
        Args:
            collection: Collection name
            document: Document to insert
            
        Returns:
            Dict: The inserted document with _id
            
        Raises:
            DuplicateKeyError: If the document violates a unique constraint
        """
        try:
            result = await self.db[collection].insert_one(document)
            document['_id'] = result.inserted_id
            return document
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error inserting document: {str(e)}")
            raise
    
    async def update_one(self, 
                        collection: str, 
                        query: Dict[str, Any], 
                        update: Dict[str, Any],
                        upsert: bool = False) -> bool:
        """
        Update a document in a collection.
        
        Args:
            collection: Collection name
            query: Query to identify the document
            update: Update operations
            upsert: Whether to insert if document doesn't exist
            
        Returns:
            bool: True if a document was modified, False otherwise
        """
        result = await self.db[collection].update_one(query, update, upsert=upsert)
        return result.modified_count > 0
    
    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """
        Delete a document from a collection.
        
        Args:
            collection: Collection name
            query: Query to identify the document
            
        Returns:
            bool: True if a document was deleted, False otherwise
        """
        result = await self.db[collection].delete_one(query)
        return result.deleted_count > 0
    
    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]], limit: int = None) -> List[Dict[str, Any]]:
        """
        Perform an aggregation pipeline query.
        
        Args:
            collection: Collection name
            pipeline: Aggregation pipeline
            limit: Maximum number of results to return
            
        Returns:
            List: Aggregation results
        """
        cursor = self.db[collection].aggregate(pipeline)
        return await cursor.to_list(length=limit)
