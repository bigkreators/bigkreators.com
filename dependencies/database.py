"""
Database dependencies for FastAPI.
"""
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import config
from services.database import Database

# Initialize database service
db_service = Database(mongo_uri=config.MONGO_URI, db_name=config.DB_NAME)

async def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency to get the MongoDB database.
    Used in route functions to access the database.
    
    Returns:
        AsyncIOMotorDatabase: The MongoDB database object
    """
    # Ensure database is connected
    if db_service.db is None:
        await db_service.connect()
    
    return db_service.db
