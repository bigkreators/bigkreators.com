"""
Home page and core navigation routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import logging

from dependencies import get_db, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

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
