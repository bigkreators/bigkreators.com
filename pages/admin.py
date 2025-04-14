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

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(
    request: Request,
    db=Depends(get_db)
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
    
    # User is an admin, render the dashboard
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "current_user": admin_user,
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
