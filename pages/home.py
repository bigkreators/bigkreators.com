"""
Homepage and basic page routes.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime

import config
from dependencies import get_db, get_cache

router = APIRouter()

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

@router.get("/random", response_class=RedirectResponse)
async def random_article(db=Depends(get_db)):
    """
    Redirect to a random article.
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
    
    # Redirect to the random article
    return RedirectResponse(url=f"/articles/{results[0]['slug']}")
