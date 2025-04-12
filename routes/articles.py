# File: routes/articles.py
"""
Article-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request, Body
from bson import ObjectId
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models import Article, ArticleCreate, ArticleUpdate
from dependencies import get_db, get_current_user, get_search, get_cache
from utils.slug import generate_slug

# Create router with explicit prefix to avoid routing issues
router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/", response_model=Article, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    search=Depends(get_search)
):
    """
    Create a new article.
    """
    try:
        logger.info(f"Creating article: {article.title}")
        
        # Generate slug from title
        slug = generate_slug(article.title)
        
        # Check if slug already exists
        existing = await db["articles"].find_one({"slug": slug})
        if existing:
            # If slug exists, add a timestamp to make it unique
            from datetime import datetime
            slug = f"{slug}-{int(datetime.now().timestamp())}"
        
        # Create article object
        new_article = {
            "title": article.title,
            "slug": slug,
            "content": article.content,
            "summary": article.summary,
            "createdBy": current_user["_id"],
            "createdAt": datetime.now(),
            "lastUpdatedAt": datetime.now(),
            "lastUpdatedBy": current_user["_id"],
            "status": "published",
            "categories": article.categories,
            "tags": article.tags,
            "views": 0,
            "metadata": article.metadata.dict() if hasattr(article.metadata, "dict") else article.metadata
        }
        
        # Insert into database
        result = await db["articles"].insert_one(new_article)
        logger.info(f"Article created with ID: {result.inserted_id}")
        
        # Update user's contribution count
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$inc": {"contributions.articlesCreated": 1}}
        )
        
        # Index in search
        if search is not None:
            try:
                await search.index(
                    index="articles",
                    id=str(result.inserted_id),
                    document={
                        "title": article.title,
                        "content": article.content,
                        "summary": article.summary,
                        "categories": article.categories,
                        "tags": article.tags,
                        "author": current_user["username"],
                        "created": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error indexing article in search: {e}")
                # Continue even if indexing fails
        
        # Get created article
        created_article = await db["articles"].find_one({"_id": result.inserted_id})
        
        # Clear cache if needed
        try:
            cache = await get_cache()
            await cache.delete("featured_article")
            await cache.delete("recent_articles")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
        
        return created_article
    
    except Exception as e:
        logger.error(f"Error creating article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create article: {str(e)}"
        )

# Rest of your article routes...

# Make sure other API routes are working correctly
@router.get("/", response_model=List[Article])
async def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    tag: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    List articles with optional filtering.
    """
    try:
        # Build the query
        query = {}
        
        # Only show published articles unless status filter is specified
        if status_filter:
            query["status"] = status_filter
        else:
            query["status"] = "published"
        
        if category:
            query["categories"] = category
        
        if tag:
            query["tags"] = tag
        
        # Try to get from cache if simple query
        cache_key = None
        if not category and not tag and status_filter == "published":
            cache_key = f"articles:list:{skip}:{limit}"
            cached = await cache.get(cache_key)
            if cached:
                return cached
        
        # Execute the query
        cursor = db["articles"].find(query).sort("createdAt", -1).skip(skip).limit(limit)
        articles = await cursor.to_list(length=limit)
        
        # Cache the result if using cache key
        if cache_key:
            await cache.set(cache_key, articles, 300)  # Cache for 5 minutes
        
        return articles
    
    except Exception as e:
        logger.error(f"Error listing articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list articles: {str(e)}"
        )
