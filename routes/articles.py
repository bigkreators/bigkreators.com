# File: routes/articles.py
"""
Article-related routes for the Kryptopedia application.
Complete implementation with all CRUD operations and additional functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request, Body
from bson import ObjectId
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from models import Article, ArticleCreate, ArticleUpdate, ArticleWithCreator
# Import dependencies explicitly to avoid circular imports
from dependencies.database import get_db
from dependencies.auth import get_current_user, get_current_admin, get_current_editor
from dependencies.cache import get_cache
from dependencies.search import get_search
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
            current_time = datetime.now()
            timestamp = int(current_time.timestamp())
            slug = f"{slug}-{timestamp}"
        else:
            current_time = datetime.now()
        
        # Create article object
        new_article = {
            "title": article.title,
            "slug": slug,
            "content": article.content,
            "summary": article.summary,
            "createdBy": current_user["_id"],
            "createdAt": current_time,
            "lastUpdatedAt": current_time,
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
                        "created": current_time.isoformat()
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

@router.get("/count", response_model=Dict[str, int])
async def count_articles(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get count of articles with optional filtering.
    """
    try:
        # Build the query
        query = {}
        
        # Only count published articles unless status filter is specified
        if status_filter:
            query["status"] = status_filter
        else:
            query["status"] = "published"
        
        if category:
            query["categories"] = category
        
        if tag:
            query["tags"] = tag
        
        # Try to get from cache
        cache_key = f"articles:count:{category or 'all'}:{tag or 'all'}:{status_filter or 'published'}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Count articles
        count = await db["articles"].count_documents(query)
        
        result = {"count": count}
        
        # Cache the result
        await cache.set(cache_key, result, 300)  # Cache for 5 minutes
        
        return result
    
    except Exception as e:
        logger.error(f"Error counting articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to count articles: {str(e)}"
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
        cache_key = "featured_article"
        cached = await cache.get(cache_key)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No featured article found"
            )
        
        # Cache the result
        await cache.set(cache_key, featured_article, 3600)  # Cache for 1 hour
        
        return featured_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting featured article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get featured article: {str(e)}"
        )

@router.get("/random", response_model=Article)
async def get_random_article(
    db=Depends(get_db)
):
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found"
            )
        
        return results[0]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get random article: {str(e)}"
        )

