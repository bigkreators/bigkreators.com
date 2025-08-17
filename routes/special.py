# File: routes/special.py
"""
Special routes for administrative functions, statistics, and user management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import logging

# Import dependencies
from dependencies.database import get_db
from dependencies.auth import get_current_user, get_current_admin, get_current_editor
from dependencies.cache import get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics(
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get platform statistics.
    """
    try:
        # Try to get from cache
        cached = await cache.get("statistics")
        if cached:
            return cached
        
        # Get statistics
        articles_count = await db["articles"].count_documents({"status": "published"})
        users_count = await db["users"].count_documents({})
        revisions_count = await db["revisions"].count_documents({})
        
        # Most viewed article
        most_viewed = await db["articles"].find_one(
            {"status": "published"},
            sort=[("views", -1)]
        )
        
        # Most active user (by edits)
        most_active = await db["users"].find_one(
            sort=[("contributions.editsPerformed", -1)]
        )
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_revisions = await db["revisions"].count_documents({"createdAt": {"$gte": yesterday}})
        recent_proposals = await db["proposals"].count_documents({"proposedAt": {"$gte": yesterday}})
        
        statistics = {
            "articles": articles_count,
            "users": users_count,
            "revisions": revisions_count,
            "mostViewedArticle": {
                "id": str(most_viewed["_id"]) if most_viewed else None,
                "title": most_viewed.get("title") if most_viewed else None,
                "views": most_viewed.get("views") if most_viewed else 0
            },
            "mostActiveUser": {
                "id": str(most_active["_id"]) if most_active else None,
                "username": most_active.get("username") if most_active else None,
                "edits": most_active.get("contributions", {}).get("editsPerformed", 0) if most_active else 0
            },
            "recentActivity": {
                "revisions": recent_revisions,
                "proposals": recent_proposals,
                "total": recent_revisions + recent_proposals
            }
        }
        
        # Cache for 1 hour
        await cache.set("statistics", statistics, 3600)
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

