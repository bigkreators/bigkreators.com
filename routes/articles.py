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
            # Add a number suffix to make it unique
            counter = 1
            while existing:
                new_slug = f"{slug}-{counter}"
                existing = await db["articles"].find_one({"slug": new_slug})
                counter += 1
            slug = new_slug
        
        # Create article document
        article_doc = {
            "title": article.title,
            "slug": slug,
            "content": article.content,
            "summary": article.summary,
            "categories": article.categories,
            "tags": article.tags,
            "status": "published",
            "createdAt": datetime.now(),
            "createdBy": current_user["_id"],
            "lastUpdatedAt": datetime.now(),
            "lastEditorId": current_user["_id"],
            "views": 0,
            "upvotes": 0,
            "downvotes": 0,
            "metadata": article.metadata if hasattr(article, 'metadata') else {}
        }
        
        # Insert into database
        result = await db["articles"].insert_one(article_doc)
        
        # Update user statistics
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$inc": {"contributions.articlesCreated": 1}}
        )
        
        # Index in search if available
        if search:
            try:
                await search.index(
                    index="articles",
                    id=str(result.inserted_id),
                    body={
                        "title": article.title,
                        "content": article.content,
                        "summary": article.summary,
                        "categories": article.categories,
                        "tags": article.tags
                    }
                )
            except Exception as e:
                logger.error(f"Error indexing article in search: {e}")
                # Continue even if indexing fails
        
        # Get created article
        created_article = await db["articles"].find_one({"_id": result.inserted_id})
        
        # Clear cache if needed
        try:
            if cache := await anext(get_cache()):
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
        
        # Ensure upvotes and downvotes fields exist
        if "upvotes" not in article:
            article["upvotes"] = 0
        if "downvotes" not in article:
            article["downvotes"] = 0
            
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
    request: Request,
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Update an existing article.
    """
    try:
        logger.info(f"Updating article with ID: {id}")
        
        # Check if article exists
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get user info (authenticated or anonymous)
        from dependencies.auth import get_user_or_anonymous
        user_info = await get_user_or_anonymous(request, db)
        
        # Check permissions
        if user_info["type"] == "anonymous":
            # Anonymous users can edit but not change certain fields
            restricted_fields = ["status", "title"]
            for field in restricted_fields:
                if hasattr(article_update, field) and getattr(article_update, field) is not None:
                    if field == "title":
                        raise HTTPException(
                            status_code=403,
                            detail="Anonymous users cannot change article titles"
                        )
                    if field == "status":
                        raise HTTPException(
                            status_code=403,
                            detail="Anonymous users cannot change article status"
                        )
        else:
            # Authenticated user - check specific permissions
            user = user_info["user"]
            is_creator = str(article["createdBy"]) == str(user["_id"])
            is_admin = user["role"] == "admin"
            is_editor = user["role"] == "editor"
            
            if not (is_creator or is_admin or is_editor):
                logger.warning(f"User {user['username']} tried to update article {id} without permission")
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
            
        # Allow status updates but only for admin/editor
        if article_update.status is not None:
            if user_info["type"] == "anonymous" or user_info["user"]["role"] not in ["admin", "editor"]:
                raise HTTPException(
                    status_code=403, 
                    detail="Only admins and editors can change article status"
                )
            
            # Validate status
            valid_statuses = ["published", "draft", "hidden", "archived"]
            if article_update.status not in valid_statuses:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            update_data["status"] = article_update.status
        
        # Set last updated info
        update_data["lastUpdatedAt"] = datetime.now()
        if user_info["type"] == "authenticated":
            update_data["lastEditorId"] = user_info["user"]["_id"]
        
        # Create revision for history
        revision_data = {
            "articleId": ObjectId(id),
            "content": article_update.content or article["content"],
            "summary": article_update.summary or article["summary"],
            "categories": article_update.categories or article.get("categories", []),
            "tags": article_update.tags or article.get("tags", []),
            "createdAt": datetime.now(),
            "editorId": user_info["user"]["_id"] if user_info["type"] == "authenticated" else None,
            "editorIP": user_info["anonymized_ip"],
            "editorType": user_info["type"],
            "editorName": user_info["display_name"],
            "comment": getattr(article_update, 'editComment', '') or "No edit summary"
        }
        
        # Insert revision
        await db["revisions"].insert_one(revision_data)
        
        # Update the article
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        
        # Update user statistics for authenticated users
        if user_info["type"] == "authenticated":
            await db["users"].update_one(
                {"_id": user_info["user"]["_id"]},
                {"$inc": {"contributions.editsPerformed": 1}}
            )
        
        # Update search index
        if search:
            try:
                await search.update(
                    index="articles",
                    id=id,
                    body={
                        "title": update_data.get("title", article["title"]),
                        "content": update_data.get("content", article["content"]),
                        "summary": update_data.get("summary", article["summary"]),
                        "categories": update_data.get("categories", article.get("categories", [])),
                        "tags": update_data.get("tags", article.get("tags", []))
                    }
                )
            except Exception as e:
                logger.error(f"Error updating search index: {e}")
        
        # Clear cache
        if cache:
            try:
                await cache.delete(f"article:{id}")
                if article.get("slug"):
                    await cache.delete(f"article:{article['slug']}")
                await cache.delete("featured_article")
                await cache.delete("recent_articles")
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
        
        # Get updated article
        updated_article = await db["articles"].find_one({"_id": ObjectId(id)})
        
        logger.info(f"Successfully updated article {id}")
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
    permanent: bool = Query(False, description="Permanently delete the article"),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Delete or archive an article. Only admins can delete articles.
    """
    try:
        logger.info(f"User {current_user['username']} attempting to delete article {id}")
        
        # Check if article exists
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        if permanent:
            # Permanently delete
            await db["articles"].delete_one({"_id": ObjectId(id)})
            
            # Also delete related data
            await db["revisions"].delete_many({"articleId": ObjectId(id)})
            await db["proposals"].delete_many({"articleId": ObjectId(id)})
            await db["rewards"].delete_many({"articleId": ObjectId(id)})
            
            message = "Article permanently deleted"
        else:
            # Mark as archived
            await db["articles"].update_one(
                {"_id": ObjectId(id)},
                {"$set": {"status": "archived"}}
            )
            message = "Article archived successfully"
        
        # Remove from search
        if search:
            try:
                await search.delete(
                    index="articles",
                    id=id
                )
            except Exception as e:
                logger.error(f"Error removing article from search: {e}")
        
        # Clear cache
        if cache:
            try:
                await cache.delete(f"article:{id}")
                if article.get("slug"):
                    await cache.delete(f"article:{article['slug']}")
                await cache.delete("featured_article")
                await cache.delete("recent_articles")
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
        
        return {"message": message}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling article deletion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process article deletion: {str(e)}"
        )

