"""
Page routes for the Kryptopedia application.
Uses the template engine instance from the main application.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import config
from dependencies import get_db, get_cache, get_current_user, get_search

router = APIRouter()

# Existing routes...
@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db=Depends(get_db), cache=Depends(get_cache)):
    """
    Render the homepage template.
    """
    # Get the templates instance from the app state
    templates = request.app.state.templates
    
    # Try to get featured article from cache
    featured_article = await cache.get("featured_article")
    
    # If not in cache, fetch from database
    if not featured_article:
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
        
        # Cache featured article for 1 hour
        if featured_article:
            await cache.set("featured_article", featured_article, 3600)
    
    # Get recent articles
    recent_articles = []
    cursor = db["articles"].find({"status": "published"}).sort("createdAt", -1).limit(3)
    recent_articles = await cursor.to_list(length=3)
    
    # Render template
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "featured_article": featured_article,
            "recent_articles": recent_articles
        }
    )

# Add new special pages routes
@router.get("/special/recentchanges", response_class=HTMLResponse)
async def recent_changes_page(
    request: Request,
    filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the recent changes page.
    """
    templates = request.app.state.templates
    
    # Try to get from cache
    cache_key = f"recent_changes:{filter}:{skip}:{limit}"
    cached_data = await cache.get(cache_key)
    
    if cached_data:
        return templates.TemplateResponse(
            "recent_changes.html",
            {
                "request": request,
                "changes": cached_data["changes"],
                "total": cached_data["total"],
                "skip": skip,
                "limit": limit,
                "filter": filter
            }
        )
    
    # Build query for different filters
    if filter == "edits":
        pipeline = [
            {"$match": {"type": "revision"}},
            {"$sort": {"createdAt": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        count_pipeline = [
            {"$match": {"type": "revision"}},
            {"$count": "total"}
        ]
    elif filter == "new":
        pipeline = [
            {"$match": {"type": "new"}},
            {"$sort": {"createdAt": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        count_pipeline = [
            {"$match": {"type": "new"}},
            {"$count": "total"}
        ]
    elif filter == "proposals":
        pipeline = [
            {"$match": {"type": "proposal"}},
            {"$sort": {"createdAt": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        count_pipeline = [
            {"$match": {"type": "proposal"}},
            {"$count": "total"}
        ]
    else:
        # All changes
        pipeline = [
            {"$sort": {"createdAt": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        count_pipeline = [
            {"$count": "total"}
        ]
    
    # Alternative method using a simple approach since the revisions collection is already structured
    try:
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).skip(skip).limit(limit)
        revisions = await revisions_cursor.to_list(length=limit)
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).skip(skip).limit(limit)
        proposals = await proposals_cursor.to_list(length=limit)
        
        # Combine and sort by date
        changes = []
        
        # Process revisions
        for rev in revisions:
            # Get article
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            if not article:
                continue
                
            # Get user
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            username = user["username"] if user else "Unknown"
            
            changes.append({
                "type": "revision",
                "timestamp": rev["createdAt"],
                "articleId": str(rev["articleId"]),
                "articleTitle": article["title"],
                "userId": str(rev["createdBy"]),
                "username": username,
                "comment": rev.get("comment", "")
            })
        
        # Process proposals
        for prop in proposals:
            # Get article
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            if not article:
                continue
                
            # Get user
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            username = user["username"] if user else "Unknown"
            
            changes.append({
                "type": "proposal",
                "timestamp": prop["proposedAt"],
                "articleId": str(prop["articleId"]),
                "articleTitle": article["title"],
                "userId": str(prop["proposedBy"]),
                "username": username,
                "comment": prop.get("summary", "")
            })
        
        # Sort combined list by timestamp (newest first)
        changes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply filter if needed
        if filter:
            changes = [c for c in changes if c["type"] == filter]
        
        # Get total count
        total = len(changes)
        
        # Paginate manually
        changes = changes[skip:skip+limit]
        
        # Cache the results
        await cache.set(cache_key, {"changes": changes, "total": total}, 300)  # Cache for 5 minutes
        
        # Render template
        return templates.TemplateResponse(
            "recent_changes.html",
            {
                "request": request,
                "changes": changes,
                "total": total,
                "skip": skip,
                "limit": limit,
                "filter": filter
            }
        )
    except Exception as e:
        print(f"Error getting recent changes: {e}")
        # Return empty results on error
        return templates.TemplateResponse(
            "recent_changes.html",
            {
                "request": request,
                "changes": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "filter": filter
            }
        )

@router.get("/special/statistics", response_class=HTMLResponse)
async def statistics_page(
    request: Request,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the statistics page.
    """
    templates = request.app.state.templates
    
    # Try to get from cache
    cache_key = "statistics_page"
    cached_data = await cache.get(cache_key)
    
    if cached_data:
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "statistics": cached_data
            }
        )
    
    try:
        # Get statistics
        statistics = {}
        
        # Article stats
        statistics["total_articles"] = await db["articles"].count_documents({"status": "published"})
        statistics["total_edits"] = await db["revisions"].count_documents({})
        statistics["total_proposals"] = await db["proposals"].count_documents({})
        
        # User stats
        statistics["total_users"] = await db["users"].count_documents({})
        statistics["new_users_today"] = await db["users"].count_documents({
            "joinDate": {"$gte": datetime.now() - timedelta(days=1)}
        })
        
        # Most active users
        top_editors_cursor = db["users"].find().sort("contributions.editsPerformed", -1).limit(5)
        statistics["top_editors"] = await top_editors_cursor.to_list(length=5)
        
        # Most viewed articles
        top_articles_cursor = db["articles"].find({"status": "published"}).sort("views", -1).limit(5)
        statistics["top_articles"] = await top_articles_cursor.to_list(length=5)
        
        # Recent activity (last 24 hours)
        recent_revisions = await db["revisions"].count_documents({
            "createdAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        recent_proposals = await db["proposals"].count_documents({
            "proposedAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        
        statistics["recent_activity"] = {
            "revisions": recent_revisions,
            "proposals": recent_proposals,
            "total": recent_revisions + recent_proposals
        }
        
        # Cache the results
        await cache.set(cache_key, statistics, 1800)  # Cache for 30 minutes
        
        # Render template
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "statistics": statistics
            }
        )
    except Exception as e:
        print(f"Error getting statistics: {e}")
        # Return empty results on error
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "statistics": {}
            }
        )

# Add more necessary special pages here...
@router.get("/special/categories", response_class=HTMLResponse)
async def categories_page(request: Request, db=Depends(get_db)):
    """Redirect to categories page."""
    return RedirectResponse(url="/categories")

@router.get("/special/tags", response_class=HTMLResponse)
async def tags_page(request: Request, db=Depends(get_db)):
    """Redirect to tags page."""
    return RedirectResponse(url="/tags")

# Keep other existing routes...
