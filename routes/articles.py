"""
Article-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from bson import ObjectId
from typing import List, Optional, Dict, Any
from datetime import datetime

from models import Article, ArticleCreate, ArticleUpdate
from dependencies import get_db, get_current_user, get_search, get_cache
from utils.slug import generate_slug

router = APIRouter()

@router.post("", response_model=Article, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    search=Depends(get_search)
):
    """
    Create a new article.
    """
    # Generate slug from title
    slug = generate_slug(article.title)
    
    # Create article object
    new_article = {
        "title": article.title,
        "slug": slug,
        "content": article.content,
        "summary": article.summary,
        "createdBy": current_user["_id"],
        "createdAt": datetime.now(),
        "status": "published",
        "categories": article.categories,
        "tags": article.tags,
        "views": 0,
        "metadata": article.metadata.dict() if hasattr(article.metadata, "dict") else article.metadata
    }
    
    # Insert into database
    result = await db["articles"].insert_one(new_article)
    
    # Update user's contribution count
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"contributions.articlesCreated": 1}}
    )
    
    # Index in search - check if search service exists
    if search is not None:  # <- Changed from implicit boolean check to explicit None check
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
    
    # Get created article
    created_article = await db["articles"].find_one({"_id": result.inserted_id})
    return created_article
