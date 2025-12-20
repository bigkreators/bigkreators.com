# File: routes/wiki.py
"""
Wiki-style routes for MediaWiki-like page access with K̡̓ONTRIB integration.
This integrates with your existing Kryptopedia FastAPI structure.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List
import logging
import re
from datetime import datetime

from dependencies import get_db, get_current_user, get_cache
from models.article import Article
from models.user import User
from utils.slug import create_slug

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/wiki/{page_title}", response_class=HTMLResponse)
async def wiki_page(
    request: Request,
    page_title: str,
    current_user: Optional[User] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Handle wiki-style page access like /wiki/Article_Name
    
    Returns:
    - Article content if exists
    - "Page does not exist" template for valid wiki pages that haven't been created
    - 404 HTTP error for invalid page titles or malformed URLs
    """
    
    # Validate page title format (prevent 404 scenarios)
    if not page_title or not is_valid_wiki_title(page_title):
        raise HTTPException(status_code=404, detail="Invalid page title")
    
    # Convert page title to slug format and back to readable title
    readable_title = page_title.replace('_', ' ')
    slug = create_slug(readable_title)
    
    # Additional validation after slug creation
    if not slug or len(slug) > 255:  # Reasonable limits
        raise HTTPException(status_code=404, detail="Invalid page title")
    
    try:
        # Try to find existing article
        articles_collection = db.get_collection("articles")
        article = await articles_collection.find_one({
            "$or": [
                {"slug": slug},
                {"title": readable_title},
                {"slug": page_title}  # Also try exact match
            ]
        })
        
        if article:
            # Article exists - render it
            article_obj = Article(**article)
            
            # Update view count
            await articles_collection.update_one(
                {"_id": article["_id"]},
                {"$inc": {"view_count": 1}}
            )
            
            # Get template from app state
            templates = request.app.state.templates
            
            return templates.TemplateResponse(
                "wiki_article.html",
                {
                    "request": request,
                    "article": article_obj,
                    "current_user": current_user,
                    "page_name": readable_title,
                    "page_title": readable_title
                }
            )
        else:
            # Valid wiki namespace, but article doesn't exist
            # Show "page does not exist" with K̡̓ONTRIB earning opportunity
            return await show_page_not_found(
                request, readable_title, current_user, db
            )
            
    except Exception as e:
        logger.error(f"Error accessing wiki page {page_title}: {e}")
        # Database errors should be 500, not 404
        raise HTTPException(status_code=500, detail="Internal server error")

def is_valid_wiki_title(title: str) -> bool:
    """
    Validate if a title is a valid wiki page title
    
    Returns False for malformed titles that should trigger 404
    Returns True for valid titles that can show "page does not exist"
    """
    if not title:
        return False
    
    # Remove underscores for validation
    clean_title = title.replace('_', ' ').strip()
    
    # Basic length check
    if len(clean_title) < 1 or len(clean_title) > 255:
        return False
    
    # Check for invalid characters that should be 404
    invalid_chars = ['<', '>', '|', '{', '}', '[', ']']
    if any(char in clean_title for char in invalid_chars):
        return False
    
    # Check for invalid patterns
    invalid_patterns = [
        '..',      # Directory traversal
        '//',      # Double slashes
        '\n',      # Newlines
        '\t',      # Tabs
    ]
    if any(pattern in title for pattern in invalid_patterns):
        return False
    
    # Reserved/system titles that should be 404
    reserved_titles = [
        'api', 'static', 'admin', 'auth', 'special',
        'favicon.ico', 'robots.txt', 'sitemap.xml'
    ]
    if clean_title.lower() in reserved_titles:
        return False
    
    return True

async def show_page_not_found(
    request: Request,
    page_title: str,
    current_user: Optional[User],
    db
):
    """
    Show the page does not exist template with K̡̓ONTRIB earning opportunities
    """
    
    # Get template from app state
    templates = request.app.state.templates
    
    # Look for similar articles (suggestions)
    suggestions = await get_similar_articles(page_title, db)
    
    # Get log events for this page title (deletions, moves, etc.)
    log_events = await get_page_log_events(page_title, db)
    
    return templates.TemplateResponse(
        "page_not_found.html",
        {
            "request": request,
            "page_title": page_title,
            "current_user": current_user,
            "suggestions": suggestions,
            "log_events": log_events
        }
    )

async def get_similar_articles(title: str, db) -> List[dict]:
    """
    Find articles with similar titles to suggest to the user
    """
    try:
        articles_collection = db.get_collection("articles")
        
        # Create regex pattern for similar titles
        title_words = title.lower().split()
        if title_words:
            # Search for articles containing any of the title words
            pattern = "|".join(re.escape(word) for word in title_words if len(word) > 2)
            
            if pattern:
                suggestions = await articles_collection.find(
                    {
                        "$or": [
                            {"title": {"$regex": pattern, "$options": "i"}},
                            {"content": {"$regex": pattern, "$options": "i"}}
                        ]
                    },
                    {"title": 1, "slug": 1, "summary": 1}
                ).limit(5).to_list(length=5)
                
                return suggestions
    except Exception as e:
        logger.error(f"Error finding similar articles: {e}")
    
    return []