@router.get("/{article_id}", response_model=ArticleWithCreator)
async def get_article(
    article_id: str = Path(..., description="Article ID or slug"),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get a specific article by ID or slug.
    """
    try:
        # Try to get from cache
        cache_key = f"article:{article_id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Find the article by ID or slug
        article = None
        
        # Check if article_id is a valid ObjectId
        if ObjectId.is_valid(article_id):
            article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        
        # If not found by ID, try slug
        if not article:
            article = await db["articles"].find_one({"slug": article_id})
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Increment view count
        await db["articles"].update_one(
            {"_id": article["_id"]},
            {"$inc": {"views": 1}}
        )
        
        # Get creator info
        creator = await db["users"].find_one({"_id": article["createdBy"]})
        if creator:
            article["creatorUsername"] = creator["username"]
            article["creatorReputation"] = creator["reputation"]
        else:
            article["creatorUsername"] = "Unknown"
            article["creatorReputation"] = 0
        
        # Cache the result
        await cache.set(cache_key, article, 3600)  # Cache for 1 hour
        
        return article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get article: {str(e)}"
        )

@router.put("/{article_id}", response_model=Article)
async def update_article(
    article_id: str,
    article_update: ArticleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Update an article. User must be the creator, an editor, or an admin.
    """
    try:
        # Check if article exists
        if not ObjectId.is_valid(article_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid article ID"
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Check permissions
        is_creator = str(article["createdBy"]) == str(current_user["_id"])
        is_editor_or_admin = current_user["role"] in ["editor", "admin"]
        
        if not (is_creator or is_editor_or_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this article"
            )
        
        # Build update document
        update_data = {}
        
        # Update fields if provided
        if article_update.title is not None:
            update_data["title"] = article_update.title
            
            # Update slug if title changed
            if article_update.title != article["title"]:
                new_slug = generate_slug(article_update.title)
                
                # Check if new slug already exists
                existing = await db["articles"].find_one({
                    "slug": new_slug,
                    "_id": {"$ne": ObjectId(article_id)}
                })
                
                if existing:
                    # If slug exists, add timestamp
                    timestamp = int(datetime.now().timestamp())
                    new_slug = f"{new_slug}-{timestamp}"
                
                update_data["slug"] = new_slug
        
        if article_update.content is not None:
            update_data["content"] = article_update.content
        
        if article_update.summary is not None:
            update_data["summary"] = article_update.summary
        
        if article_update.categories is not None:
            update_data["categories"] = article_update.categories
        
        if article_update.tags is not None:
            update_data["tags"] = article_update.tags
        
        if article_update.metadata is not None:
            if hasattr(article_update.metadata, "dict"):
                update_data["metadata"] = article_update.metadata.dict()
            else:
                update_data["metadata"] = article_update.metadata
        
        # Add update metadata
        update_data["lastUpdatedAt"] = datetime.now()
        update_data["lastUpdatedBy"] = current_user["_id"]
        
        # Update the article
        await db["articles"].update_one(
            {"_id": ObjectId(article_id)},
            {"$set": update_data}
        )
        
        # Create revision
        revision = {
            "articleId": ObjectId(article_id),
            "content": article_update.content or article["content"],
            "createdBy": current_user["_id"],
            "createdAt": datetime.now(),
            "comment": article_update.editComment or "Updated article"
        }
        
        await db["revisions"].insert_one(revision)
        
        # Update user's contribution count if not the original creator
        if not is_creator:
            await db["users"].update_one(
                {"_id": current_user["_id"]},
                {"$inc": {"contributions.editsPerformed": 1}}
            )
        
        # Update search index
        if search is not None:
            try:
                # Get the updated fields relevant for search
                search_update = {}
                if "title" in update_data:
                    search_update["title"] = update_data["title"]
                if "content" in update_data:
                    search_update["content"] = update_data["content"]
                if "summary" in update_data:
                    search_update["summary"] = update_data["summary"]
                if "categories" in update_data:
                    search_update["categories"] = update_data["categories"]
                if "tags" in update_data:
                    search_update["tags"] = update_data["tags"]
                
                search_update["updated"] = update_data["lastUpdatedAt"].isoformat()
                
                await search.update(
                    index="articles",
                    id=article_id,
                    document=search_update
                )
            except Exception as e:
                logger.error(f"Error updating article in search: {e}")
                # Continue even if search update fails
        
        # Clear cache
        await cache.delete(f"article:{article_id}")
        if "slug" in update_data:
            await cache.delete(f"article:{article['slug']}")
        await cache.delete("recent_articles")
        
        # Get updated article
        updated_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        
        return updated_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update article: {str(e)}"
        )

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin),  # Admin only
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Delete an article (admin only).
    """
    try:
        # Check if article exists
        if not ObjectId.is_valid(article_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid article ID"
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Delete article
        await db["articles"].delete_one({"_id": ObjectId(article_id)})
        
        # Delete all revisions
        await db["revisions"].delete_many({"articleId": ObjectId(article_id)})
        
        # Delete all proposals
        await db["proposals"].delete_many({"articleId": ObjectId(article_id)})
        
        # Delete from search index
        if search is not None:
            try:
                await search.delete(
                    index="articles",
                    id=article_id
                )
            except Exception as e:
                logger.error(f"Error deleting article from search: {e}")
                # Continue even if search deletion fails
        
        # Clear cache
        await cache.delete(f"article:{article_id}")
        await cache.delete(f"article:{article['slug']}")
        await cache.delete("recent_articles")
        await cache.delete("featured_article")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete article: {str(e)}"
        )

@router.get("/{article_id}/history", response_model=List[Dict[str, Any]])
async def get_article_history(
    article_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get revision history for an article.
    """
    try:
        # Check if article exists
        if not ObjectId.is_valid(article_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid article ID"
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Get revisions
        cursor = db["revisions"].find(
            {"articleId": ObjectId(article_id)}
        ).sort("createdAt", -1).skip(skip).limit(limit)
        
        revisions = await cursor.to_list(length=limit)
        
        # Enhance with user info
        enhanced_revisions = []
        for revision in revisions:
            # Get creator info
            creator = await db["users"].find_one({"_id": revision["createdBy"]})
            creator_username = creator["username"] if creator else "Unknown"
            
            # Add to enhanced list
            enhanced_revisions.append({
                **revision,
                "creatorUsername": creator_username
            })
        
        return enhanced_revisions
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get article history: {str(e)}"
        )

