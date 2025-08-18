# File: test/fixed-main-search-import.py
"""
Fixed version of the main search import test file.
"""
import asyncio
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dependencies.database import get_db
from motor.motor_asyncio import AsyncIOMotorClient
import config

async def test_search_import():
    """Test the search import functionality."""
    try:
        # Connect to database
        client = AsyncIOMotorClient(config.MONGO_URI)
        db = client[config.DB_NAME]
        
        # Test database connection
        await client.admin.command('ping')
        print("✅ Database connection successful")
        
        # Test search functionality
        articles = await db["articles"].find({"status": "published"}).limit(5).to_list(length=5)
        print(f"✅ Found {len(articles)} articles")
        
        # Close connection
        client.close()
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_search_import())
    sys.exit(0 if result else 1)

# File: test/generate_sample_changes.py
"""
Generate sample data for testing recent changes functionality.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from bson import ObjectId

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dependencies.database import get_db
from motor.motor_asyncio import AsyncIOMotorClient
import config

async def generate_sample_changes():
    """Generate sample revisions and proposals for testing."""
    try:
        # Connect to database
        client = AsyncIOMotorClient(config.MONGO_URI)
        db = client[config.DB_NAME]
        
        # Test database connection
        await client.admin.command('ping')
        print("✅ Database connection successful")
        
        # Get some sample articles and users
        articles = await db["articles"].find({"status": "published"}).limit(3).to_list(length=3)
        users = await db["users"].find().limit(2).to_list(length=2)
        
        if not articles or not users:
            print("❌ Need at least 3 articles and 2 users to generate sample data")
            return False
        
        # Generate sample revisions
        sample_revisions = []
        for i in range(5):
            revision = {
                "_id": ObjectId(),
                "articleId": articles[i % len(articles)]["_id"],
                "createdBy": users[i % len(users)]["_id"],
                "createdAt": datetime.now() - timedelta(hours=i),
                "summary": f"Sample revision {i+1}",
                "changeType": "edit",
                "content": f"Updated content for revision {i+1}",
                "diff": "Sample diff content"
            }
            sample_revisions.append(revision)
        
        # Insert sample revisions
        if sample_revisions:
            await db["revisions"].insert_many(sample_revisions)
            print(f"✅ Inserted {len(sample_revisions)} sample revisions")
        
        # Generate sample proposals
        sample_proposals = []
        for i in range(3):
            proposal = {
                "_id": ObjectId(),
                "articleId": articles[i % len(articles)]["_id"],
                "proposedBy": users[i % len(users)]["_id"],
                "proposedAt": datetime.now() - timedelta(hours=i+1),
                "summary": f"Sample proposal {i+1}",
                "status": "pending",
                "content": f"Proposed content for proposal {i+1}",
                "reason": f"Reason for proposal {i+1}"
            }
            sample_proposals.append(proposal)
        
        # Insert sample proposals
        if sample_proposals:
            await db["proposals"].insert_many(sample_proposals)
            print(f"✅ Inserted {len(sample_proposals)} sample proposals")
        
        # Close connection
        client.close()
        print("✅ Sample data generation completed successfully")
        
    except Exception as e:
        print(f"❌ Sample data generation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(generate_sample_changes())
    sys.exit(0 if result else 1)

# File: test/setup-test-data.py
"""
Setup test data for the Kryptopedia application.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from bson import ObjectId

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dependencies.database import get_db
from motor.motor_asyncio import AsyncIOMotorClient
from utils.security import hash_password
import config

