# File: db_import_export.py

"""
Database Import/Export Utility for Kryptopedia (Updated for PyMongo 4.x+)

This script provides functionality to export the MongoDB database to JSON files
and import data back from JSON files. Compatible with modern PyMongo versions.

Usage:
    Export: python db_import_export.py export [--collections all|collection1,collection2,...]
    Import: python db_import_export.py import [--collections all|collection1,collection2,...]
    Stats: python db_import_export.py stats
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Handle MongoDB imports with version compatibility
try:
    from bson import ObjectId
    from bson.json_util import dumps, loads, RELAXED_JSON_OPTIONS
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError as e:
    print(f"Error importing MongoDB dependencies: {e}")
    print("Please install required packages:")
    print("pip install motor pymongo")
    sys.exit(1)

# Import config to get MongoDB connection details
try:
    import config
except ImportError:
    print("Error: Cannot import config file. Make sure config.py exists in the current directory.")
    print("You can create it based on the template provided.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_import_export")

# Directory to store exports
EXPORT_DIR = Path("db_exports")

class DatabaseManager:
    """Handle database connections and operations."""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB database."""
        try:
            self.client = AsyncIOMotorClient(config.MONGO_URI)
            self.db = self.client[config.DB_NAME]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {config.DB_NAME}")
            return self.db
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def list_collections(self) -> List[str]:
        """Get list of all collections in the database."""
        try:
            collections = await self.db.list_collection_names()
            return collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

class DataExporter:
    """Handle data export operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db = db_manager.db
    
    async def export_collection(self, collection_name: str, output_dir: Path) -> bool:
        """Export a single collection to JSON file."""
        try:
            logger.info(f"Exporting collection: {collection_name}")
            collection = self.db[collection_name]
            
            # Fetch all documents with proper cursor handling
            documents = []
            async for document in collection.find():
                documents.append(document)
            
            # Create output file
            output_file = output_dir / f"{collection_name}.json"
            
            # Write to file using bson.json_util for proper ObjectId handling
            with open(output_file, 'w', encoding='utf-8') as f:
                json_data = dumps(documents, json_options=RELAXED_JSON_OPTIONS, indent=2)
                f.write(json_data)
            
            logger.info(f"Exported {len(documents)} documents to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export collection {collection_name}: {e}")
            return False
    
    async def export_all_collections(self, specific_collections: Optional[List[str]] = None) -> str:
        """Export all collections or specified ones."""
        collections = await self.db_manager.list_collections()
        if not collections:
            logger.error("No collections found in database")
            return ""
        
        # Filter to specific collections if provided
        if specific_collections and specific_collections != ["all"]:
            collections = [c for c in collections if c in specific_collections]
            not_found = [c for c in specific_collections if c not in collections]
            if not_found:
                logger.warning(f"Collections not found: {', '.join(not_found)}")
        
        logger.info(f"Found {len(collections)} collections to export")
        
        # Create timestamped export directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = EXPORT_DIR / timestamp
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export metadata
        metadata = {
            "timestamp": timestamp,
            "database": config.DB_NAME,
            "collections": collections,
            "exported_at": datetime.now().isoformat(),
            "mongo_uri": config.MONGO_URI.split('@')[-1] if '@' in config.MONGO_URI else config.MONGO_URI  # Hide credentials
        }
        
        metadata_file = export_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Export each collection
        successful = 0
        failed = 0
        for collection_name in collections:
            success = await self.export_collection(collection_name, export_dir)
            if success:
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Export completed: {successful} successful, {failed} failed")
        logger.info(f"Exports saved to {export_dir}")
        
        return str(export_dir)

class DataImporter:
    """Handle data import operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db = db_manager.db
    
    async def import_collection(self, collection_name: str, filepath: Path, clear_existing: bool = False) -> bool:
        """Import a single collection from JSON file."""
        try:
            logger.info(f"Importing collection: {collection_name} from {filepath}")
            collection = self.db[collection_name]
            
            # Read the JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = f.read()
                documents = loads(json_data)
            
            if not documents:
                logger.warning(f"No documents found in {filepath}")
                return True
            
            # Clear existing collection if requested
            if clear_existing:
                result = await collection.delete_many({})
                logger.info(f"Deleted {result.deleted_count} documents from {collection_name}")
            
            # Insert documents
            try:
                if len(documents) == 1:
                    await collection.insert_one(documents[0])
                else:
                    await collection.insert_many(documents, ordered=False)
                
                logger.info(f"Imported {len(documents)} documents to {collection_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to insert documents into {collection_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to import collection {collection_name}: {e}")
            return False
    
    async def import_from_directory(self, directory: Path, specific_collections: Optional[List[str]] = None):
        """Import collections from a directory."""
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return
        
        # Check for metadata file
        metadata_file = directory / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                logger.info(f"Found metadata for export from {metadata.get('exported_at')}")
                logger.info(f"Source database: {metadata.get('database')}")
                available_collections = metadata.get("collections", [])
            except Exception as e:
                logger.error(f"Failed to read metadata: {e}")
                available_collections = []
        else:
            # No metadata, scan for JSON files
            available_collections = [
                f.stem for f in directory.glob("*.json") 
                if f.name != "metadata.json"
            ]
        
        # Filter to specific collections if provided
        if specific_collections and specific_collections != ["all"]:
            collections_to_import = [c for c in available_collections if c in specific_collections]
        else:
            collections_to_import = available_collections
        
        if not collections_to_import:
            logger.error("No collections found to import")
            return
        
        logger.info(f"Found {len(collections_to_import)} collections to import")
        
        # Confirm import
        print(f"\nCollections to import: {', '.join(collections_to_import)}")
        confirm = input("Are you sure you want to proceed with import? This may overwrite existing data. (y/n): ")
        if confirm.lower() != 'y':
            logger.info("Import cancelled")
            return
        
        # Ask about clearing existing data
        clear_all = input("Do you want to clear existing collections before import? (y/n): ")
        clear_existing = clear_all.lower() == 'y'
        
        # Import each collection
        successful = 0
        failed = 0
        for collection_name in collections_to_import:
            file_path = directory / f"{collection_name}.json"
            if not file_path.exists():
                logger.warning(f"File not found for collection {collection_name}: {file_path}")
                continue
            
            success = await self.import_collection(collection_name, file_path, clear_existing)
            if success:
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Import completed: {successful} successful, {failed} failed")

