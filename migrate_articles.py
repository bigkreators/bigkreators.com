#!/usr/bin/env python3
# File: migrate_articles.py
"""
Standalone migration script to fix namespace articles.
Run this from the project root directory.
"""
import asyncio
import re
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_title_namespace(full_title: str) -> tuple[str, str]:
    """
    Parse a title to extract namespace and title.
    
    Args:
        full_title: The full title (e.g., "Category:Blockchain" or "Introduction to Crypto")
        
    Returns:
        tuple[str, str]: (namespace, title) - namespace is empty string for main namespace
    """
    valid_namespaces = [
        "Category", "Template", "Help", "User", "File", "Kryptopedia", "Talk"
    ]
    
    if ":" in full_title:
        potential_namespace, title = full_title.split(":", 1)
        if potential_namespace in valid_namespaces:
            return potential_namespace, title.strip()
    
    # No valid namespace found, treat as main namespace
    return "", full_title.strip()

def generate_namespace_slug(namespace: str, title: str) -> str:
    """
    Generate a namespace-aware slug that preserves the namespace:title format.
    
    Args:
        namespace: The namespace (empty string for main namespace)
        title: The title within the namespace
        
    Returns:
        str: The generated namespace-aware slug
    """
    # Clean the title by replacing spaces with underscores and removing problematic chars
    clean_title = title.strip()
    
    # Replace spaces with underscores, preserve parentheses and basic punctuation
    clean_title = re.sub(r'\s+', '_', clean_title)
    # Remove characters that are problematic in URLs but keep colons, parentheses, underscores
    clean_title = re.sub(r'[^\w\(\):.-]', '', clean_title)
    
    if namespace:
        # For namespaced articles, use the format "Namespace:Title"
        slug = f"{namespace}:{clean_title}"
    else:
        # Main namespace articles don't need prefix
        slug = clean_title
    
    return slug

async def migrate_articles():
    """Run the migration."""
    
    # Database connection
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "kryptopedia")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    print("🚀 Starting namespace migration...")
    print(f"📁 Database: {db_name}")
    
    stats = {
        "total_processed": 0,
        "articles_migrated": 0,
        "articles_skipped": 0,
        "errors": []
    }
    
    try:
        # Find articles that might have namespace prefixes in their titles
        articles_cursor = db["articles"].find({
            "title": {"$regex": r"^[A-Za-z]+:", "$options": "i"},
            "$or": [
                {"namespace": {"$exists": False}},
                {"namespace": ""}
            ]
        })
        
        articles = await articles_cursor.to_list(length=None)
        stats["total_processed"] = len(articles)
        
        print(f"📊 Found {len(articles)} articles to potentially migrate")
        
        for article in articles:
            try:
                original_title = article["title"]
                
                # Parse namespace from title
                namespace, new_title = parse_title_namespace(original_title)
                
                # Skip if no valid namespace found
                if not namespace:
                    print(f"⏭️  Skipping: '{original_title}' (no valid namespace)")
                    stats["articles_skipped"] += 1
                    continue
                
                # Generate new slug with namespace
                new_slug = generate_namespace_slug(namespace, new_title)
                
                # Check if new slug already exists (conflict check)
                existing_slug = await db["articles"].find_one({
                    "slug": new_slug,
                    "_id": {"$ne": article["_id"]}
                })
                
                if existing_slug:
                    error_msg = f"Cannot migrate '{original_title}' - target slug '{new_slug}' already exists"
                    stats["errors"].append(error_msg)
                    print(f"❌ {error_msg}")
                    continue
                
                # Update the article
                update_result = await db["articles"].update_one(
                    {"_id": article["_id"]},
                    {
                        "$set": {
                            "title": new_title,
                            "namespace": namespace,
                            "slug": new_slug,
                            "lastUpdatedAt": datetime.now(),
                            "migrated_at": datetime.now(),
                            "migration_note": f"Migrated from '{original_title}' to namespace '{namespace}'"
                        }
                    }
                )
                
                if update_result.modified_count > 0:
                    stats["articles_migrated"] += 1
                    new_url = f"/articles/{new_slug}"
                    print(f"✅ Migrated: '{original_title}' → '{namespace}:{new_title}'")
                    print(f"   New URL: {new_url}")
                else:
                    stats["articles_skipped"] += 1
                    
            except Exception as e:
                error_msg = f"Error migrating article {article.get('_id')}: {str(e)}"
                stats["errors"].append(error_msg)
                print(f"❌ {error_msg}")
        
        # Print final stats
        print(f"\n✅ Migration completed!")
        print(f"   • Total articles processed: {stats['total_processed']}")
        print(f"   • Articles migrated: {stats['articles_migrated']}")
        print(f"   • Articles skipped: {stats['articles_skipped']}")
        print(f"   • Errors: {len(stats['errors'])}")
        
        if stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in stats['errors']:
                print(f"   • {error}")
        
        if stats['articles_migrated'] > 0:
            print(f"\n🎯 Your articles should now be accessible with the correct URLs!")
            print(f"   Example: http://0.0.0.0:8000/articles/Kryptopedia:Rules_(being_merged)")
    
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate_articles())
