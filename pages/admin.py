# File: pages/admin.py

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

async def get_admin_from_request(request, db):
    """
    Try to get an admin user from the request using multiple methods.
    Returns None if no authenticated admin user is found.
    """
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            from dependencies.auth import get_current_user
            user = await get_current_user(token=token, db=db)
            if user and user.get("role") == "admin":
                return user
        except Exception as e:
            logger.debug(f"Error getting admin from Authorization header: {e}")
    
    # Try to get token from cookie
    token = request.cookies.get("token")
    if token:
        try:
            from dependencies.auth import get_current_user
            user = await get_current_user(token=token, db=db)
            if user and user.get("role") == "admin":
                return user
        except Exception as e:
            logger.debug(f"Error getting admin from cookie: {e}")
    
    # No valid admin authentication found
    return None

async def get_dashboard_stats(db):
    """
    Get dashboard statistics for the admin dashboard.
    """
    try:
        stats = {}
        
        # Article stats
        stats["articles"] = await db["articles"].count_documents({})
        stats["published_articles"] = await db["articles"].count_documents({"status": "published"})
        stats["draft_articles"] = await db["articles"].count_documents({"status": "draft"})
        stats["hidden_articles"] = await db["articles"].count_documents({"status": "hidden"})
        
        # User stats
        stats["users"] = await db["users"].count_documents({})
        stats["admins"] = await db["users"].count_documents({"role": "admin"})
        stats["editors"] = await db["users"].count_documents({"role": "editor"})
        
        # New users this week
        week_ago = datetime.now() - timedelta(days=7)
        stats["new_users_week"] = await db["users"].count_documents(
            {"joinDate": {"$gte": week_ago}}
        )
        
        # Activity stats
        stats["edits_week"] = await db["revisions"].count_documents(
            {"createdAt": {"$gte": week_ago}}
        )
        
        stats["proposals_week"] = await db["proposals"].count_documents(
            {"proposedAt": {"$gte": week_ago}}
        )
        
        stats["pending_proposals"] = await db["proposals"].count_documents(
            {"status": "pending"}
        )
        
        stats["new_articles_week"] = await db["articles"].count_documents(
            {"createdAt": {"$gte": week_ago}}
        )
        
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {}

