"""
Article-related page routes.
"""
from fastapi import APIRouter, Request, Depends, Path, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from typing import Optional, Dict, Any
import logging

from dependencies import get_db, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

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
    templates = request.app.state.templates
    
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

@router.get("/articles/{slug}", response_class=HTMLResponse)
async def article_page(
    request: Request, 
    slug: str = Path(..., description="Article slug or ID"),
    db=Depends(get_db)
):
    """
    Render an article page.
    """
    templates = request.app.state.templates
    
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
    
    # Get current user for editing permissions
    current_user = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
    except:
        pass
    
    # Render article template
    return templates.TemplateResponse(
        "article.html",
        {"request": request, "article": article, "current_user": current_user}
    )

@router.get("/create-article", response_class=HTMLResponse)
async def create_article_page(request: Request):
    """
    Render the article creation page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "create_article.html",
        {"request": request}
    )

@router.get("/edit-article/{article_id}", response_class=HTMLResponse)
async def edit_article_page(
    request: Request,
    article_id: str = Path(..., description="Article ID"),
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
    
    # Render template
    return templates.TemplateResponse(
        "edit_article.html",
        {"request": request, "article": article}
    )

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

@router.get("/articles/{article_id}/history", response_class=HTMLResponse)
async def article_history_page(
    request: Request,
    article_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the article history page.
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
        
        # Get revisions
        cursor = db["revisions"].find({"articleId": ObjectId(article_id)}).sort("createdAt", -1).skip(skip).limit(limit)
        revisions = await cursor.to_list(length=limit)
        
        # Enhance with user info
        enhanced_revisions = []
        for rev in revisions:
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            username = user["username"] if user else "Unknown"
            
            enhanced_revisions.append({
                **rev,
                "creatorUsername": username
            })
        
        # Get total count
        total = await db["revisions"].count_documents({"articleId": ObjectId(article_id)})
        
        # Get current user to check if they're an editor
        current_user = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
        except:
            pass
        
        is_editor = current_user and current_user.get("role") in ["admin", "editor"]
        
        # Render template
        return templates.TemplateResponse(
            "article_history.html",
            {
                "request": request,
                "article": article,
                "revisions": enhanced_revisions,
                "total": total,
                "skip": skip,
                "limit": limit,
                "is_editor": is_editor
            }
        )
    except Exception as e:
        print(f"Error getting article history: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading article history: {str(e)}"},
            status_code=500
        )

@router.get("/articles/{article_id}/revisions/{revision_id}", response_class=HTMLResponse)
async def article_revision_page(
    request: Request,
    article_id: str,
    revision_id: str,
    db=Depends(get_db)
):
    """
    Render the article revision page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if article and revision exist
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(revision_id):
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
        
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(article_id)
        })
        
        if not revision:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Revision not found"},
                status_code=404
            )
        
        # Get user info
        user = await db["users"].find_one({"_id": revision["createdBy"]})
        username = user["username"] if user else "Unknown"
        
        # Check if user is editor
        current_user = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
        except:
            pass
        
        is_editor = current_user and current_user.get("role") in ["admin", "editor"]
        
        # Render template
        return templates.TemplateResponse(
            "article_revision.html",
            {
                "request": request,
                "article": article,
                "revision": {**revision, "creatorUsername": username},
                "is_editor": is_editor
            }
        )
    except Exception as e:
        print(f"Error getting article revision: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading revision: {str(e)}"},
            status_code=500
        )

