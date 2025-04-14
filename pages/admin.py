"""
Admin page routes for the Kryptopedia application.
Handles rendering of admin dashboard, user management, and other admin functionality.
"""
from fastapi import APIRouter, Request, Depends, Path, Query, HTTPException, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Dict, Any, List, Optional
import logging
from bson import ObjectId
from datetime import datetime, timedelta

from dependencies import get_db, get_current_admin, get_current_editor, get_cache
from models.user import UserUpdate

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(
    request: Request,
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Render the admin dashboard page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "admin"
        }
    )

@router.get("/admin/users", response_class=HTMLResponse)
async def user_management_page(
    request: Request,
    role: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Render the user management page.
    """
    templates = request.app.state.templates
    
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
    
    # Get users with pagination and sorting
    cursor = db["users"].find(query).sort("joinDate", -1).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    
    # Remove sensitive information
    for user in users:
        if "passwordHash" in user:
            del user["passwordHash"]
    
    return templates.TemplateResponse(
        "user_management.html",
        {
            "request": request,
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit,
            "role": role,
            "search": search,
            "current_user": current_user,
            "is_admin": True,
            "active_page": "admin"
        }
    )

@router.get("/admin/articles", response_class=HTMLResponse)
async def article_management_page(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Render the article management page.
    """
    templates = request.app.state.templates
    
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
    
    # Get articles with pagination and sorting
    cursor = db["articles"].find(query).sort("createdAt", -1).skip(skip).limit(limit)
    articles = await cursor.to_list(length=limit)
    
    # Enhance articles with creator information
    enhanced_articles = []
    for article in articles:
        creator = await db["users"].find_one({"_id": article["createdBy"]})
        creator_username = creator["username"] if creator else "Unknown"
        
        enhanced_articles.append({
            **article,
            "creatorUsername": creator_username
        })
    
    return templates.TemplateResponse(
        "article_management.html",
        {
            "request": request,
            "articles": enhanced_articles,
            "total": total,
            "skip": skip,
            "limit": limit,
            "status": status,
            "search": search,
            "current_user": current_user,
            "active_page": "admin"
        }
    )

@router.get("/admin/proposals", response_class=HTMLResponse)
async def proposals_management_page(
    request: Request,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_editor)
):
    """
    Render the proposals management page.
    """
    # Redirect to the proposals page with appropriate filters
    url = "/proposals"
    
    if status:
        url += f"?status={status}"
    
    if skip > 0:
        url += f"{'&' if '?' in url else '?'}skip={skip}"
    
    if limit != 20:
        url += f"{'&' if '?' in url else '?'}limit={limit}"
        
    return RedirectResponse(url=url)

@router.get("/admin/statistics", response_class=HTMLResponse)
async def admin_statistics_page(
    request: Request,
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin)
):
    """
    Render the admin statistics page.
    """
    # Redirect to the special statistics page
    return RedirectResponse(url="/special/statistics")

# API endpoints to support admin dashboard functionality