@router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get a list of users (admin only).
    """
    try:
        cursor = db["users"].find().sort("joinDate", -1).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Remove password hashes for security
        for user in users:
            if "passwordHash" in user:
                del user["passwordHash"]
        
        return users
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_detail(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get detailed information about a specific user (admin only).
    """
    try:
        # Check if user exists
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove sensitive information
        if "passwordHash" in user:
            del user["passwordHash"]
        
        # Get user's articles
        articles_cursor = db["articles"].find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1).limit(10)
        articles = await articles_cursor.to_list(length=10)
        
        # Get user's edits/revisions
        revisions_cursor = db["revisions"].find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1).limit(10)
        revisions = await revisions_cursor.to_list(length=10)
        
        # Get user's proposals
        proposals_cursor = db["proposals"].find({"proposedBy": ObjectId(user_id)}).sort("proposedAt", -1).limit(10)
        proposals = await proposals_cursor.to_list(length=10)
        
        # Enhance with article titles
        enhanced_revisions = []
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            article_title = article["title"] if article else "Unknown Article"
            
            enhanced_revisions.append({
                **rev,
                "articleTitle": article_title
            })
        
        enhanced_proposals = []
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            article_title = article["title"] if article else "Unknown Article"
            
            enhanced_proposals.append({
                **prop,
                "articleTitle": article_title
            })
        
        # Return complete user info
        return {
            "user": user,
            "articles": articles,
            "revisions": enhanced_revisions,
            "proposals": enhanced_proposals
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user details: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Delete a user account (admin only).
    """
    try:
        # Check if user exists
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow deletion of the current admin user
        if str(user["_id"]) == str(current_user["_id"]):
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Delete the user
        result = await db["users"].delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: Dict[str, str],
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Update a user's role (admin only).
    """
    try:
        # Check if user exists
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate role
        new_role = role_data.get("role")
        valid_roles = ["reader", "editor", "admin"]
        if new_role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
        
        # Don't allow changing your own role to prevent lockout
        if str(user["_id"]) == str(current_user["_id"]):
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        
        # Ensure there's at least one admin remaining
        if user.get("role") == "admin" and new_role != "admin":
            admin_count = await db["users"].count_documents({
                "role": "admin",
                "_id": {"$ne": ObjectId(user_id)}
            })
            if admin_count == 0:
                raise HTTPException(status_code=400, detail="Cannot remove the last admin")
        
        # Ensure there's at least one editor remaining  
        if user.get("role") == "editor" and new_role not in ["editor", "admin"]:
            editor_count = await db["users"].count_documents({
                "role": {"$in": ["editor", "admin"]},
                "_id": {"$ne": ObjectId(user_id)}
            })
            if editor_count == 0:
                raise HTTPException(status_code=400, detail="Cannot remove the last editor")
        
        # Update the user's role
        update_data = {
            "role": new_role,
            "updatedAt": datetime.now()
        }
        
        result = await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get updated user
        updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})
        
        # Remove password hash
        if "passwordHash" in updated_user:
            del updated_user["passwordHash"]
        
        return {
            "message": "User role updated successfully",
            "user": updated_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.get("/recent-changes", response_model=List[Dict[str, Any]])
async def get_recent_changes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    filter_type: Optional[str] = Query(None, description="Filter by type: revision, proposal, or all"),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get recent changes (revisions and proposals).
    """
    try:
        # Try to get from cache if no filtering
        cache_key = f"recent_changes_{skip}_{limit}_{filter_type or 'all'}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        changes = []
        
        # Get recent revisions if not filtering for proposals only
        if filter_type != "proposal":
            revisions_cursor = db["revisions"].find().sort("createdAt", -1).skip(skip).limit(limit)
            revisions = await revisions_cursor.to_list(length=limit)
            
            for rev in revisions:
                # Get article info
                article = await db["articles"].find_one({"_id": rev["articleId"]})
                # Get user info
                user = await db["users"].find_one({"_id": rev["createdBy"]})
                
                changes.append({
                    "type": "revision",
                    "id": str(rev["_id"]),
                    "timestamp": rev["createdAt"],
                    "articleId": str(rev["articleId"]),
                    "articleTitle": article["title"] if article else "Unknown Article",
                    "userId": str(rev["createdBy"]),
                    "username": user["username"] if user else "Unknown User",
                    "summary": rev.get("summary", "No summary provided"),
                    "changeType": rev.get("changeType", "edit")
                })
        
        # Get recent proposals if not filtering for revisions only
        if filter_type != "revision":
            proposals_cursor = db["proposals"].find().sort("proposedAt", -1).skip(skip).limit(limit)
            proposals = await proposals_cursor.to_list(length=limit)
            
            for prop in proposals:
                # Get article info
                article = await db["articles"].find_one({"_id": prop["articleId"]})
                # Get user info
                user = await db["users"].find_one({"_id": prop["proposedBy"]})
                
                changes.append({
                    "type": "proposal",
                    "id": str(prop["_id"]),
                    "timestamp": prop["proposedAt"],
                    "articleId": str(prop["articleId"]),
                    "articleTitle": article["title"] if article else "Unknown Article",
                    "userId": str(prop["proposedBy"]),
                    "username": user["username"] if user else "Unknown User",
                    "summary": prop.get("summary", "No summary provided"),
                    "status": prop.get("status", "pending")
                })
        
        # Sort all changes by timestamp (newest first)
        changes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit the results
        changes = changes[:limit]
        
        # Cache for 5 minutes
        await cache.set(cache_key, changes, 300)
        
        return changes
        
    except Exception as e:
        logger.error(f"Error getting recent changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent changes: {str(e)}"
        )

@router.get("/search-users", response_model=List[Dict[str, Any]])
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Search for users by username or email (admin only).
    """
    try:
        # Create search query
        search_filter = {
            "$or": [
                {"username": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}}
            ]
        }
        
        cursor = db["users"].find(search_filter).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Remove password hashes for security
        for user in users:
            if "passwordHash" in user:
                del user["passwordHash"]
        
        return users
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )
