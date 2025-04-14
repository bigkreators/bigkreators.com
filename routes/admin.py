# File: routes/admin.py

"""
Admin API routes for the Kryptopedia application.
Provides backend endpoints for the admin dashboard functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from typing import Dict, Any, List, Optional
from bson import ObjectId
from datetime import datetime, timedelta
import logging

from dependencies import get_db, get_current_admin, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/statistics")
async def get_admin_statistics(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get dashboard statistics for the admin dashboard.
    """
    try:
        # Check if stats are cached
        cache_key = "admin_dashboard_stats"
        cached_stats = await cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Calculate statistics
        statistics = {}
        
        # Article stats
        statistics["total_articles"] = await db["articles"].count_documents({})
        statistics["published_articles"] = await db["articles"].count_documents({"status": "published"})
        statistics["draft_articles"] = await db["articles"].count_documents({"status": "draft"})
        statistics["hidden_articles"] = await db["articles"].count_documents({"status": "hidden"})
        statistics["archived_articles"] = await db["articles"].count_documents({"status": "archived"})
        
        # User stats
        statistics["total_users"] = await db["users"].count_documents({})
        statistics["admin_users"] = await db["users"].count_documents({"role": "admin"})
        statistics["editor_users"] = await db["users"].count_documents({"role": "editor"})
        statistics["regular_users"] = await db["users"].count_documents({"role": "user"})
        
        # Activity stats
        statistics["total_edits"] = await db["revisions"].count_documents({})
        statistics["total_proposals"] = await db["proposals"].count_documents({})
        statistics["pending_proposals"] = await db["proposals"].count_documents({"status": "pending"})
        
        # Recent activity (last 24 hours)
        recent_revisions = await db["revisions"].count_documents({
            "createdAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        recent_proposals = await db["proposals"].count_documents({
            "proposedAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        recent_users = await db["users"].count_documents({
            "joinDate": {"$gte": datetime.now() - timedelta(days=1)}
        })
        
        statistics["recent_activity"] = {
            "revisions": recent_revisions,
            "proposals": recent_proposals,
            "users": recent_users,
            "total": recent_revisions + recent_proposals + recent_users
        }
        
        # Cache results for 5 minutes
        await cache.set(cache_key, statistics, 300)
        
        return statistics
    except Exception as e:
        logger.error(f"Error getting admin statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/users")
async def get_admin_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get users for admin management.
    """
    try:
        # Build query
        query = {}
        
        # Role filter
        if role:
            query["role"] = role
        
        # Search filter
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total = await db["users"].count_documents(query)
        
        # Get users with pagination
        cursor = db["users"].find(query).sort("joinDate", -1).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Remove sensitive fields
        for user in users:
            if "passwordHash" in user:
                del user["passwordHash"]
        
        return {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@router.get("/articles")
async def get_admin_articles(
    search: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get articles for admin management.
    """
    try:
        # Build query
        query = {}
        
        # Status filter
        if status:
            query["status"] = status
        
        # Search filter
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}},
                {"summary": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total = await db["articles"].count_documents(query)
        
        # Get articles with pagination
        cursor = db["articles"].find(query).sort("createdAt", -1).skip(skip).limit(limit)
        articles = await cursor.to_list(length=limit)
        
        # Enhance articles with creator username
        enhanced_articles = []
        for article in articles:
            # Get creator info
            creator = await db["users"].find_one({"_id": article["createdBy"]})
            creator_username = creator["username"] if creator else "Unknown"
            
            # Add to enhanced list
            enhanced_articles.append({
                **article,
                "creatorUsername": creator_username
            })
        
        return {
            "articles": enhanced_articles,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting admin articles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Delete a user (admin only).
    """
    try:
        # Verify valid ObjectId
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Check that user exists
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admins from deleting themselves
        if str(user["_id"]) == str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Cannot delete your own account")
        
        # Delete user
        result = await db["users"].delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete user")
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.post("/cache/clear")
async def clear_cache(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    cache=Depends(get_cache)
):
    """
    Clear the application cache (admin only).
    """
    try:
        # Clear cache
        result = await cache.clear()
        
        if result:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
