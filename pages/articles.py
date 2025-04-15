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
            # Parse wiki markup
            parsed_content, short_description = parse_wiki_markup(cached_article["content"])
            
            # Update view count in background
            await db["articles"].update_one(
                {"_id": cached_article["_id"]},
                {"$inc": {"views": 1}}
            )
            
            return templates.TemplateResponse(
                "article_wiki.html",
                {
                    "request": request,
                    "article": cached_article,
                    "parsed_content": parsed_content,
                    "short_description": short_description,
                    "current_user": current_user
                }
            )
        
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
        
        # Parse wiki markup
        parsed_content, short_description = parse_wiki_markup(article["content"])
        
        # Update view count
        await db["articles"].update_one(
            {"_id": article["_id"]},
            {"$inc": {"views": 1}}
        )
        
        # Cache article
        await cache.set(cache_key, article, 3600)  # Cache for 1 hour
        
        # Render article
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
    except Exception as e:
        logger.error(f"Error rendering article: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Error rendering article"},
            status_code=500
        )

# File: pages/articles.py

# Add to the existing file

@router.get("/create-article-wiki", response_class=HTMLResponse)
async def create_article_wiki_page(request: Request):
    """
    Render the wiki-style article creation page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "create_article_wiki.html",
        {"request": request}
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

# File: pages/proposals.py

# Add to the existing router

@router.get("/articles/{article_id}/propose-wiki", response_class=HTMLResponse)
async def propose_edit_wiki_page(
    request: Request,
    article_id: str = Path(..., description="Article ID"),
    db=Depends(get_db)
):
    """
    Render the wiki-style page for creating an edit proposal.
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
        "propose_edit_wiki.html",
        {"request": request, "article": article}
    )

# File: pages/articles.py

# Add to the existing file

@router.get("/articles/{article_id}/talk", response_class=HTMLResponse)
async def article_talk_page(
    request: Request,
    article_id: str,
    db=Depends(get_db)
):
    """
    Render the article talk/discussion page.
    """
    templates = request.app.state.templates
    
    try:
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
        
        # Get talk sections for this article
        cursor = db["talk_sections"].find({"articleId": ObjectId(article_id)}).sort("createdAt", -1)
        talk_sections = await cursor.to_list(length=100)
        
        # Enhance sections with comments
        enhanced_sections = []
        for section in talk_sections:
            # Get comments for this section
            comments_cursor = db["talk_comments"].find({
                "sectionId": section["_id"]
            }).sort("createdAt", 1)
            
            comments = await comments_cursor.to_list(length=100)
            
            # Enhance comments with user info
            enhanced_comments = []
            for comment in comments:
                user = await db["users"].find_one({"_id": comment["userId"]})
                username = user["username"] if user else "Unknown"
                
                enhanced_comments.append({
                    **comment,
                    "username": username
                })
            
            enhanced_sections.append({
                **section,
                "comments": enhanced_comments
            })
        
        # Get current user
        current_user = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
        except:
            pass
        
        # Render the talk page template
        return templates.TemplateResponse(
            "talk_page.html",
            {
                "request": request,
                "article": article,
                "talk_sections": enhanced_sections,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error loading talk page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading talk page: {str(e)}"},
            status_code=500
        )
