# File: pages/help.py
"""
Help page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
import logging

from dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request, db=Depends(get_db)):
    """
    Render the main help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help.html",
        {"request": request}
    )

@router.get("/help/formatting", response_class=HTMLResponse)
async def formatting_guide(request: Request):
    """
    Render the formatting guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_formatting.html",
        {"request": request}
    )

@router.get("/help/references", response_class=HTMLResponse)
async def references_guide(request: Request):
    """
    Render the references guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_references.html",
        {"request": request}
    )

@router.get("/help/media", response_class=HTMLResponse)
async def media_guide(request: Request):
    """
    Render the media guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_media.html",
        {"request": request}
    )

@router.get("/help/categories", response_class=HTMLResponse)
async def categories_guide(request: Request):
    """
    Render the categories guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_categories.html",
        {"request": request}
    )

# File: pages/community.py
"""
Community page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
import logging

from dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/community", response_class=HTMLResponse)
async def community_page(request: Request, db=Depends(get_db)):
    """
    Render the community portal page.
    """
    templates = request.app.state.templates
    
    try:
        # Gather statistics
        stats = {}
        
        # Article stats
        stats["articles"] = await db["articles"].count_documents({"status": "published"})
        
        # User stats
        stats["users"] = await db["users"].count_documents({})
        
        # Edits count
        stats["edits"] = await db["revisions"].count_documents({})
        
        # Categories count
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories"}},
            {"$count": "total"}
        ]
        
        categories_count = await db["articles"].aggregate(pipeline).to_list(length=1)
        stats["categories"] = categories_count[0]["total"] if categories_count else 0
        
        # Get recent activity
        recent_activities = []
        
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            
            if article and user:
                recent_activities.append({
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
                recent_activities.append({
                    "type": "Proposal",
                    "timestamp": prop["proposedAt"],
                    "articleId": str(prop["articleId"]),
                    "articleTitle": article["title"],
                    "username": user["username"]
                })
        
        # Sort by timestamp and limit to 10
        recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activities = recent_activities[:10]
        
        # Get announcements (in a real app, these would come from a database)
        announcements = [
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
        
        # Get upcoming events (in a real app, these would come from a database)
        events = [
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
        top_contributors_cursor = db["users"].find().sort("contributions.editsPerformed", -1).limit(10)
        top_contributors = await top_contributors_cursor.to_list(length=10)
        
        return templates.TemplateResponse(
            "community.html",
            {
                "request": request,
                "stats": stats,
                "recent_activities": recent_activities,
                "announcements": announcements,
                "events": events,
                "top_contributors": top_contributors
            }
        )
    except Exception as e:
        logger.error(f"Error in community page: {e}")
        return templates.TemplateResponse(
            "community.html",
            {
                "request": request,
                "stats": {"articles": 0, "users": 0, "edits": 0, "categories": 0},
                "recent_activities": [],
                "announcements": [],
                "events": [],
                "top_contributors": []
            }
        )

# File: pages/donate.py
"""
Donation page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
import logging

from dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/donate", response_class=HTMLResponse)
async def donate_page(request: Request, db=Depends(get_db)):
    """
    Render the donation page.
    """
    templates = request.app.state.templates
    
    # Get top donors (in a real app, these would come from a database)
    top_donors = [
        {"name": "Anonymous"},
        {"name": "Jane Smith"},
        {"name": "John Doe"},
        {"name": "Acme Corporation"},
        {"name": "Tech Innovations LLC"}
    ]
    
    return templates.TemplateResponse(
        "donate.html",
        {
            "request": request,
            "top_donors": top_donors
        }
    )
