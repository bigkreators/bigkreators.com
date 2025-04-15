# File: pages/proposals.py

"""
Proposal-related page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, Path, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from typing import Optional
import logging

from dependencies import get_db, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/articles/{article_id}/propose", response_class=HTMLResponse)
async def propose_edit_page(
    request: Request,
    article_id: str = Path(..., description="Article ID"),
    mode: str = Query("wiki", description="Edit mode: wiki or html"),
    db=Depends(get_db)
):
    """
    Render the page for creating an edit proposal.
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
    template_name = "propose_edit_wiki.html" if mode == "wiki" else "propose_edit.html"
    
    # Render template
    return templates.TemplateResponse(
        template_name,
        {"request": request, "article": article, "mode": mode}
    )