@router.get("/api/admin/dashboard/stats")
async def get_dashboard_stats(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get admin dashboard statistics.
    """
    try:
        # Try to get from cache first
        cache_key = "admin_dashboard_stats"
        cached_stats = await cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Calculate stats
        stats = {}
        
        # Article stats
        stats["articles"] = await db["articles"].count_documents({})
        stats["published_articles"] = await db["articles"].count_documents({"status": "published"})
        stats["draft_articles"] = await db["articles"].count_documents({"status": "draft"})
        stats["hidden_articles"] = await db["articles"].count_documents({"status": "hidden"})
        stats["archived_articles"] = await db["articles"].count_documents({"status": "archived"})
        
        # User stats
        stats["users"] = await db["users"].count_documents({})
        stats["admins"] = await db["users"].count_documents({"role": "admin"})
        stats["editors"] = await db["users"].count_documents({"role": "editor"})
        stats["regular_users"] = await db["users"].count_documents({"role": "user"})
        
        # Recent stats (last 7 days)
        one_week_ago = datetime.now() - timedelta(days=7)
        
        stats["new_users_week"] = await db["users"].count_documents({
            "joinDate": {"$gte": one_week_ago}
        })
        
        stats["new_articles_week"] = await db["articles"].count_documents({
            "createdAt": {"$gte": one_week_ago}
        })
        
        stats["edits_week"] = await db["revisions"].count_documents({
            "createdAt": {"$gte": one_week_ago}
        })
        
        stats["proposals_week"] = await db["proposals"].count_documents({
            "proposedAt": {"$gte": one_week_ago}
        })
        
        stats["pending_proposals"] = await db["proposals"].count_documents({
            "status": "pending"
        })
        
        # Get recent activity
        recent_activity = []
        
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "edit",
                    "timestamp": rev["createdAt"],
                    "user": {
                        "id": str(user["_id"]),
                        "username": user["username"],
                        "role": user.get("role", "user")
                    },
                    "article": {
                        "id": str(article["_id"]),
                        "title": article["title"],
                        "slug": article.get("slug", "")
                    },
                    "comment": rev.get("comment", "")
                })
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).limit(5)
        proposals = await proposals_cursor.to_list(length=5)
        
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "proposal",
                    "timestamp": prop["proposedAt"],
                    "user": {
                        "id": str(user["_id"]),
                        "username": user["username"],
                        "role": user.get("role", "user")
                    },
                    "article": {
                        "id": str(article["_id"]),
                        "title": article["title"],
                        "slug": article.get("slug", "")
                    },
                    "status": prop["status"],
                    "summary": prop.get("summary", "")
                })
        
        # Get new users
        users_cursor = db["users"].find().sort("joinDate", -1).limit(5)
        new_users = await users_cursor.to_list(length=5)
        
        for user in new_users:
            recent_activity.append({
                "type": "new_user",
                "timestamp": user["joinDate"],
                "user": {
                    "id": str(user["_id"]),
                    "username": user["username"],
                    "role": user.get("role", "user")
                }
            })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Get top 5 items
        recent_activity = recent_activity[:5]
        
        # Store activity in the stats
        stats["recent_activity"] = recent_activity
        
        # Cache the results for 15 minutes
        await cache.set(cache_key, stats, 900)
        
        return stats
    except Exception as e:
        logger.error(f"Error getting admin dashboard stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting dashboard statistics: {str(e)}"
        )

@router.get("/api/admin/users")
async def get_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("joinDate", description="Field to sort by"),
    sort_order: int = Query(-1, description="Sort order: 1 for ascending, -1 for descending"),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get a list of users with optional filtering.
    """
    try:
        # Build query
        query = {}
        
        # Search filter
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # Role filter
        if role:
            query["role"] = role
        
        # Get total count
        total = await db["users"].count_documents(query)
        
        # Get users with pagination and sorting
        cursor = db["users"].find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Remove sensitive information
        for user in users:
            if "passwordHash" in user:
                del user["passwordHash"]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": users
        }
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting users: {str(e)}"
        )

@router.put("/api/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str = Query(..., description="New role"),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Update a user's role.
    """
    try:
        # Check if role is valid
        valid_roles = ["user", "editor", "admin"]
        if role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        # Check if user ID is valid
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid user ID format"
            )
        
        # Prevent self-role change
        if str(current_user["_id"]) == user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot change your own role"
            )
        
        # Find user
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Update role
        result = await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": role}}
        )
        
        if result.modified_count == 0:
            # User role might already be set to the requested role
            if user["role"] == role:
                return {"message": f"User role is already {role}"}
            
            raise HTTPException(
                status_code=400,
                detail="Failed to update user role"
            )
        
        return {"message": f"User role updated to {role}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user role: {str(e)}"
        )

@router.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Delete a user (admin only).
    """
    try:
        # Check if user ID is valid
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid user ID format"
            )
        
        # Prevent self-deletion
        if str(current_user["_id"]) == user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own account"
            )
        
        # Find user
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Delete user
        result = await db["users"].delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Failed to delete user"
            )
        
        return {"message": f"User {user['username']} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting user: {str(e)}"
        )

@router.post("/api/admin/system/clear-cache")
async def clear_cache(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    cache=Depends(get_cache)
):
    """
    Clear the application cache (admin only).
    """
    try:
        result = await cache.clear()
        return {"success": result, "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )
