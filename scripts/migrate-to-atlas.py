# File: migrate-to-atlas.py
"""
Automated migration script to move Kryptopedia from local MongoDB to Atlas.
"""

import os
import sys
import asyncio
import argparse
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from bson import ObjectId, json_util
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: Missing dependencies: {e}")
    print("Please run: pip install motor pymongo bson python-dotenv")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AtlasMigration:
    """Handles migration from local MongoDB to Atlas."""
    
    def __init__(self, local_uri: str, local_db: str, atlas_uri: str, atlas_db: str):
        self.local_uri = local_uri
        self.local_db_name = local_db
        self.atlas_uri = atlas_uri
        self.atlas_db_name = atlas_db
        
        self.local_client: Optional[AsyncIOMotorClient] = None
        self.atlas_client: Optional[AsyncIOMotorClient] = None
        self.local_db = None
        self.atlas_db = None
    
    async def connect_local(self):
        """Connect to local MongoDB."""
        try:
            self.local_client = AsyncIOMotorClient(self.local_uri, serverSelectionTimeoutMS=5000)
            await self.local_client.server_info()
            self.local_db = self.local_client[self.local_db_name]
            logger.info(f"✓ Connected to local MongoDB: {self.local_uri}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to local MongoDB: {e}")
            raise
    
    async def connect_atlas(self):
        """Connect to Atlas MongoDB."""
        try:
            self.atlas_client = AsyncIOMotorClient(self.atlas_uri, serverSelectionTimeoutMS=10000)
            await self.atlas_client.admin.command('ping')
            self.atlas_db = self.atlas_client[self.atlas_db_name]
            logger.info(f"✓ Connected to MongoDB Atlas")
        except Exception as e:
            logger.error(f"✗ Failed to connect to Atlas: {e}")
            logger.error("Check your connection string, credentials, and network access settings")
            raise
    
    async def test_connections(self):
        """Test both connections."""
        logger.info("Testing database connections...")
        await self.connect_local()
        await self.connect_atlas()
        logger.info("✓ Both connections successful")
    
    async def get_collection_stats(self, db, db_name: str) -> Dict[str, Any]:
        """Get statistics for all collections in a database."""
        stats = {}
        try:
            collections = await db.list_collection_names()
            
            for collection_name in collections:
                collection = db[collection_name]
                count = await collection.count_documents({})
                
                # Get sample document
                sample = await collection.find_one({})
                
                stats[collection_name] = {
                    "count": count,
                    "sample_fields": list(sample.keys()) if sample else []
                }
            
            return {
                "database": db_name,
                "collections": stats,
                "total_collections": len(collections),
                "total_documents": sum(col["count"] for col in stats.values())
            }
        except Exception as e:
            logger.error(f"Error getting stats for {db_name}: {e}")
            return {}
    
    async def compare_databases(self):
        """Compare local and Atlas databases."""
        logger.info("Comparing databases...")
        
        local_stats = await self.get_collection_stats(self.local_db, "Local")
        atlas_stats = await self.get_collection_stats(self.atlas_db, "Atlas")
        
        print("\n=== Database Comparison ===")
        print(f"Local Database ({self.local_db_name}):")
        print(f"  Collections: {local_stats.get('total_collections', 0)}")
        print(f"  Documents: {local_stats.get('total_documents', 0):,}")
        
        print(f"\nAtlas Database ({self.atlas_db_name}):")
        print(f"  Collections: {atlas_stats.get('total_collections', 0)}")
        print(f"  Documents: {atlas_stats.get('total_documents', 0):,}")
        
        print(f"\nCollection Details:")
        local_collections = local_stats.get('collections', {})
        atlas_collections = atlas_stats.get('collections', {})
        
        all_collections = set(local_collections.keys()) | set(atlas_collections.keys())
        
        for collection in sorted(all_collections):
            local_count = local_collections.get(collection, {}).get('count', 0)
            atlas_count = atlas_collections.get(collection, {}).get('count', 0)
            status = "✓" if local_count == atlas_count else "✗"
            print(f"  {status} {collection}: Local={local_count:,}, Atlas={atlas_count:,}")
        
        return local_stats, atlas_stats
    
    async def migrate_collection(self, collection_name: str, batch_size: int = 1000):
        """Migrate a single collection from local to Atlas."""
        logger.info(f"Migrating collection: {collection_name}")
        
        local_collection = self.local_db[collection_name]
        atlas_collection = self.atlas_db[collection_name]
        
        # Get total count
        total_docs = await local_collection.count_documents({})
        if total_docs == 0:
            logger.info(f"  Collection {collection_name} is empty, skipping")
            return
        
        logger.info(f"  Migrating {total_docs:,} documents in batches of {batch_size}")
        
        # Clear Atlas collection first
        result = await atlas_collection.delete_many({})
        if result.deleted_count > 0:
            logger.info(f"  Cleared {result.deleted_count:,} existing documents from Atlas")
        
        # Migrate in batches
        migrated = 0
        cursor = local_collection.find({})
        
        batch = []
        async for doc in cursor:
            batch.append(doc)
            
            if len(batch) >= batch_size:
                await atlas_collection.insert_many(batch)
                migrated += len(batch)
                logger.info(f"  Progress: {migrated:,}/{total_docs:,} ({migrated/total_docs*100:.1f}%)")
                batch = []
        
        # Insert remaining documents
        if batch:
            await atlas_collection.insert_many(batch)
            migrated += len(batch)
        
        logger.info(f"✓ Completed {collection_name}: {migrated:,} documents migrated")
    
    async def full_migration(self, batch_size: int = 1000):
        """Perform full database migration."""
        logger.info("Starting full database migration...")
        
        await self.connect_local()
        await self.connect_atlas()
        
        # Get collections to migrate
        collections = await self.local_db.list_collection_names()
        
        logger.info(f"Found {len(collections)} collections to migrate: {collections}")
        
        # Migrate each collection
        migration_results = {}
        start_time = datetime.now()
        
        for collection_name in collections:
            try:
                await self.migrate_collection(collection_name, batch_size)
                migration_results[collection_name] = "success"
            except Exception as e:
                logger.error(f"✗ Failed to migrate {collection_name}: {e}")
                migration_results[collection_name] = f"failed: {e}"
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Create migration report
        report = {
            "migration_date": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "source": {
                "uri": self.local_uri,
                "database": self.local_db_name
            },
            "destination": {
                "database": self.atlas_db_name
            },
            "collections_migrated": len([k for k, v in migration_results.items() if v == "success"]),
            "collections_failed": len([k for k, v in migration_results.items() if v != "success"]),
            "results": migration_results
        }
        
        # Save report
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"\n=== Migration Complete ===")
        logger.info(f"Duration: {duration}")
        logger.info(f"Report saved to: {report_file}")
        
        # Final comparison
        await self.compare_databases()
        
        return report
    
    async def create_indexes(self):
        """Create recommended indexes on Atlas."""
        logger.info("Creating indexes on Atlas...")
        
        try:
            # Articles collection indexes
            await self.atlas_db.articles.create_index("slug", unique=True)
            await self.atlas_db.articles.create_index("status")
            await self.atlas_db.articles.create_index("createdAt")
            await self.atlas_db.articles.create_index("categories")
            await self.atlas_db.articles.create_index("tags")
            await self.atlas_db.articles.create_index([("title", "text"), ("content", "text")])
            logger.info("  ✓ Articles indexes created")
            
            # Users collection indexes
            await self.atlas_db.users.create_index("username", unique=True)
            await self.atlas_db.users.create_index("email", unique=True)
            await self.atlas_db.users.create_index("role")
            logger.info("  ✓ Users indexes created")
            
            # Other collections
            await self.atlas_db.revisions.create_index("articleId")
            await self.atlas_db.proposals.create_index("articleId")
            await self.atlas_db.media.create_index("uploadedBy")
            logger.info("  ✓ Additional indexes created")
            
            logger.info("✓ All indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Some indexes may have failed: {e}")
    
    async def close_connections(self):
        """Close database connections."""
        if self.local_client:
            self.local_client.close()
        if self.atlas_client:
            self.atlas_client.close()

async def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Migrate Kryptopedia to MongoDB Atlas")
    parser.add_argument("--atlas-uri", required=True, help="Atlas connection string")
    parser.add_argument("--local-uri", default="mongodb://localhost:27017", help="Local MongoDB URI")
    parser.add_argument("--local-db", default="kryptopedia", help="Local database name")
    parser.add_argument("--atlas-db", default="kryptopedia", help="Atlas database name")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for migration")
    parser.add_argument("--test-only", action="store_true", help="Only test connections")
    parser.add_argument("--compare-only", action="store_true", help="Only compare databases")
    parser.add_argument("--create-indexes", action="store_true", help="Create indexes after migration")
    
    args = parser.parse_args()
    
    # Initialize migration
    migration = AtlasMigration(
        local_uri=args.local_uri,
        local_db=args.local_db,
        atlas_uri=args.atlas_uri,
        atlas_db=args.atlas_db
    )
    
    try:
        if args.test_only:
            await migration.test_connections()
            logger.info("✓ Connection test completed successfully")
            return
        
        if args.compare_only:
            await migration.test_connections()
            await migration.compare_databases()
            return
        
        # Full migration
        await migration.full_migration(args.batch_size)
        
        if args.create_indexes:
            await migration.create_indexes()
        
        logger.info("✓ Migration completed successfully!")
        logger.info("Don't forget to:")
        logger.info("  1. Update your .env file with the Atlas connection string")
        logger.info("  2. Test your application with the new database")
        logger.info("  3. Update any deployment configurations")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        await migration.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
