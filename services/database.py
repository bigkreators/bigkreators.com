"""
Database service for the Kryptopedia application.
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
        if self.client is not None:  # Changed from 'if self.client:' to avoid bool() evaluation
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    async def create_indices(self):
        """
        Create necessary indices for the application.
        """
        try:
            if self.db is None:  # Changed from 'if not self.db:' to avoid bool() evaluation
                await self.connect()
                
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