async def get_page_log_events(title: str, db) -> List[dict]:
    """
    Get log events (deletions, moves, etc.) for this page title
    This would integrate with your existing logging system
    """
    try:
        # This would query your logs collection if you have one
        # For now, return empty list
        return []
    except Exception as e:
        logger.error(f"Error getting log events: {e}")
        return []

@router.post("/create", response_class=HTMLResponse)
async def quick_create_article(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Quick article creation from the "page does not exist" form
    Awards K̡̓ONTRIB tokens for creation
    """
    
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    try:
        slug = create_slug(title)
        
        # Check if article already exists
        articles_collection = db.get_collection("articles")
        existing = await articles_collection.find_one({"slug": slug})
        
        if existing:
            # Redirect to existing article
            return RedirectResponse(url=f"/wiki/{slug}", status_code=302)
        
        # Create new article
        new_article = {
            "title": title,
            "slug": slug,
            "content": content.strip(),
            "summary": content.strip()[:200] + "..." if len(content) > 200 else content.strip(),
            "author_id": current_user.id,
            "status": "published",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "view_count": 0,
            "edit_count": 1,
            "kontrib_earned": 0  # Will be updated by token system
        }
        
        result = await articles_collection.insert_one(new_article)
        
        # Award K̡̓ONTRIB tokens for article creation
        await award_kontrib_tokens(
            user_id=current_user.id,
            amount=50,  # Base creation reward
            action="article_creation",
            context=title,
            db=db
        )
        
        # Calculate length bonus
        word_count = len(content.split())
        if word_count >= 100:
            length_bonus = min(word_count // 25, 50)
            await award_kontrib_tokens(
                user_id=current_user.id,
                amount=length_bonus,
                action="content_length_bonus",
                context=f"{title} ({word_count} words)",
                db=db
            )
        
        # Redirect to the new article
        return RedirectResponse(url=f"/wiki/{slug}", status_code=302)
        
    except Exception as e:
        logger.error(f"Error creating article {title}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create article")

@router.get("/edit/{page_title}", response_class=HTMLResponse)
async def edit_wiki_page(
    request: Request,
    page_title: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Show edit interface for wiki page (existing or new)
    """
    
    readable_title = page_title.replace('_', ' ')
    slug = create_slug(readable_title)
    
    # Try to find existing article
    articles_collection = db.get_collection("articles")
    article = await articles_collection.find_one({"slug": slug})
    
    # Get template from app state
    templates = request.app.state.templates
    
    if article:
        # Editing existing article
        article_obj = Article(**article)
        return templates.TemplateResponse(
            "wiki_edit.html",  # We'll create this
            {
                "request": request,
                "article": article_obj,
                "current_user": current_user,
                "page_title": readable_title,
                "is_new": False
            }
        )
    else:
        # Creating new article
        return templates.TemplateResponse(
            "wiki_edit.html",
            {
                "request": request,
                "article": None,
                "current_user": current_user,
                "page_title": readable_title,
                "is_new": True
            }
        )

async def award_kontrib_tokens(
    user_id: str,
    amount: float,
    action: str,
    context: str,
    db
):
    """
    Award K̡̓ONTRIB tokens to a user
    This integrates with your existing token system
    """
    try:
        # Update user's token balance
        users_collection = db.get_collection("users")
        await users_collection.update_one(
            {"_id": user_id},
            {
                "$inc": {"kontrib_balance": amount},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Record the transaction
        transactions_collection = db.get_collection("kontrib_transactions")
        await transactions_collection.insert_one({
            "user_id": user_id,
            "amount": amount,
            "action": action,
            "context": context,
            "timestamp": datetime.utcnow(),
            "status": "completed"
        })
        
        logger.info(f"Awarded {amount} K̡̓ontrib to user {user_id} for {action}: {context}")
        
    except Exception as e:
        logger.error(f"Error awarding K̡̓ontrib tokens: {e}")

# Additional wiki-style routes

@router.get("/talk/{page_title}", response_class=HTMLResponse)
async def talk_page(
    request: Request,
    page_title: str,
    current_user: Optional[User] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Show talk/discussion page for an article
    """
    readable_title = page_title.replace('_', ' ')
    
    # Get template from app state
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "wiki_talk.html",
        {
            "request": request,
            "page_title": readable_title,
            "current_user": current_user
        }
    )

@router.get("/history/{page_title}", response_class=HTMLResponse)
async def page_history(
    request: Request,
    page_title: str,
    current_user: Optional[User] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Show revision history for a wiki page
    """
    readable_title = page_title.replace('_', ' ')
    slug = create_slug(readable_title)
    
    # Get revision history
    revisions_collection = db.get_collection("revisions")
    revisions = await revisions_collection.find(
        {"article_slug": slug}
    ).sort("created_at", -1).limit(50).to_list(length=50)
    
    # Get template from app state
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "wiki_history.html",
        {
            "request": request,
            "page_title": readable_title,
            "revisions": revisions,
            "current_user": current_user
        }
    )

# Route for handling redirects and alternative titles
@router.get("/", response_class=HTMLResponse)
async def main_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Handle main page (like Wikipedia's front page)
    """
    return RedirectResponse(url="/wiki/Main_Page", status_code=302)
