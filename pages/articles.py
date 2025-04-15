# File: pages/articles.py

"""
Article page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, Dict, Any
import logging
from bson import ObjectId

from dependencies import get_db, get_current_user, get_cache
from utils.wiki_parser import parse_wiki_markup

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/articles/{slug_or_id}", response_class=HTMLResponse)
async def article_page(
    request: Request,
    slug_or_id: str = Path(..., description="Article slug or ID"),
    mode: str = Query("wiki", description="View mode: wiki or html"),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the article page.
    """
    templates = request.app.state.templates
    
    try:
        # Try to get current user
        current_user = None
        try:
            from dependencies.auth import get_current_user_from_request
            current_user = await get_current_user_from_request(request, db)
        except:
            pass
        
        # Try to get from cache first
        cache_key = f"article:{slug_or_id}"
        cached_article = await cache.get(cache_key)
        
        if cached_article:
            article = cached_article
            
            # Update view count in background
            await db["articles"].update_one(
                {"_id": article["_id"]},
                {"$inc": {"views": 1}}
            )
        else:
            # Get article by slug or ID
            article = None
            
            # Check if it's a valid ObjectId
            if len(slug_or_id) == 24 and all(c in "0123456789abcdef" for c in slug_or_id):
                article = await db["articles"].find_one({"_id": ObjectId(slug_or_id)})
            
            # If not found by ID, try slug
            if not article:
                article = await db["articles"].find_one({"slug": slug_or_id})
            
            # If still not found, return 404
            if not article:
                return templates.TemplateResponse(
                    "404.html",
                    {"request": request, "message": "Article not found"},
                    status_code=404
                )
            
            # Cache article
            await cache.set(cache_key, article, 3600)  # Cache for 1 hour
            
            # Update view count
            await db["articles"].update_one(
                {"_id": article["_id"]},
                {"$inc": {"views": 1}}
            )
        
        # Check article status
        if article.get("status") not in ["published", None]:
            # Only allow admins, editors, and the creator to view non-published articles
            if not current_user or (
                current_user["role"] not in ["admin", "editor"] and
                str(current_user["_id"]) != str(article["createdBy"])
            ):
                return templates.TemplateResponse(
                    "403.html",
                    {"request": request, "message": "This article is not currently published"},
                    status_code=403
                )
        
        # Choose template based on mode
        if mode == "wiki":
            # Parse wiki markup if using wiki mode
            parsed_content, short_description = parse_wiki_markup(article["content"])
            
            return templates.TemplateResponse(
                "article_wiki.html",
                {
                    "request": request,
                    "article": article,
                    "parsed_content": parsed_content,
                    "short_description": short_description,
                    "current_user": current_user
                }
            )
        else:
            # Return HTML mode
            return templates.TemplateResponse(
                "article.html",
                {
                    "request": request,
                    "article": article,
                    "current_user": current_user
                }
            )
    except Exception as e:
        logger.error(f"Error rendering article: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Error rendering article"},
            status_code=500
        )

@router.get("/create-article", response_class=HTMLResponse)
async def create_article_page(
    request: Request,
    mode: str = Query("wiki", description="Edit mode: wiki or html")
):
    """
    Render the article creation page.
    """
    templates = request.app.state.templates
    
    # Choose template based on mode
    template_name = "create_article_wiki.html" if mode == "wiki" else "create_article.html"
    
    return templates.TemplateResponse(
        template_name,
        {"request": request}
    )

@router.get("/edit-article/{article_id}", response_class=HTMLResponse)
async def edit_article_page(
    request: Request,
    article_id: str = Path(..., description="Article ID"),
    mode: str = Query("wiki", description="Edit mode: wiki or html"),
    db=Depends(get_db)
):
    """
    Render the article editing page.
    """
    templates = request.app.state.templates
    
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Invalid article ID"},
            status_code=404
        )
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    # Choose template based on mode
    template_name = "edit_article_wiki.html" if mode == "wiki" else "edit_article.html"
    
    # Render template
    return templates.TemplateResponse(
        template_name,
        {"request": request, "article": article}
    )

@router.get("/edit-article-wiki/{article_id}", response_class=HTMLResponse)
async def edit_article_wiki_page(
    request: Request,
    article_id: str = Path(..., description="Article ID"),
    db=Depends(get_db)
):
    """
    Render the wiki-style article editing page.
    """
    templates = request.app.state.templates
    
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Invalid article ID"},
            status_code=404
        )
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    # Render template
    return templates.TemplateResponse(
        "edit_article_wiki.html",
        {"request": request, "article": article}
    )
