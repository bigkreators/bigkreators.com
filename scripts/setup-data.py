#!/usr/bin/env python3
"""
Initialization script for Kryptopedia

This script sets up the required directories and initial data for Kryptopedia.
It creates:
1. Required directories (templates, static, media)
2. Initial demo article
3. Admin user

Usage: python setup-data.py
"""

import os
import sys
import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timedelta
import json
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection info from environment or use defaults
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "kryptopedia")

# Initial demo article content
DEMO_ARTICLE = {
    "title": "Welcome to Kryptopedia",
    "slug": "welcome-to-kryptopedia",
    "content": """
<h1>Welcome to Kryptopedia!</h1>

<p>Kryptopedia is a collaborative knowledge base dedicated to your favorite topics. Our goal is to create a comprehensive resource where enthusiasts and experts can share information, discoveries, and insights.</p>

<h2>What is Kryptopedia?</h2>

<p>Kryptopedia is a wiki-style platform where users can:</p>

<ul>
    <li>Create and edit articles on various topics</li>
    <li>Organize content with categories and tags</li>
    <li>Collaborate through proposals and edits</li>
    <li>Reward valuable contributions</li>
    <li>Upload and share media files</li>
</ul>

<h2>Getting Started</h2>

<p>To get started with Cryptopedia, you can:</p>

<ol>
    <li>Browse existing articles to learn about different topics</li>
    <li>Create an account to contribute your own knowledge</li>
    <li>Edit or improve existing articles</li>
    <li>Propose changes to articles you don't have permission to edit directly</li>
    <li>Create new articles on topics not yet covered</li>
</ol>

<h2>Special Features</h2>

<h3>The Voiceless Uvular Fricative Trill</h3>

<p>As an example of the kind of specialized content Cryptopedia can host, let's talk about the <strong>voiceless uvular fricative trill</strong>.</p>

<p>This is a rare type of consonantal sound used in some spoken languages. The IPA symbol for it is ⟨ʀ̝̊⟩, but since this sound is actually a simultaneous [χ] and [ʀ̥], it can also be transcribed as ⟨χ͡ʀ̥⟩.</p>

<p>Most of the languages that are claimed to have a <strong>voiceless uvular fricative</strong> might actually have a <strong>voiceless uvular fricative trill</strong>, since a complication of uvular fricatives is that the shape of the vocal tract may be such that the uvula vibrates.</p>

<h2>How to Contribute</h2>

<p>Ready to contribute? Here's how:</p>

<ol>
    <li><a href="/create-article">Create a new article</a> on a topic you're knowledgeable about</li>
    <li>Find an existing article and click "Edit" to improve it</li>
    <li>Upload media files like images or audio to enhance articles</li>
    <li>Add categories and tags to help organize content</li>
    <li>Reward other contributors for their valuable additions</li>
</ol>

<p>We're excited to see what knowledge you'll bring to Cryptopedia!</p>
    """,
    "summary": "Introduction to Cryptopedia, its features, and how to contribute",
    "createdAt": datetime.now(),
    "status": "published",
    "categories": ["Introduction", "Help"],
    "tags": ["welcome", "getting started", "tutorial"],
    "views": 0,
    "metadata": {
        "hasAudio": False,
        "hasSpecialSymbols": True,
        "containsMadeUpContent": False
    },
    "featuredUntil": datetime.now() + timedelta(days=30)  # Featured for 30 days
}

# Admin user
ADMIN_USER = {
    "username": "admin",
    "email": "admin@kryptopedia.local",
    "password": "admin123",  # This will be hashed before storage
    "role": "admin",
    "joinDate": datetime.now(),
    "reputation": 100,
    "contributions": {
        "articlesCreated": 1,
        "editsPerformed": 0,
        "rewardsReceived": 0
    }
}

async def init_database(mongo_uri, db_name):
    """Initialize the database with demo content"""
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    # Check if admin user exists
    existing_admin = await db["users"].find_one({"username": ADMIN_USER["username"]})
    if not existing_admin:
        # Hash password
        hashed_password = bcrypt.hashpw(ADMIN_USER["password"].encode('utf-8'), bcrypt.gensalt())
        admin_data = ADMIN_USER.copy()
        admin_data["passwordHash"] = hashed_password.decode('utf-8')
        del admin_data["password"]  # Remove plain password
        
        # Insert admin user
        admin_result = await db["users"].insert_one(admin_data)
        print(f"Created admin user: {ADMIN_USER['username']} (ID: {admin_result.inserted_id})")
        admin_id = admin_result.inserted_id
    else:
        print(f"Admin user already exists: {ADMIN_USER['username']}")
        admin_id = existing_admin["_id"]
    
    # Check if demo article exists
    existing_article = await db["articles"].find_one({"slug": DEMO_ARTICLE["slug"]})
    if not existing_article:
        # Add creator ID to article
        article_data = DEMO_ARTICLE.copy()
        article_data["createdBy"] = admin_id
        
        # Insert demo article
        article_result = await db["articles"].insert_one(article_data)
        print(f"Created demo article: {DEMO_ARTICLE['title']} (ID: {article_result.inserted_id})")
    else:
        print(f"Demo article already exists: {DEMO_ARTICLE['title']}")
    
    # Create indices for collections
    print("Creating database indices...")
    await db["articles"].create_index([("title", "text"), ("content", "text"), ("summary", "text")])
    await db["articles"].create_index([("slug", 1)], unique=True)
    await db["articles"].create_index([("status", 1)])
    await db["articles"].create_index([("categories", 1)])
    await db["articles"].create_index([("tags", 1)])
    
    await db["users"].create_index([("username", 1)], unique=True)
    await db["users"].create_index([("email", 1)], unique=True)
    
    await db["revisions"].create_index([("articleId", 1)])
    await db["proposals"].create_index([("articleId", 1)])
    await db["proposals"].create_index([("status", 1)])
    
    await db["media"].create_index([("filename", 1)], unique=True)
    
    client.close()
    print("Database initialization complete!")

def create_directories():
    """Create required directories"""
    directories = ["templates", "static", "media"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

def check_template_files():
    """Check if template files exist"""
    template_files = [
        "templates/index.html",
        "templates/article.html",
        "templates/articles_list.html",
        "templates/search_results.html",
        "templates/create_article.html",
        "templates/404.html"
    ]
    
    static_files = [
        "static/style.css",
        "static/script.js"
    ]
    
    missing_files = []
    
    for filepath in template_files + static_files:
        if not os.path.exists(filepath):
            missing_files.append(filepath)
    
    if missing_files:
        print("\nWARNING: The following files are missing:")
        for filepath in missing_files:
            print(f"  - {filepath}")
        print("\nMake sure to create these files before starting the application.")
    else:
        print("\nAll required template and static files exist.")

async def main():
    print("\n=== Kryptopedia Initialization ===\n")
    
    # Create directories
    create_directories()
    
    # Initialize database
    try:
        await init_database(MONGO_URI, DB_NAME)
    except Exception as e:
        print(f"\nERROR: Failed to initialize database: {str(e)}")
        print("Make sure MongoDB is running and the connection URI is correct.")
        sys.exit(1)
    
    # Check template files
    check_template_files()
    
    print("\nInitialization complete! You can now start the application.")
    print("Run: python main.py")

if __name__ == "__main__":
    asyncio.run(main())
