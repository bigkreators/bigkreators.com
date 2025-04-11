"""
Template routes for the Cryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from typing import Optional
from datetime import datetime

import config
from dependencies import get_db, get_cache

# Initialize templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db=Depends(get_db), cache=Depends(get_cache)):
    """
    Render the homepage template.
    """
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

@router.get("/articles/{slug}", response_class=HTMLResponse)
async def article_page(
    request: Request, 
    slug: str = Path(..., description="Article slug or ID"),
    db=Depends(get_db)
):
    """
    Render an article page.
    """
    # Try to find article by slug
    article = await db["articles"].find_one({"slug": slug, "status": "published"})
    
    # If not found by slug, try ObjectId (if valid)
    if not article and ObjectId.is_valid(slug):
        article = await db["articles"].find_one({
            "_id": ObjectId(slug),
            "status": "published"
        })
    
    # If article not found, return 404
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    # Increment view count
    await db["articles"].update_one(
        {"_id": article["_id"]},
        {"$inc": {"views": 1}}
    )
    
    # Render article template
    return templates.TemplateResponse(
        "article.html",
        {"request": request, "article": article}
    )

@router.get("/articles", response_class=HTMLResponse)
async def articles_list_page(
    request: Request,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the articles list page.
    """
    # Build query
    query = {"status": "published"}
    if category:
        query["categories"] = category
    if tag:
        query["tags"] = tag
    
    # Get total count
    total_count = await db["articles"].count_documents(query)
    
    # Get articles
    cursor = db["articles"].find(query).sort("createdAt", -1).skip(skip).limit(limit)
    articles = await cursor.to_list(length=limit)
    
    # Render template
    return templates.TemplateResponse(
        "articles_list.html",
        {
            "request": request,
            "articles": articles,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "category": category,
            "tag": tag
        }
    )

@router.get("/create-article", response_class=HTMLResponse)
async def create_article_page(request: Request):
    """
    Render the article creation page.
    """
    return templates.TemplateResponse(
        "create_article.html",
        {"request": request}
    )

@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Render the search results page.
    """
    results = []
    
    if q:
        # Perform simple text search
        try:
            cursor = db["articles"].find(
                {"$text": {"$search": q}, "status": "published"},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(20)
            
            results = await cursor.to_list(length=20)
        except Exception as e:
            print(f"Search error: {str(e)}")
    
    # Render template
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "query": q or "", "results": results}
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
