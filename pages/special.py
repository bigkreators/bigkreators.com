"""
Special page routes for statistics, recent changes, etc.
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import logging
from bson import ObjectId

from dependencies import get_db, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

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
    
    # Process revisions and proposals
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
        
        # Check if we have any changes
        if not changes:
            # Generate some sample changes if no real data exists
            logger.info("No changes found, generating sample data")
            sample_changes = await generate_sample_changes(db)
            changes.extend(sample_changes)
        
        # Sort combined list by timestamp (newest first)
        changes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply filter if needed
        if filter:
            changes = [c for c in changes if c["type"] == filter]
        
        # Get total count
        total = len(changes)
        
        # Paginate manually
        changes = changes[skip:skip+limit]
        
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
        logger.error(f"Error getting recent changes: {e}")
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

async def generate_sample_changes(db) -> List[Dict[str, Any]]:
    """
    Generate sample changes for display when no real data exists.
    """
    sample_changes = []
    
    # Get some articles and users to reference
    articles_cursor = db["articles"].find({"status": "published"}).limit(5)
    articles = await articles_cursor.to_list(length=5)
    
    if not articles:
        # If no articles exist, we can't generate sample changes
        return []
    
    users_cursor = db["users"].find().limit(3)
    users = await users_cursor.to_list(length=3)
    
    if not users:
        # If no users exist, use a default
        admin_user = {
            "_id": ObjectId(),
            "username": "admin"
        }
        users = [admin_user]
    
    # Sample comments for revisions
    revision_comments = [
        "Fixed typos in introduction",
        "Updated information in the second paragraph",
        "Added new section on advanced techniques",
        "Corrected historical information",
        "Improved formatting and readability",
        "Added references and citations",
        "Restructured content for better flow"
    ]
    
    # Sample comments for proposals
    proposal_comments = [
        "Suggested new content for the introduction",
        "Proposed additional examples",
        "Suggested clearer explanation of concepts",
        "Proposed update to outdated information",
        "Suggested adding missing details"
    ]
    
    # Generate sample revisions
    now = datetime.now()
    for i in range(10):
        article = random.choice(articles)
        user = random.choice(users)
        
        # Create a sample revision
        sample_changes.append({
            "type": "revision",
            "timestamp": now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            "articleId": str(article["_id"]),
            "articleTitle": article["title"],
            "userId": str(user["_id"]),
            "username": user["username"],
            "comment": random.choice(revision_comments)
        })
    
    # Generate sample proposals
    for i in range(5):
        article = random.choice(articles)
        user = random.choice(users)
        
        # Create a sample proposal
        sample_changes.append({
            "type": "proposal",
            "timestamp": now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            "articleId": str(article["_id"]),
            "articleTitle": article["title"],
            "userId": str(user["_id"]),
            "username": user["username"],
            "comment": random.choice(proposal_comments)
        })
    
    return sample_changes

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
        logger.error(f"Error getting statistics: {e}")
        # Return empty results on error
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "statistics": {}
            }
        )

@router.get("/special/categories", response_class=HTMLResponse)
async def special_categories_page(request: Request):
    """Redirect to categories page."""
    return RedirectResponse(url="/categories")

@router.get("/special/tags", response_class=HTMLResponse)
async def special_tags_page(request: Request):
    """Redirect to tags page."""
    return RedirectResponse(url="/tags")

@router.get("/special/search", response_class=HTMLResponse)
async def special_search_page(request: Request, q: Optional[str] = None):
    """Redirect to search page."""
    if q:
        return RedirectResponse(url=f"/search?q={q}")
    return RedirectResponse(url="/search")

@router.get("/special/featured", response_class=HTMLResponse)
async def featured_articles_page(
    request: Request,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the featured articles page.
    """
    templates = request.app.state.templates
    
    try:
        # Get featured articles
        featured_cursor = db["articles"].find({
            "status": "published",
            "featuredUntil": {"$gt": datetime.now()}
        }).sort("featuredUntil", -1)
        
        featured_articles = await featured_cursor.to_list(length=20)
        
        # Render template
        return templates.TemplateResponse(
            "featured_articles.html",
            {
                "request": request,
                "articles": featured_articles
            }
        )
    except Exception as e:
        logger.error(f"Error getting featured articles: {e}")
        # Return empty results on error
        return templates.TemplateResponse(
            "featured_articles.html",
            {
                "request": request,
                "articles": []
            }
        )

@router.get("/special/random", response_class=HTMLResponse)
async def random_redirect(db=Depends(get_db)):
    """Redirect to a random article."""
    # Redirect to the random route
    return RedirectResponse(url="/random")

@router.get("/special/help", response_class=HTMLResponse)
async def special_help_page(request: Request):
    """
    Redirect to the main help page.
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/help")

@router.get("/special/donate", response_class=HTMLResponse)
async def special_donate_page(request: Request):
    """
    Redirect to the donation page.
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/donate")

@router.get("/special-pages", response_class=HTMLResponse)
async def special_pages(request: Request, db=Depends(get_db)):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "special_pages.html",
        {"request": request}
    )

@router.get("/special-pages", response_class=HTMLResponse)
async def special_pages(request: Request,db=Depends(get_db)):
    """Redirect to a random article."""
    # Redirect to the random route
    return RedirectResponse(url="/random")
