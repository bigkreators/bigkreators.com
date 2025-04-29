"""
Home page and core navigation routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timedelta
import logging
from bson import ObjectId

from dependencies import get_db, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db=Depends(get_db), cache=Depends(get_cache)):
    """
    Render the homepage template with dynamic content.
    """
    # Get the templates instance from the app state
    templates = request.app.state.templates
    
    try:
        # Try to get data from cache first
        cache_key = "homepage_data"
        cached_data = await cache.get(cache_key)
        
        if cached_data:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    **cached_data
                }
            )
        
        # Get featured article from cache or database
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
        
        # Get multiple featured articles for the home page
        featured_articles_cursor = db["articles"].find(
            {"status": "published"}
        ).sort("views", -1).limit(3)
        
        featured_articles = await featured_articles_cursor.to_list(length=3)
        
        # Get recent articles
        recent_articles_cursor = db["articles"].find(
            {"status": "published"}
        ).sort("createdAt", -1).limit(5)
        
        recent_articles = await recent_articles_cursor.to_list(length=5)
        
        # Get recent changes
        recent_changes = []
        
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            
            if article and user:
                recent_changes.append({
                    "type": "edit",
                    "title": article["title"],
                    "slug": article.get("slug", str(article["_id"])),
                    "user": user["username"],
                    "comment": rev.get("comment", ""),
                    "timestamp": rev["createdAt"]
                })
        
        # Get new articles
        new_articles_cursor = db["articles"].find(
            {"status": "published"}
        ).sort("createdAt", -1).limit(5)
        
        new_articles = await new_articles_cursor.to_list(length=5)
        
        for article in new_articles:
            user = await db["users"].find_one({"_id": article["createdBy"]})
            
            if user:
                recent_changes.append({
                    "type": "new",
                    "title": article["title"],
                    "slug": article.get("slug", str(article["_id"])),
                    "user": user["username"],
                    "comment": "New article created",
                    "timestamp": article["createdAt"]
                })
        
        # Sort combined changes by timestamp (newest first)
        recent_changes.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_changes = recent_changes[:5]  # Limit to 5 items
        
        # Get article counts for stats
        article_count = await db["articles"].count_documents({"status": "published"})
        edit_count = await db["revisions"].count_documents({})
        user_count = await db["users"].count_documents({})
        
        # Prepare data for template
        homepage_data = {
            "featured_article": featured_article,
            "featured_articles": featured_articles,
            "recent_articles": recent_articles,
            "recent_changes": recent_changes,
            "article_count": article_count,
            "edit_count": edit_count,
            "user_count": user_count
        }
        
        # Cache the homepage data
        await cache.set(cache_key, homepage_data, 300)  # Cache for 5 minutes
        
        # Render template with our data
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                **homepage_data
            }
        )
    except Exception as e:
        logger.error(f"Error rendering homepage: {e}")
        # Fallback to minimal template with error handling
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "featured_article": None,
                "featured_articles": [],
                "recent_articles": [],
                "recent_changes": [],
                "article_count": 0,
                "edit_count": 0,
                "user_count": 0,
                "error": str(e)
            }
        )

@router.get("/random", response_class=HTMLResponse)
async def random_article_page(request: Request, db=Depends(get_db)):
    """
    Display a random article or redirect to a random article.
    """
    # Use aggregation to get a random article
    pipeline = [
        {"$match": {"status": "published"}},
        {"$sample": {"size": 1}}
    ]
    
    results = await db["articles"].aggregate(pipeline).to_list(length=1)
    
    if not results:
        # No articles found, redirect to homepage
        return RedirectResponse(url="/")
    
    # Set active_page for highlighting in navigation
    article = results[0]
    
    # Increment view count
    await db["articles"].update_one(
        {"_id": article["_id"]},
        {"$inc": {"views": 1}}
    )
    
    # Render the article template with active_page set to 'random'
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "article.html",
        {
            "request": request, 
            "article": article,
            "active_page": "random"
        }
    )

@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """
    Render the help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help.html",
        {"request": request}
    )

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """
    Render the about page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "about.html",
        {"request": request}
    )

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """
    Render the privacy policy page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request}
    )

@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    """
    Render the terms of use page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "terms.html",
        {"request": request}
    )

@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """
    Render the contact page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "contact.html",
        {"request": request}
    )

@router.get("/community", response_class=HTMLResponse)
async def community_page(request: Request):
    """
    Render the community portal page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "community.html",
        {"request": request}
    )

@router.get("/contribute", response_class=HTMLResponse)
async def contribute_page(request: Request):
    """
    Render the contribute page with various options to contribute to the wiki.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "contribute.html",
        {"request": request}
    )

@router.get("/mission", response_class=HTMLResponse)
async def mission_page(request: Request):
    """
    Render the mission page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "mission.html",
        {"request": request}
    )

@router.get("/values", response_class=HTMLResponse)
async def values_page(request: Request):
    """
    Render the values page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "values.html",
        {"request": request}
    )

@router.get("/team", response_class=HTMLResponse)
async def team_page(request: Request):
    """
    Render the team page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "team.html",
        {"request": request}
    )

@router.get("/rules", response_class=HTMLResponse)
async def team_page(request: Request):
    """
    Render the team page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "community_rules.html",
        {"request": request}
    )

@router.get("/guides", response_class=HTMLResponse)
async def team_page(request: Request):
    """
    Render the team page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "editor_guide.html",
        {"request": request}
    )