@router.get("/{article_id}/revisions/{revision_id}", response_model=Dict[str, Any])
async def get_article_revision(
    article_id: str,
    revision_id: str,
    db=Depends(get_db)
):
    """
    Get a specific revision of an article.
    """
    try:
        # Check if article exists
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(revision_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Get revision
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(article_id)
        })
        
        if not revision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revision not found"
            )
        
        # Get creator info
        creator = await db["users"].find_one({"_id": revision["createdBy"]})
        creator_username = creator["username"] if creator else "Unknown"
        
        # Enhance revision with article info and creator info
        enhanced_revision = {
            **revision,
            "articleTitle": article["title"],
            "creatorUsername": creator_username
        }
        
        return enhanced_revision
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article revision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get article revision: {str(e)}"
        )

@router.post("/{article_id}/revisions/{revision_id}/restore", response_model=Article)
async def restore_article_revision(
    article_id: str,
    revision_id: str,
    comment: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_editor),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Restore an article to a specific revision (editor or admin only).
    """
    try:
        # Check if article exists
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(revision_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Get revision
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(article_id)
        })
        
        if not revision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revision not found"
            )
        
        # Update article with revision content
        current_time = datetime.now()
        await db["articles"].update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {
                "content": revision["content"],
                "lastUpdatedAt": current_time,
                "lastUpdatedBy": current_user["_id"]
            }}
        )
        
        # Create a new revision for this restore
        restore_comment = comment or f"Restored to revision from {revision['createdAt'].strftime('%Y-%m-%d %H:%M')}"
        new_revision = {
            "articleId": ObjectId(article_id),
            "content": revision["content"],
            "createdBy": current_user["_id"],
            "createdAt": current_time,
            "comment": restore_comment
        }
        
        await db["revisions"].insert_one(new_revision)
        
        # Update user's contribution count
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
        
        # Update search index
        if search is not None:
            try:
                await search.update(
                    index="articles",
                    id=article_id,
                    document={
                        "content": revision["content"],
                        "updated": current_time.isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error updating article in search: {e}")
                # Continue even if search update fails
        
        # Clear cache
        await cache.delete(f"article:{article_id}")
        await cache.delete(f"article:{article['slug']}")
        
        # Get updated article
        updated_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        
        return updated_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring article revision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore article revision: {str(e)}"
        )

@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_categories(
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get all categories used in articles with counts.
    """
    try:
        # Try to get from cache
        cache_key = "categories"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Use aggregation to get categories with counts
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        result = await db["articles"].aggregate(pipeline).to_list(None)
        
        # Cache the result
        await cache.set(cache_key, result, 3600)  # Cache for 1 hour
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )

@router.get("/tags", response_model=List[Dict[str, Any]])
async def get_tags(
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get all tags used in articles with counts.
    """
    try:
        # Try to get from cache
        cache_key = "tags"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # Use aggregation to get tags with counts
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        result = await db["articles"].aggregate(pipeline).to_list(None)
        
        # Cache the result
        await cache.set(cache_key, result, 3600)  # Cache for 1 hour
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tags: {str(e)}"
        )

@router.post("/{article_id}/set-featured", response_model=Article)
async def set_featured_article(
    article_id: str,
    days: int = Query(7, ge=1, le=30),
    current_user: Dict[str, Any] = Depends(get_current_admin),  # Admin only
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Set an article as featured for a specified number of days (admin only).
    """
    try:
        # Check if article exists
        if not ObjectId.is_valid(article_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid article ID"
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Set featured until date
        featured_until = datetime.now() + timedelta(days=days)
        
        # Update article
        await db["articles"].update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {"featuredUntil": featured_until}}
        )
        
        # Clear cache
        await cache.delete("featured_article")
        await cache.delete(f"article:{article_id}")
        await cache.delete(f"article:{article['slug']}")
        
        # Get updated article
        updated_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        
        return updated_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting featured article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set featured article: {str(e)}"
        )
