"""
Article-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request, Body
from bson import ObjectId
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models import Article, ArticleCreate, ArticleUpdate
from dependencies import get_db, get_current_user, get_current_admin, get_current_editor, get_search, get_cache
from utils.slug import generate_slug

# Create router
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

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
            cache = await anext(get_cache())
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

@router.get("/{id}", response_model=Article)
async def get_article(
    id: str,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get an article by ID or slug.
    """
    try:
        # Try to get from cache
        cache_key = f"article:{id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
            
        # Try to find by slug first
        article = await db["articles"].find_one({"slug": id, "status": "published"})
        
        # If not found by slug and ID is a valid ObjectId, try finding by ID
        if not article and ObjectId.is_valid(id):
            article = await db["articles"].find_one({"_id": ObjectId(id)})
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
            
        # Cache for 1 hour
        await cache.set(cache_key, article, 3600)
        
        return article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get article: {str(e)}"
        )

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
    
    # Only allow updates by the creator or admin/editor
    is_creator = str(article["createdBy"]) == str(current_user["_id"])
    is_admin = current_user["role"] == "admin"
    is_editor = current_user["role"] == "editor"
    
    if not (is_creator or is_admin or is_editor):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to update this article"
        )
    
    # Prepare update data
    update_data = {}
    if article_update.title is not None:
        update_data["title"] = article_update.title
    
    if article_update.content is not None:
        update_data["content"] = article_update.content
    
    if article_update.summary is not None:
        update_data["summary"] = article_update.summary
    
    if article_update.categories is not None:
        update_data["categories"] = article_update.categories
    
    if article_update.tags is not None:
        update_data["tags"] = article_update.tags
    
    if article_update.metadata is not None:
        update_data["metadata"] = article_update.metadata.dict() if hasattr(article_update.metadata, "dict") else article_update.metadata
    
    # Don't update if no changes
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    # Update lastUpdatedAt and lastUpdatedBy
    update_data["lastUpdatedAt"] = datetime.now()
    update_data["lastUpdatedBy"] = current_user["_id"]
    
    # Create a revision entry
    revision = {
        "articleId": ObjectId(id),
        "content": update_data.get("content", article["content"]),
        "createdBy": current_user["_id"],
        "createdAt": datetime.now(),
        "comment": article_update.editComment or "Updated article"
    }
    
    # Update the article and create the revision
    try:
        # Start with article update
        result = await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to the article")
        
        # Create revision
        await db["revisions"].insert_one(revision)
        
        # Update user's edit count
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
        
        # Update search index
        if search:
            search_data = {
                "updated": datetime.now().isoformat()
            }
            
            if "content" in update_data:
                search_data["content"] = update_data["content"]
            
            if "title" in update_data:
                search_data["title"] = update_data["title"]
            
            if "summary" in update_data:
                search_data["summary"] = update_data["summary"]
            
            await search.update(
                index="articles",
                id=id,
                document=search_data
            )
        
        # Invalidate cache
        if cache:
            await cache.delete(f"article:{id}")
            if article.get("slug"):
                await cache.delete(f"article:{article['slug']}")
            await cache.delete("featured_article")
            await cache.delete("recent_articles")
        
        # Get updated article
        updated_article = await db["articles"].find_one({"_id": ObjectId(id)})
        
        return updated_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update article: {str(e)}"
        )

@router.delete("/{id}")
async def delete_article(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Delete an article (admin only). Actually marks it as archived.
    """
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Mark as archived instead of actually deleting
    try:
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": {"status": "archived"}}
        )
        
        # Remove from search
        if search:
            await search.delete(
                index="articles",
                id=id
            )
        
        # Invalidate cache
        if cache:
            await cache.delete(f"article:{id}")
            if article.get("slug"):
                await cache.delete(f"article:{article['slug']}")
            await cache.delete("featured_article")
            await cache.delete("recent_articles")
        
        return {"message": "Article archived successfully"}
    
    except Exception as e:
        logger.error(f"Error archiving article: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to archive article: {str(e)}"
        )

@router.get("/{id}/history", response_model=List[Dict[str, Any]])
async def get_article_history(
    id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get revision history for an article.
    """
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get revisions
    try:
        cursor = db["revisions"].find({"articleId": ObjectId(id)}).sort("createdAt", -1).skip(skip).limit(limit)
        revisions = await cursor.to_list(length=limit)
        
        # Enhance with user info
        result = []
        for rev in revisions:
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            username = user["username"] if user else "Unknown"
            
            result.append({
                **rev,
                "creatorUsername": username
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting article history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get article history: {str(e)}"
        )

@router.get("/featured", response_model=Article)
async def get_featured_article(
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get the current featured article.
    """
    try:
        # Try to get from cache
        cached = await cache.get("featured_article")
        if cached:
            return cached
        
        # Find featured articles (featuredUntil > now)
        featured_article = await db["articles"].find_one({
            "featuredUntil": {"$gt": datetime.now()},
            "status": "published"
        })
        
        # If no featured article, get most viewed article
        if not featured_article:
            featured_article = await db["articles"].find_one(
                {"status": "published"},
                sort=[("views", -1)]
            )
        
        if not featured_article:
            raise HTTPException(status_code=404, detail="No featured article found")
        
        # Cache for 1 hour
        await cache.set("featured_article", featured_article, 3600)
        
        return featured_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting featured article: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get featured article: {str(e)}"
        )

@router.get("/random", response_model=Article)
async def get_random_article(db=Depends(get_db)):
    """
    Get a random article.
    """
    try:
        # Use aggregation to get a random article
        pipeline = [
            {"$match": {"status": "published"}},
            {"$sample": {"size": 1}}
        ]
        
        results = await db["articles"].aggregate(pipeline).to_list(length=1)
        
        if not results:
            raise HTTPException(status_code=404, detail="No articles found")
        
        return results[0]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random article: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get random article: {str(e)}"
        )

@router.get("/by-category/{category}", response_model=List[Article])
async def get_articles_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get articles by category.
    """
    try:
        cursor = db["articles"].find(
            {"categories": category, "status": "published"}
        ).sort("createdAt", -1).skip(skip).limit(limit)
        
        articles = await cursor.to_list(length=limit)
        return articles
    
    except Exception as e:
        logger.error(f"Error getting articles by category: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get articles by category: {str(e)}"
        )

@router.get("/by-tag/{tag}", response_model=List[Article])
async def get_articles_by_tag(
    tag: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get articles by tag.
    """
    try:
        cursor = db["articles"].find(
            {"tags": tag, "status": "published"}
        ).sort("createdAt", -1).skip(skip).limit(limit)
        
        articles = await cursor.to_list(length=limit)
        return articles
    
    except Exception as e:
        logger.error(f"Error getting articles by tag: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get articles by tag: {str(e)}"
        )

@router.get("/{id}/revisions/{revision_id}", response_model=Dict[str, Any])
async def get_revision(
    id: str,
    revision_id: str,
    db=Depends(get_db)
):
    """
    Get a specific revision of an article.
    """
    # Check if article exists
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(revision_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get the revision
    revision = await db["revisions"].find_one({
        "_id": ObjectId(revision_id),
        "articleId": ObjectId(id)
    })
    
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")
    
    # Get user info
    user = await db["users"].find_one({"_id": revision["createdBy"]})
    username = user["username"] if user else "Unknown"
    
    return {
        **revision,
        "article": article,
        "creatorUsername": username
    }