async def setup_test_data():
    """Setup comprehensive test data for the application."""
    try:
        # Connect to database
        client = AsyncIOMotorClient(config.MONGO_URI)
        db = client[config.DB_NAME]
        
        # Test database connection
        await client.admin.command('ping')
        print("✅ Database connection successful")
        
        # Create test users
        test_users = [
            {
                "_id": ObjectId(),
                "username": "testuser1",
                "email": "test1@example.com",
                "passwordHash": hash_password("password123"),
                "role": "editor",
                "joinDate": datetime.now() - timedelta(days=30),
                "contributions": {
                    "articlesCreated": 5,
                    "editsPerformed": 15
                }
            },
            {
                "_id": ObjectId(),
                "username": "testuser2", 
                "email": "test2@example.com",
                "passwordHash": hash_password("password123"),
                "role": "reader",
                "joinDate": datetime.now() - timedelta(days=15),
                "contributions": {
                    "articlesCreated": 2,
                    "editsPerformed": 8
                }
            }
        ]
        
        # Check if users already exist
        for user in test_users:
            existing_user = await db["users"].find_one({"username": user["username"]})
            if not existing_user:
                await db["users"].insert_one(user)
                print(f"✅ Created test user: {user['username']}")
            else:
                print(f"ℹ️  Test user already exists: {user['username']}")
        
        # Create test articles
        test_articles = [
            {
                "_id": ObjectId(),
                "title": "Test Article 1",
                "slug": "test-article-1",
                "content": "This is the content of test article 1.",
                "status": "published",
                "createdBy": test_users[0]["_id"],
                "createdAt": datetime.now() - timedelta(days=10),
                "views": 150,
                "categories": ["Technology"],
                "tags": ["test", "example"]
            },
            {
                "_id": ObjectId(),
                "title": "Test Article 2",
                "slug": "test-article-2", 
                "content": "This is the content of test article 2.",
                "status": "published",
                "createdBy": test_users[1]["_id"],
                "createdAt": datetime.now() - timedelta(days=5),
                "views": 89,
                "categories": ["Science"],
                "tags": ["test", "science"]
            }
        ]
        
        # Check if articles already exist
        for article in test_articles:
            existing_article = await db["articles"].find_one({"slug": article["slug"]})
            if not existing_article:
                await db["articles"].insert_one(article)
                print(f"✅ Created test article: {article['title']}")
            else:
                print(f"ℹ️  Test article already exists: {article['title']}")
        
        # Create test revisions
        test_revisions = [
            {
                "_id": ObjectId(),
                "articleId": test_articles[0]["_id"],
                "createdBy": test_users[0]["_id"],
                "createdAt": datetime.now() - timedelta(hours=5),
                "summary": "Updated introduction section",
                "changeType": "edit",
                "content": "Updated content for test article 1"
            },
            {
                "_id": ObjectId(),
                "articleId": test_articles[1]["_id"],
                "createdBy": test_users[1]["_id"],
                "createdAt": datetime.now() - timedelta(hours=2),
                "summary": "Fixed typos and added references",
                "changeType": "edit",
                "content": "Updated content for test article 2"
            }
        ]
        
        # Insert test revisions
        for revision in test_revisions:
            existing_revision = await db["revisions"].find_one({"_id": revision["_id"]})
            if not existing_revision:
                await db["revisions"].insert_one(revision)
                print(f"✅ Created test revision for article: {revision['articleId']}")
            else:
                print(f"ℹ️  Test revision already exists for article: {revision['articleId']}")
        
        # Create test proposals
        test_proposals = [
            {
                "_id": ObjectId(),
                "articleId": test_articles[0]["_id"],
                "proposedBy": test_users[1]["_id"],
                "proposedAt": datetime.now() - timedelta(hours=1),
                "summary": "Proposed improvement to article structure",
                "status": "pending",
                "content": "Proposed new content structure",
                "reason": "Better organization of information"
            }
        ]
        
        # Insert test proposals
        for proposal in test_proposals:
            existing_proposal = await db["proposals"].find_one({"_id": proposal["_id"]})
            if not existing_proposal:
                await db["proposals"].insert_one(proposal)
                print(f"✅ Created test proposal for article: {proposal['articleId']}")
            else:
                print(f"ℹ️  Test proposal already exists for article: {proposal['articleId']}")
        
        # Close connection
        client.close()
        print("✅ Test data setup completed successfully")
        
    except Exception as e:
        print(f"❌ Test data setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(setup_test_data())
    sys.exit(0 if result else 1)
