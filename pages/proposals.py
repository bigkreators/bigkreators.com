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
    
    # Render template
    return templates.TemplateResponse(
        "propose_edit.html",
        {"request": request, "article": article}
    )

@router.get("/proposals", response_class=HTMLResponse)
async def proposals_list_page(
    request: Request,
    status: Optional[str] = None,
    article_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the page listing edit proposals.
    """
    templates = request.app.state.templates
    
    # Build query
    query = {}
    if status and status != "all":
        query["status"] = status
    
    if article_id and ObjectId.is_valid(article_id):
        query["articleId"] = ObjectId(article_id)
    
    # Get proposals
    cursor = db["proposals"].find(query).sort("proposedAt", -1).skip(skip).limit(limit)
    proposals = await cursor.to_list(length=limit)
    
    # Get total count
    total_count = await db["proposals"].count_documents(query)
    
    # Enhance proposals with article info
    enhanced_proposals = []
    for prop in proposals:
        # Get article info
        article = await db["articles"].find_one({"_id": prop["articleId"]})
        article_title = article["title"] if article else "Unknown Article"
        
        # Get user info
        proposer = await db["users"].find_one({"_id": prop["proposedBy"]})
        proposer_username = proposer["username"] if proposer else "Unknown"
        
        # Get reviewer info if available
        reviewer_username = None
        if prop.get("reviewedBy"):
            reviewer = await db["users"].find_one({"_id": prop["reviewedBy"]})
            reviewer_username = reviewer["username"] if reviewer else "Unknown"
        
        # Add enhanced info
        enhanced_proposals.append({
            **prop,
            "articleTitle": article_title,
            "proposerUsername": proposer_username,
            "reviewerUsername": reviewer_username
        })
    
    # Get article if filtering by article
    article = None
    if article_id and ObjectId.is_valid(article_id):
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    
    # Check if user is editor
    is_editor = False
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
            is_editor = current_user.get("role") in ["admin", "editor"]
    except:
        pass
    
    # Render template
    return templates.TemplateResponse(
        "proposals_list.html",
        {
            "request": request,
            "proposals": enhanced_proposals,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "status": status,
            "article": article,
            "is_editor": is_editor
        }
    )

@router.get("/articles/{article_id}/proposals", response_class=HTMLResponse)
async def article_proposals_page(
    request: Request,
    article_id: str,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the page listing proposals for a specific article.
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
    
    # Redirect to the general proposals page with article filter
    return RedirectResponse(
        url=f"/proposals?article_id={article_id}" + (f"&status={status}" if status else "")
    )

@router.get("/articles/{article_id}/proposals/{proposal_id}", response_class=HTMLResponse)
async def view_proposal_page(
    request: Request,
    article_id: str,
    proposal_id: str,
    db=Depends(get_db)
):
    """
    Render the page for viewing a specific proposal.
    """
    templates = request.app.state.templates
    
    # Check if article and proposal exist
    if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(proposal_id):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Invalid ID format"},
            status_code=404
        )
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    proposal = await db["proposals"].find_one({
        "_id": ObjectId(proposal_id),
        "articleId": ObjectId(article_id)
    })
    
    if not proposal:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Proposal not found"},
            status_code=404
        )
    
    # Get user info
    proposer = await db["users"].find_one({"_id": proposal["proposedBy"]})
    proposer_username = proposer["username"] if proposer else "Unknown"
    
    reviewer_username = None
    if proposal.get("reviewedBy"):
        reviewer = await db["users"].find_one({"_id": proposal["reviewedBy"]})
        reviewer_username = reviewer["username"] if reviewer else "Unknown"
    
    # Check if user is editor
    is_editor = False
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
            is_editor = current_user.get("role") in ["admin", "editor"]
    except:
        pass
    
    # Add user info to proposal
    enhanced_proposal = {
        **proposal,
        "proposerUsername": proposer_username,
        "reviewerUsername": reviewer_username
    }
    
    # Render template
    return templates.TemplateResponse(
        "proposal_view.html",
        {
            "request": request,
            "article": article,
            "proposal": enhanced_proposal,
            "is_editor": is_editor
        }
    )
