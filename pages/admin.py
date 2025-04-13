"""
Admin page routes.
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from dependencies import get_db, get_current_admin, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Render the admin dashboard.
    """
    templates = request.app.state.templates
    
    try:
        # Gather statistics
        stats = {}
        
        # Article stats
        stats["articles"] = await db["articles"].count_documents({"status": "published"})
        
        # User stats
        stats["users"] = await db["users"].count_documents({})
        
        # Pending proposals
        stats["pending_proposals"] = await db["proposals"].count_documents({"status": "pending"})
        
        # Recent activity (last 24 hours)
        recent_revisions = await db["revisions"].count_documents({
            "createdAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        recent_proposals = await db["proposals"].count_documents({
            "proposedAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        
        stats["recent_activity"] = {
            "revisions": recent_revisions,
            "proposals": recent_proposals,
            "total": recent_revisions + recent_proposals
        }
        
        # Get recent activity for display
        recent_activity = []
        
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "Edit",
                    "timestamp": rev["createdAt"],
                    "articleId": str(rev["articleId"]),
                    "articleTitle": article["title"],
                    "username": user["username"]
                })
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).limit(5)
        proposals = await proposals_cursor.to_list(length=5)
        
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "Proposal",
                    "timestamp": prop["proposedAt"],
                    "articleId": str(prop["articleId"]),
                    "articleTitle": article["title"],
                    "username": user["username"]
                })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:5]  # Only show top 5
        
        # Render template
        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "stats": stats,
                "recent_activity": recent_activity,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

@router.get("/admin/articles", response_class=HTMLResponse)
async def article_management_page(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Render the article management page (admin only).
    """
    templates = request.app.state.templates
    
    try:
        # Build query
        query = {}
        
        # Filter by status if provided
        if status:
            query["status"] = status
        
        # Search in title, content, or summary if provided
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}},
                {"summary": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total_count = await db["articles"].count_documents(query)
        
        # Get articles with pagination
        cursor = db["articles"].find(query).sort("lastUpdatedAt", -1).skip(skip).limit(limit)
        articles = await cursor.to_list(length=limit)
        
        # Render template
        return templates.TemplateResponse(
            "article_management.html",
            {
                "request": request,
                "articles": articles,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "status": status,
                "search": search,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in article management page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

@router.get("/admin/users", response_class=HTMLResponse)
async def user_management_page(
    request: Request,
    role: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Render the user management page.
    """
    templates = request.app.state.templates
    
    try:
        # Build query
        query = {}
        
        # Filter by role if provided
        if role:
            query["role"] = role
        
        # Search in username or email if provided
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total_count = await db["users"].count_documents(query)
        
        # Get users with pagination
        cursor = db["users"].find(query).sort("joinDate", -1).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Render template
        return templates.TemplateResponse(
            "user_management.html",
            {
                "request": request,
                "users": users,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "role": role,
                "search": search,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in user management page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

@router.get("/admin/proposals", response_class=HTMLResponse)
async def admin_proposals_page(
    request: Request,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Admin page for managing all proposals.
    """
    # Redirect to the proposals page with proper filtering
    return RedirectResponse(url=f"/proposals?status={status or 'pending'}")