@router.get("/articles/{article_id}/compare/{old_id}/{new_id}", response_class=HTMLResponse)
async def article_compare_page(
    request: Request,
    article_id: str,
    old_id: str,
    new_id: str,
    db=Depends(get_db)
):
    """
    Render the article comparison page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if article and revisions exist
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(old_id) or not ObjectId.is_valid(new_id):
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
        
        old_revision = await db["revisions"].find_one({
            "_id": ObjectId(old_id),
            "articleId": ObjectId(article_id)
        })
        
        new_revision = await db["revisions"].find_one({
            "_id": ObjectId(new_id),
            "articleId": ObjectId(article_id)
        })
        
        if not old_revision or not new_revision:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "One or both revisions not found"},
                status_code=404
            )
        
        # Get user info
        old_user = await db["users"].find_one({"_id": old_revision["createdBy"]})
        new_user = await db["users"].find_one({"_id": new_revision["createdBy"]})
        
        old_revision["creatorUsername"] = old_user["username"] if old_user else "Unknown"
        new_revision["creatorUsername"] = new_user["username"] if new_user else "Unknown"
        
        # Render template
        return templates.TemplateResponse(
            "article_compare.html",
            {
                "request": request,
                "article": article,
                "old_revision": old_revision,
                "new_revision": new_revision
            }
        )
    except Exception as e:
        print(f"Error comparing revisions: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error comparing revisions: {str(e)}"},
            status_code=500
        )

@router.get("/articles/{article_id}/revisions/{revision_id}/restore", response_class=HTMLResponse)
async def article_restore_page(
    request: Request,
    article_id: str,
    revision_id: str,
    db=Depends(get_db)
):
    """
    Render the article restore confirmation page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if article and revision exist
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(revision_id):
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
        
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(article_id)
        })
        
        if not revision:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Revision not found"},
                status_code=404
            )
        
        # Get user info
        user = await db["users"].find_one({"_id": revision["createdBy"]})
        username = user["username"] if user else "Unknown"
        
        # Render template
        return templates.TemplateResponse(
            "article_restore_confirm.html",
            {
                "request": request,
                "article": article,
                "revision": {**revision, "creatorUsername": username}
            }
        )
    except Exception as e:
        print(f"Error loading restore page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading restore page: {str(e)}"},
            status_code=500
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

@router.get("/categories", response_class=HTMLResponse)
async def categories_list_page(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Render the categories list page.
    """
    templates = request.app.state.templates
    
    try:
        # Use aggregation to get unique categories and their count
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        categories = await db["articles"].aggregate(pipeline).to_list(length=limit)
        
        # Get total count
        total_pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories"}},
            {"$count": "total"}
        ]
        
        total_result = await db["articles"].aggregate(total_pipeline).to_list(length=1)
        total = total_result[0]["total"] if total_result else 0
        
        # Render template
        return templates.TemplateResponse(
            "categories.html",
            {
                "request": request,
                "categories": categories,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        print(f"Error getting categories: {e}")
        return templates.TemplateResponse(
            "categories.html",
            {
                "request": request,
                "categories": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }
        )

@router.get("/tags", response_class=HTMLResponse)
async def tags_list_page(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db)
):
    """
    Render the tags list page.
    """
    templates = request.app.state.templates
    
    try:
        # Use aggregation to get unique tags and their count
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        tags = await db["articles"].aggregate(pipeline).to_list(length=limit)
        
        # Get total count
        total_pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$count": "total"}
        ]
        
        total_result = await db["articles"].aggregate(total_pipeline).to_list(length=1)
        total = total_result[0]["total"] if total_result else 0
        
        # Render template
        return templates.TemplateResponse(
            "tags.html",
            {
                "request": request,
                "tags": tags,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        print(f"Error getting tags: {e}")
        return templates.TemplateResponse(
            "tags.html",
            {
                "request": request,
                "tags": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }
        )

@router.get("/quick-edit", response_class=HTMLResponse)
async def quick_edit_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Render the quick edit page for easily creating revisions.
    """
    templates = request.app.state.templates
    
    # Get all published articles
    cursor = db["articles"].find({"status": "published"}).sort("title", 1)
    articles = await cursor.to_list(length=100)
    
    return templates.TemplateResponse(
        "quick_edit.html",
        {
            "request": request,
            "articles": articles
        }
    )