class DatabaseStats:
    """Handle database statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db = db_manager.db
    
    async def display_stats(self):
        """Display comprehensive database statistics."""
        collections = await self.db_manager.list_collections()
        
        if not collections:
            logger.info("No collections found in database")
            return
        
        print(f"\n{'='*60}")
        print(f"Database: {config.DB_NAME}")
        print(f"Total collections: {len(collections)}")
        print(f"{'='*60}")
        print(f"{'Collection':<30} {'Documents':<15} {'Size (approx.)':<15}")
        print(f"{'-'*60}")
        
        total_documents = 0
        for collection_name in sorted(collections):
            try:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                total_documents += count
                
                # Get approximate size by sampling
                size_info = "N/A"
                try:
                    stats = await self.db.command("collStats", collection_name)
                    size_bytes = stats.get("size", 0)
                    if size_bytes > 1024 * 1024:
                        size_info = f"{size_bytes / (1024 * 1024):.1f} MB"
                    elif size_bytes > 1024:
                        size_info = f"{size_bytes / 1024:.1f} KB"
                    else:
                        size_info = f"{size_bytes} B"
                except Exception:
                    pass
                
                print(f"{collection_name:<30} {count:<15} {size_info:<15}")
            except Exception as e:
                print(f"{collection_name:<30} Error: {str(e)}")
        
        print(f"{'-'*60}")
        print(f"{'Total Documents:':<30} {total_documents:<15}")
        print(f"{'='*60}")

def find_latest_export_directory() -> Optional[Path]:
    """Find the most recent export directory."""
    if not EXPORT_DIR.exists():
        return None
    
    timestamp_dirs = []
    for item in EXPORT_DIR.iterdir():
        if item.is_dir():
            try:
                timestamp = datetime.strptime(item.name, "%Y%m%d_%H%M%S")
                timestamp_dirs.append((item, timestamp))
            except ValueError:
                # Skip directories that don't match the timestamp format
                continue
    
    if not timestamp_dirs:
        return None
    
    # Sort by timestamp (newest first)
    timestamp_dirs.sort(key=lambda x: x[1], reverse=True)
    return timestamp_dirs[0][0]

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Kryptopedia Database Import/Export Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python db_import_export.py export
  python db_import_export.py export --collections articles,users
  python db_import_export.py import
  python db_import_export.py import --dir db_exports/20231201_120000
  python db_import_export.py stats
        """
    )
    
    parser.add_argument(
        'action', 
        choices=['export', 'import', 'stats'], 
        help='Action to perform'
    )
    parser.add_argument(
        '--collections', 
        default='all',
        help='Comma-separated list of collections to process (default: all)'
    )
    parser.add_argument(
        '--dir', 
        type=Path,
        help='Directory for import/export (default: auto-detect latest for import)'
    )
    
    args = parser.parse_args()
    
    # Process collections list
    if args.collections == 'all':
        args.collections = ['all']
    else:
        args.collections = [c.strip() for c in args.collections.split(',')]
    
    return args

async def main():
    """Main function."""
    args = parse_arguments()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Connect to database
        await db_manager.connect()
        
        if args.action == 'export':
            logger.info("Starting export process")
            exporter = DataExporter(db_manager)
            export_dir = await exporter.export_all_collections(args.collections)
            print(f"\nExport completed successfully!")
            print(f"Files saved to: {export_dir}")
        
        elif args.action == 'import':
            logger.info("Starting import process")
            importer = DataImporter(db_manager)
            
            import_dir = args.dir
            if not import_dir:
                import_dir = find_latest_export_directory()
                if import_dir:
                    logger.info(f"Using latest export directory: {import_dir}")
                else:
                    logger.error("No export directory specified and couldn't find latest export")
                    return
            
            await importer.import_from_directory(import_dir, args.collections)
        
        elif args.action == 'stats':
            logger.info("Displaying database statistics")
            stats = DatabaseStats(db_manager)
            await stats.display_stats()
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
    finally:
        await db_manager.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)