async def get_recent_activity(db, limit=10):
    """
    Get recent activity for the admin dashboard.
    """
    try:
        activities = []
        
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(limit)
        revisions = await revisions_cursor.to_list(length=limit)
        
        for rev in revisions:
            # Get article info
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            if not article:
                continue
                
            # Get user info
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            if not user:
                continue
                
            activities.append({
                "type": "edit",
                "timestamp": rev["createdAt"],
                "user": {
                    "username": user["username"],
                    "_id": str(user["_id"])
                },
                "article": {
                    "title": article["title"],
                    "slug": article.get("slug", ""),
                    "_id": str(article["_id"])
                },
                "comment": rev.get("comment", "")
            })
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).limit(limit)
        proposals = await proposals_cursor.to_list(length=limit)
        
        for prop in proposals:
            # Get article info
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            if not article:
                continue
                
            # Get user info
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            if not user:
                continue
                
            activities.append({
                "type": "proposal",
                "timestamp": prop["proposedAt"],
                "user": {
                    "username": user["username"],
                    "_id": str(user["_id"])
                },
                "article": {
                    "title": article["title"],
                    "slug": article.get("slug", ""),
                    "_id": str(article["_id"])
                },
                "comment": prop.get("summary", "")
            })
        
        # Get new users
        week_ago = datetime.now() - timedelta(days=7)
        users_cursor = db["users"].find({"joinDate": {"$gte": week_ago}}).sort("joinDate", -1).limit(limit)
        new_users = await users_cursor.to_list(length=limit)
        
        for user in new_users:
            activities.append({
                "type": "new_user",
                "timestamp": user["joinDate"],
                "user": {
                    "username": user["username"],
                    "_id": str(user["_id"])
                },
                "comment": "joined the wiki"
            })
        
        # Sort by timestamp (newest first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit to requested number
        activities = activities[:limit]
        
        return activities
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return []

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(
    request: Request,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the admin dashboard page with proper authentication check.
    """
    templates = request.app.state.templates
    
    # Try to get admin user from request
    admin_user = await get_admin_from_request(request, db)
    
    # If no admin user is found, return login required page
    if not admin_user:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request, 
                "redirect_to": "/admin",
                "active_page": "admin"
            }
        )
    
    # Try to get dashboard data from cache
    cache_key = "admin_dashboard_data"
    dashboard_data = await cache.get(cache_key)
    
    if not dashboard_data:
        # Fetch dashboard statistics
        stats = await get_dashboard_stats(db)
        
        # Fetch recent activity
        recent_activity = await get_recent_activity(db)
        
        # Combine data
        dashboard_data = {
            "stats": stats,
            "recent_activity": recent_activity
        }
        
        # Cache for 5 minutes
        await cache.set(cache_key, dashboard_data, 300)
    
    # User is an admin, render the dashboard with data
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "current_user": admin_user,
            "active_page": "admin",
            "dashboard_data": dashboard_data
        }
    )

@router.get("/admin/users", response_class=HTMLResponse)
async def user_management_page(
    request: Request,
    role: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the user management page with proper authentication check.
    """
    templates = request.app.state.templates
    
    # Try to get admin user from request
    admin_user = await get_admin_from_request(request, db)
    
    # If no admin user is found, return login required page
    if not admin_user:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request, 
                "redirect_to": f"/admin/users?role={role or ''}&search={search or ''}&skip={skip}&limit={limit}",
                "active_page": "admin"
            }
        )
    
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
            "current_user": admin_user,
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
    db=Depends(get_db)
):
    """
    Render the article management page with proper authentication check.
    """
    templates = request.app.state.templates
    
    # Try to get admin user from request
    admin_user = await get_admin_from_request(request, db)
    
    # If no admin user is found, return login required page
    if not admin_user:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request, 
                "redirect_to": f"/admin/articles?status={status or ''}&search={search or ''}&skip={skip}&limit={limit}",
                "active_page": "admin"
            }
        )
    
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
        try:
            # Safely get createdBy field with fallback
            creator_id = article.get("createdBy")
            creator_username = "Unknown"
            
            # Only look up the creator if we have a valid ID
            if creator_id:
                creator = await db["users"].find_one({"_id": creator_id})
                if creator:
                    creator_username = creator.get("username", "Unknown")
            
            enhanced_articles.append({
                **article,
                "creatorUsername": creator_username
            })
        except Exception as e:
            # If there's any error processing this article, log it and include a basic version
            logger.error(f"Error processing article {article.get('_id')}: {e}")
            enhanced_articles.append({
                **article,
                "creatorUsername": "Unknown"
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
            "current_user": admin_user,
            "active_page": "admin"
        }
    )

@router.get("/admin/proposals", response_class=HTMLResponse)
async def proposals_management_page(
    request: Request,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the proposals management page with proper authentication check for editors.
    """
    templates = request.app.state.templates
    
    # Try to get editor/admin user from request
    admin_user = await get_admin_from_request(request, db)
    
    # Check if user is admin or editor
    is_editor = False
    if admin_user:
        is_editor = True
    else:
        # Try to check if user is an editor
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                from dependencies.auth import get_current_user
                user = await get_current_user(token=token, db=db)
                if user and user.get("role") in ["admin", "editor"]:
                    is_editor = True
            except:
                pass
    
    # If not editor or admin, return login required page
    if not is_editor:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request, 
                "redirect_to": f"/admin/proposals?status={status or ''}&skip={skip}&limit={limit}",
                "active_page": "admin"
            }
        )
    
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
    db=Depends(get_db)
):
    """
    Redirect to the special statistics page with proper authentication check.
    """
    # Try to get admin user from request
    admin_user = await get_admin_from_request(request, db)
    
    # If no admin user is found, return login required page
    if not admin_user:
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request, 
                "redirect_to": "/admin/statistics",
                "active_page": "admin"
            }
        )
    
    return RedirectResponse(url="/special/statistics")

# API endpoints remain the same but with updated authentication
# These endpoints already use the get_current_admin dependency which handles auth correctly

# Add an API endpoint to fetch dashboard data
@router.get("/api/admin/dashboard/stats")
async def get_admin_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_admin), db=Depends(get_db)):
    """
    Get dashboard statistics for the admin dashboard.
    """
    try:
        # Fetch dashboard statistics
        stats = await get_dashboard_stats(db)
        
        # Fetch recent activity
        recent_activity = await get_recent_activity(db)
        
        return {
            **stats,
            "recent_activity": recent_activity
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard statistics")
