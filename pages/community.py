# File: pages/community.py
"""
Community page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from dependencies import get_db, get_current_user, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/community", response_class=HTMLResponse)
async def community_page(request: Request, db=Depends(get_db), cache=Depends(get_cache)):
    """
    Render the community portal page.
    """
    templates = request.app.state.templates
    
    # Try to get from cache first
    cache_key = "community_dashboard"
    cached_data = await cache.get(cache_key)
    
    if cached_data:
        return templates.TemplateResponse(
            "community.html",
            {
                "request": request,
                **cached_data
            }
        )
    
    # Initialize data with defaults
    dashboard_data = {
        "stats": {
            "articles": 0,
            "users": 0,
            "edits": 0,
            "categories": 0
        },
        "recent_activities": [],
        "announcements": [],
        "events": [],
        "top_contributors": []
    }
    
    try:
        # Get article stats
        dashboard_data["stats"]["articles"] = await db["articles"].count_documents({"status": "published"})
        
        # Get user stats
        dashboard_data["stats"]["users"] = await db["users"].count_documents({})
        
        # Get edit stats
        dashboard_data["stats"]["edits"] = await db["revisions"].count_documents({})
        
        # Get category count using aggregation
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories"}},
            {"$count": "total"}
        ]
        
        categories_count = await db["articles"].aggregate(pipeline).to_list(length=1)
        if categories_count and len(categories_count) > 0:
            dashboard_data["stats"]["categories"] = categories_count[0]["total"]
        
        # Get recent activity
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            
            if article and user:
                dashboard_data["recent_activities"].append({
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
                dashboard_data["recent_activities"].append({
                    "type": "Proposal",
                    "timestamp": prop["proposedAt"],
                    "articleId": str(prop["articleId"]),
                    "articleTitle": article["title"],
                    "username": user["username"]
                })
        
        # Sort activities by timestamp
        dashboard_data["recent_activities"].sort(key=lambda x: x["timestamp"], reverse=True)
        dashboard_data["recent_activities"] = dashboard_data["recent_activities"][:10]
        
        # Get sample announcements
        dashboard_data["announcements"] = [
            {
                "title": "New Article Categories Added",
                "date": datetime.now() - timedelta(days=2),
                "content": "We've added new categories to better organize our growing collection of articles."
            },
            {
                "title": "Community Call for Contributors",
                "date": datetime.now() - timedelta(days=5),
                "content": "We're looking for experts in various fields to contribute to our knowledge base."
            }
        ]
        
        # Get sample events
        dashboard_data["events"] = [
            {
                "title": "Monthly Community Meeting",
                "date": datetime.now() + timedelta(days=7),
                "description": "Join us for our monthly community meeting to discuss the future of Kryptopedia.",
                "link": "#"
            },
            {
                "title": "Contributor Workshop",
                "date": datetime.now() + timedelta(days=14),
                "description": "Learn how to effectively contribute to Kryptopedia in this online workshop.",
                "link": "#"
            }
        ]
        
        # Get top contributors
        contributors_cursor = db["users"].find().sort("contributions.editsPerformed", -1).limit(5)
        dashboard_data["top_contributors"] = await contributors_cursor.to_list(length=5)
        
        # Remove sensitive information from contributors
        for contributor in dashboard_data["top_contributors"]:
            if "passwordHash" in contributor:
                del contributor["passwordHash"]
        
        # If we end up with all zeros and no real data, use sample data
        if (dashboard_data["stats"]["articles"] == 0 and
            dashboard_data["stats"]["users"] == 0 and
            dashboard_data["stats"]["edits"] == 0 and
            dashboard_data["stats"]["categories"] == 0):
            
            dashboard_data["stats"] = {
                "articles": 42,
                "users": 15,
                "edits": 128,
                "categories": 8
            }
        
        # Cache the dashboard data
        await cache.set(cache_key, dashboard_data, 900)  # Cache for 15 minutes
        
    except Exception as e:
        logger.error(f"Error getting community dashboard data: {e}")
        # Use default data in case of errors
    
    # Render template with our data
    return templates.TemplateResponse(
        "community.html",
        {
            "request": request,
            **dashboard_data
        }
    )

@router.get("/community/extra", response_class=HTMLResponse)
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

        # Add stats dictionary to be compatible with the first endpoint
        stats = {
            "articles": 42,  # Sample data
            "users": 15,     # Sample data
            "edits": 128,    # Sample data
            "categories": 8  # Sample data
        }
        
        # Log for debugging
        logger.info(f"Community extra page - using stats: {stats}")
        
        # Render template with both sets of variables for compatibility
        return templates.TemplateResponse(
            "community.html",
            {
                "request": request,
                "active_users": data["active_users"],
                "recent_revisions": data["recent_revisions"],
                "top_contributors": data["top_contributors"],
                "recent_discussions": data["recent_discussions"],
                "upcoming_events": data["upcoming_events"],
                # Add these for compatibility with the main community endpoint
                "stats": stats,
                "recent_activities": data["recent_revisions"],  # Reuse recent_revisions
                "announcements": [],
                "events": data["upcoming_events"]  # Reuse upcoming_events
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
