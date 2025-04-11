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

@router.get("", response_model=List[Article])
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get a list of articles with optional filtering by category or tag.
    """
    # Try to get from cache
    cache_key = f"articles:{skip}:{limit}:{category}:{tag}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Build query
    query = {"status": "published"}
    if category:
        query["categories"] = category
    if tag:
        query["tags"] = tag
    
    # Execute query
    cursor = db["articles"].find(query).skip(skip).limit(limit).sort("createdAt", -1)
    articles = await cursor.to_list(length=limit)
    
    # Cache for 5 minutes
    await cache.set(cache_key, articles, 300)
    
    return articles

@router.get("/featured", response_model=Article)
async def get_featured_article(db=Depends(get_db), cache=Depends(get_cache)):
    """
    Get the currently featured article.
    """
    # Try to get from cache
    cached = await cache.get("featured_article")
    if cached:
        return cached
    
    # Get a featured article (featuredUntil > now)
    article = await db["articles"].find_one({
        "featuredUntil": {"$gt": datetime.now()},
        "status": "published"
    })
    
    # If no article is featured, get most viewed article
    if not article:
        article = await db["articles"].find_one(
            {"status": "published"},
            sort=[("views", -1)]
        )
    
    if not article:
        raise HTTPException(status_code=404, detail="No articles found")
    
    # Cache for 1 hour
    await cache.set("featured_article", article, 3600)
    
    return article

@router.get("/random")
async def get_random_article_redirect(db=Depends(get_db)):
    """
    Get a random article and redirect to it.
    """
    from fastapi.responses import RedirectResponse
    
    # Use MongoDB aggregation to get a random article
    pipeline = [
        {"$match": {"status": "published"}},
        {"$sample": {"size": 1}}
    ]
    
    # Execute pipeline
    results = await db["articles"].aggregate(pipeline).to_list(length=1)
    
    if not results:
        raise HTTPException(status_code=404, detail="No articles found")
    
    # Get the random article
    article = results[0]
    
    # Redirect to the article page
    return RedirectResponse(url=f"/articles/{article['slug']}")

@router.get("/{id}", response_model=Article)
async def get_article(
    id: str = Path(..., description="Article ID or slug"),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get a specific article by ID or slug.
    """
    # Try to get from cache
    cache_key = f"article:{id}"
    cached = await cache.get(cache_key)
    if cached:
        # Increment view count in background without awaiting
        db["articles"].update_one(
            {"_id": cached["_id"] if isinstance(cached["_id"], ObjectId) else ObjectId(cached["_id"])},
            {"$inc": {"views": 1}}
        )
        return cached
    
    # Check if ID is valid ObjectId
    if ObjectId.is_valid(id):
        # Find by ID
        article = await db["articles"].find_one({"_id": ObjectId(id)})
    else:
        # Find by slug
        article = await db["articles"].find_one({"slug": id})
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    await db["articles"].update_one(
        {"_id": article["_id"]},
        {"$inc": {"views": 1}}
    )
    
    # Cache for 5 minutes
    await cache.set(cache_key, article, 300)
    
    return article

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
    
    # Index in search
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

@router.put("/{id}", response_model=Article)
async def update_article(
    id: str,
    article_update: ArticleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Update an existing article.
    """
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if user is authorized (admin or original creator)
    if str(article["createdBy"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this article")
    
    # Create update object with only provided fields
    update_data = {}
    
    if article_update.title:
        update_data["title"] = article_update.title
        # Generate new slug if title changes
        update_data["slug"] = generate_slug(article_update.title)
    
    if article_update.content:
        update_data["content"] = article_update.content
    
    if article_update.summary:
        update_data["summary"] = article_update.summary
    
    if article_update.categories:
        update_data["categories"] = article_update.categories
    
    if article_update.tags:
        update_data["tags"] = article_update.tags
    
    if article_update.metadata:
        update_data["metadata"] = article_update.metadata.dict() if hasattr(article_update.metadata, "dict") else article_update.metadata
    
    # Add update metadata
    update_data["lastUpdatedAt"] = datetime.now()
    update_data["lastUpdatedBy"] = current_user["_id"]
    
    # Update article if there are changes
    if update_data:
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        
        # Create a revision
        revision = {
            "articleId": ObjectId(id),
            "content": article_update.content or article["content"],
            "createdBy": current_user["_id"],
            "createdAt": datetime.now(),
            "comment": "Article updated"  # Could be taken from request if needed
        }
        
        await db["revisions"].insert_one(revision)
        
        # Update user's contribution count
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
        
        # Update in search
        await search.update(
            index="articles",
            id=id,
            document={
                "title": article_update.title or article["title"],
                "content": article_update.content or article["content"],
                "summary": article_update.summary or article["summary"],
                "categories": article_update.categories or article["categories"],
                "tags": article_update.tags or article["tags"],
                "updated": datetime.now().isoformat()
            }
        )
        
        # Invalidate cache
        await cache.delete(f"article:{id}")
        await cache.delete(f"article:{article['slug']}")
        if "slug" in update_data:  # If slug changed, invalidate the new slug too
            await cache.delete(f"article:{update_data['slug']}")
    
    # Get updated article
    updated_article = await db["articles"].find_one({"_id": ObjectId(id)})
    return updated_article

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_article(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Delete (or archive) an article.
    """
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Only admins can delete articles
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete articles")
    
    # Mark as archived instead of actually deleting
    await db["articles"].update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": "archived"}}
    )
    
    # Delete from search
    await search.delete(index="articles", id=id)
    
    # Invalidate cache
    await cache.delete(f"article:{id}")
    await cache.delete(f"article:{article['slug']}")
    
    return {"message": "Article archived successfully"}

@router.get("/{id}/history", response_model=List[Dict[str, Any]])
async def get_article_history(
    id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get the revision history of an article.
    """
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get revisions
    cursor = db["revisions"].find({"articleId": ObjectId(id)}).sort("createdAt", -1).skip(skip).limit(limit)
    revisions = await cursor.to_list(length=limit)
    
    # Enhance revisions with user info
    enhanced_revisions = []
    for rev in revisions:
        user = await db["users"].find_one({"_id": rev["createdBy"]})
        enhanced_revisions.append({
            **rev,
            "username": user["username"] if user else "Unknown"
        })
    
    return enhanced_revisions
