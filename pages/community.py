"""
Community-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from dependencies import get_db, get_current_user, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/community", response_class=HTMLResponse)
async def community_portal(
    request: Request,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the community portal page.
    """
    templates = request.app.state.templates
    
    try:
        # Try to get data from cache
        cache_key = "community_portal"
        cached_data = await cache.get(cache_key)
        
        if not cached_data:
            # Get active users (users who logged in within the last 7 days)
            active_users_cursor = db["users"].find({
                "lastLogin": {"$gte": datetime.now() - timedelta(days=7)}
            }).sort("lastLogin", -1).limit(10)
            
            active_users = await active_users_cursor.to_list(length=10)
            
            # Remove sensitive info
            for user in active_users:
                if "passwordHash" in user:
                    del user["passwordHash"]
            
            # Get recent revisions
            recent_revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(10)
            recent_revisions = await recent_revisions_cursor.to_list(length=10)
            
            # Enhance with article and user info
            enhanced_revisions = []
            for rev in recent_revisions:
                article = await db["articles"].find_one({"_id": rev["articleId"]})
                user = await db["users"].find_one({"_id": rev["createdBy"]})
                
                if article and user:
                    enhanced_revisions.append({
                        "timestamp": rev["createdAt"],
                        "articleId": str(rev["articleId"]),
                        "articleTitle": article.get("title", "Unknown Article"),
                        "articleSlug": article.get("slug"),
                        "username": user.get("username", "Unknown User"),
                        "comment": rev.get("comment", "")
                    })
            
            # Get top contributors
            top_contributors_cursor = db["users"].find().sort(
                "contributions.editsPerformed", -1
            ).limit(5)
            
            top_contributors = await top_contributors_cursor.to_list(length=5)
            
            # Remove sensitive info
            for user in top_contributors:
                if "passwordHash" in user:
                    del user["passwordHash"]
            
            # Get recent discussions (placeholder - would be implemented with a discussions/forum system)
            recent_discussions = []
            
            # Get upcoming events (placeholder - would be implemented with an events system)
            upcoming_events = []
            
            # Combine data
            portal_data = {
                "active_users": active_users,
                "recent_revisions": enhanced_revisions,
                "top_contributors": top_contributors,
                "recent_discussions": recent_discussions,
                "upcoming_events": upcoming_events
            }
            
            # Cache data for 15 minutes
            await cache.set(cache_key, portal_data, 900)
            
            # Use the fetched data
            data = portal_data
        else:
            # Use cached data
            data = cached_data
        
        # Render template
        return templates.TemplateResponse(
            "community.html",
            {
                "request": request,
                "active_users": data["active_users"],
                "recent_revisions": data["recent_revisions"],
                "top_contributors": data["top_contributors"],
                "recent_discussions": data["recent_discussions"],
                "upcoming_events": data["upcoming_events"]
            }
        )
    except Exception as e:
        logger.error(f"Error rendering community portal: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading community portal: {str(e)}"},
            status_code=500
        )

@router.get("/community/contributors", response_class=HTMLResponse)
async def contributors_page(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the page listing all contributors.
    """
    templates = request.app.state.templates
    
    try:
        # Get contributors sorted by number of edits
        contributors_cursor = db["users"].find().sort(
            "contributions.editsPerformed", -1
        ).skip(skip).limit(limit)
        
        contributors = await contributors_cursor.to_list(length=limit)
        
        # Remove sensitive info
        for user in contributors:
            if "passwordHash" in user:
                del user["passwordHash"]
        
        # Get total count
        total_count = await db["users"].count_documents({})
        
        # Render template
        return templates.TemplateResponse(
            "contributors.html",
            {
                "request": request,
                "contributors": contributors,
                "total": total_count,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        logger.error(f"Error rendering contributors page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading contributors page: {str(e)}"},
            status_code=500
        )

@router.get("/community/guidelines", response_class=HTMLResponse)
async def community_guidelines(request: Request):
    """
    Render the community guidelines page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "community_guidelines.html",
        {"request": request}
    )

@router.get("/community/events", response_class=HTMLResponse)
async def community_events(
    request: Request,
    db=Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Render the community events page.
    """
    templates = request.app.state.templates
    
    # Placeholder for events data - would be fetched from database in a real implementation
    events = [
        {
            "title": "Monthly Contributor Meeting",
            "date": datetime.now() + timedelta(days=15),
            "description": "Join us for our monthly virtual meeting to discuss the wiki's progress and future plans.",
            "location": "Virtual (Zoom)",
            "organizer": "Admin Team"
        },
        {
            "title": "New Editor Training",
            "date": datetime.now() + timedelta(days=7),
            "description": "Learn how to effectively edit articles and contribute to the wiki.",
            "location": "Virtual (Zoom)",
            "organizer": "Training Team"
        },
        {
            "title": "Content Creation Sprint",
            "date": datetime.now() + timedelta(days=30),
            "description": "Join our focused effort to create content in specific topic areas.",
            "location": "Online",
            "organizer": "Content Team"
        }
    ]
    
    # Determine if user can create events (admin/editor role)
    can_create_events = False
    if current_user and current_user.get("role") in ["admin", "editor"]:
        can_create_events = True
    
    return templates.TemplateResponse(
        "community_events.html",
        {
            "request": request,
            "events": events,
            "can_create_events": can_create_events
        }
    )

@router.get("/community/forum", response_class=HTMLResponse)
async def community_forum(
    request: Request,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the community forum page.
    
    Note: This is a placeholder for a full forum implementation.
    In a real application, you would likely integrate with an
    existing forum software or implement a more robust system.
    """
    templates = request.app.state.templates
    
    # Placeholder for categories and topics
    categories = [
        {"id": "general", "name": "General Discussion", "description": "General discussion about Kryptopedia"},
        {"id": "technical", "name": "Technical Questions", "description": "Technical questions and discussions"},
        {"id": "suggestions", "name": "Suggestions", "description": "Suggestions for improving Kryptopedia"},
        {"id": "admin", "name": "Administrative", "description": "Administrative announcements and discussions"}
    ]
    
    # Placeholder for topics (in a real implementation these would come from database)
    topics = [
        {
            "id": "1",
            "title": "Welcome to the Forum",
            "category": "general",
            "author": "Admin",
            "created_at": datetime.now() - timedelta(days=10),
            "last_reply_at": datetime.now() - timedelta(hours=5),
            "replies": 15
        },
        {
            "id": "2",
            "title": "How to contribute effectively",
            "category": "general",
            "author": "Editor",
            "created_at": datetime.now() - timedelta(days=7),
            "last_reply_at": datetime.now() - timedelta(days=2),
            "replies": 8
        },
        {
            "id": "3",
            "title": "Technical issues with editing",
            "category": "technical",
            "author": "User123",
            "created_at": datetime.now() - timedelta(days=3),
            "last_reply_at": datetime.now() - timedelta(days=1),
            "replies": 4
        }
    ]
    
    # Filter by category if provided
    if category:
        topics = [topic for topic in topics if topic["category"] == category]
    
    return templates.TemplateResponse(
        "community_forum.html",
        {
            "request": request,
            "categories": categories,
            "topics": topics,
            "current_category": category
        }
    )