@router.post("/{id}/revisions/{revision_id}/restore")
async def restore_article_revision(
    id: str,
    revision_id: str,
    request: Request,
    restore_data: Dict[str, Any] = Body(...),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Restore an article to a previous revision.
    This creates a new revision with the content from the specified revision.
    """
    try:
        # Get user info (authenticated or anonymous)
        from dependencies.auth import get_user_or_anonymous
        user_info = await get_user_or_anonymous(request, db)
        
        # Check permissions - only editors/admins can restore, not anonymous users
        if user_info["type"] == "anonymous":
            raise HTTPException(
                status_code=401,
                detail="You must be logged in to restore article revisions"
            )
        
        user = user_info["user"]
        if user["role"] not in ["admin", "editor"]:
            raise HTTPException(
                status_code=403,
                detail="Only editors and administrators can restore article revisions"
            )
        
        logger.info(f"User {user['username']} attempting to restore article {id} to revision {revision_id}")
        
        # Validate IDs
        if not ObjectId.is_valid(id) or not ObjectId.is_valid(revision_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        # Get the article
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get the revision to restore
        revision_to_restore = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(id)
        })
        if not revision_to_restore:
            raise HTTPException(status_code=404, detail="Revision not found")
        
        # Create new revision with restored content
        new_revision = {
            "articleId": ObjectId(id),
            "content": revision_to_restore["content"],
            "summary": revision_to_restore.get("summary", ""),
            "categories": revision_to_restore.get("categories", []),
            "tags": revision_to_restore.get("tags", []),
            "createdAt": datetime.now(),
            "editorId": user["_id"],
            "editorIP": user_info["anonymized_ip"],
            "editorType": "authenticated",
            "editorName": user["username"],
            "comment": restore_data.get("comment", f"Restored to revision from {revision_to_restore['createdAt']}"),
            "isRestore": True,
            "restoredFromRevision": ObjectId(revision_id)
        }
        
        # Insert the new revision
        revision_result = await db["revisions"].insert_one(new_revision)
        
        # Update the article with restored content
        update_data = {
            "content": revision_to_restore["content"],
            "summary": revision_to_restore.get("summary", ""),
            "categories": revision_to_restore.get("categories", []),
            "tags": revision_to_restore.get("tags", []),
            "lastUpdatedAt": datetime.now(),
            "lastEditorId": user["_id"]
        }
        
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        
        # Update user statistics
        await db["users"].update_one(
            {"_id": user["_id"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
        
        # Clear cache
        if cache:
            try:
                await cache.delete(f"article:{id}")
                if article.get("slug"):
                    await cache.delete(f"article:{article['slug']}")
                await cache.delete("recent_articles")
                await cache.delete("featured_article")
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
        
        # Update search index
        search = request.app.state.search
        if search:
            try:
                await search.update(
                    index="articles",
                    id=id,
                    body={
                        "title": article["title"],
                        "content": revision_to_restore["content"],
                        "summary": revision_to_restore.get("summary", ""),
                        "categories": revision_to_restore.get("categories", []),
                        "tags": revision_to_restore.get("tags", [])
                    }
                )
            except Exception as e:
                logger.error(f"Error updating search index: {e}")
        
        logger.info(f"Article {id} restored to revision {revision_id} by {user['username']}")
        
        return {
            "message": "Article restored successfully",
            "revisionId": str(revision_result.inserted_id),
            "restoredFromRevision": revision_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring article revision: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore article revision: {str(e)}"
        )
