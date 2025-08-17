# File: routes/articles.py

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request, Body
from fastapi.responses import HTMLResponse
from bson import ObjectId
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# Import necessary dependencies and models
from dependencies.auth import get_user_or_anonymous
from dependencies import get_db, get_search, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.delete("/{id}")
async def delete_article(
    id: str,
    request: Request,
    permanent: bool = Query(False, description="Permanently delete the article"),
    reason: str = Query("No reason provided", description="Reason for deletion"),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Handle article deletion with discussion system.
    - Authors can delete immediately
    - Others must create deletion request for discussion
    - Admins can override with permanent deletion
    """
    try:
        # Get user info
        user_info = await get_user_or_anonymous(request, db)
        
        if user_info["type"] == "anonymous":
            raise HTTPException(
                status_code=401,
                detail="You must be logged in to request article deletion"
            )
        
        user = user_info["user"]
        
        # Check if article exists
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get article author
        author = await db["users"].find_one({"_id": article["createdBy"]})
        is_author = str(article["createdBy"]) == str(user["_id"])
        is_admin = user["role"] == "admin"
        
        logger.info(f"User {user['username']} requesting deletion of article {id} (is_author: {is_author}, is_admin: {is_admin})")
        
        # Case 1: Author deleting their own article
        if is_author:
            if permanent:
                # Permanently delete
                await db["articles"].delete_one({"_id": ObjectId(id)})
                await db["revisions"].delete_many({"articleId": ObjectId(id)})
                await db["proposals"].delete_many({"articleId": ObjectId(id)})
                await db["rewards"].delete_many({"articleId": ObjectId(id)})
                
                # Remove any deletion requests for this article
                await db["deletion_requests"].delete_many({"articleId": ObjectId(id)})
                
                message = "Article permanently deleted by author"
            else:
                # Mark as archived
                await db["articles"].update_one(
                    {"_id": ObjectId(id)},
                    {"$set": {"status": "archived", "archivedAt": datetime.now(), "archivedBy": user["_id"]}}
                )
                message = "Article archived by author"
            
            # Clear from search and cache
            await _clear_article_from_search_and_cache(search, cache, id, article)
            
            return {"message": message, "deletedImmediately": True}
        
        # Case 2: Admin override
        elif is_admin and permanent:
            # Admin can force delete but should record reason
            await db["articles"].delete_one({"_id": ObjectId(id)})
            await db["revisions"].delete_many({"articleId": ObjectId(id)})
            await db["proposals"].delete_many({"articleId": ObjectId(id)})
            await db["rewards"].delete_many({"articleId": ObjectId(id)})
            
            # Log admin deletion
            await db["admin_actions"].insert_one({
                "action": "force_delete_article",
                "articleId": ObjectId(id),
                "articleTitle": article["title"],
                "adminId": user["_id"],
                "adminUsername": user["username"],
                "reason": reason,
                "timestamp": datetime.now()
            })
            
            await _clear_article_from_search_and_cache(search, cache, id, article)
            
            return {"message": "Article permanently deleted by admin", "deletedImmediately": True}
        
        # Case 3: Others requesting deletion - create deletion request
        else:
            # Check if deletion request already exists
            existing_request = await db["deletion_requests"].find_one({
                "articleId": ObjectId(id),
                "status": "pending"
            })
            
            if existing_request:
                raise HTTPException(
                    status_code=409,
                    detail="A deletion request for this article is already pending discussion"
                )
            
            # Create deletion request
            deletion_request = {
                "articleId": ObjectId(id),
                "articleTitle": article["title"],
                "requesterId": user["_id"],
                "requesterUsername": user["username"],
                "authorId": article["createdBy"],
                "authorUsername": author["username"] if author else "Unknown",
                "reason": reason,
                "status": "pending",
                "createdAt": datetime.now(),
                "discussionComments": [],
                "votes": {
                    "delete": [str(user["_id"])],  # Requester votes delete
                    "keep": []
                }
            }
            
            result = await db["deletion_requests"].insert_one(deletion_request)
            
            # Notify the author (could be expanded to email notification)
            await db["notifications"].insert_one({
                "userId": article["createdBy"],
                "type": "deletion_request",
                "title": f"Deletion requested for your article: {article['title']}",
                "message": f"{user['username']} has requested deletion of your article. Reason: {reason}",
                "articleId": ObjectId(id),
                "deletionRequestId": result.inserted_id,
                "createdAt": datetime.now(),
                "read": False
            })
            
            return {
                "message": "Deletion request created and author has been notified",
                "deletionRequestId": str(result.inserted_id),
                "deletedImmediately": False,
                "discussionUrl": f"/articles/{id}/deletion-discussion"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling article deletion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process article deletion: {str(e)}"
        )

async def _clear_article_from_search_and_cache(search, cache, article_id, article):
    """Helper function to clear article from search and cache"""
    # Remove from search
    if search:
        try:
            await search.delete(index="articles", id=article_id)
        except Exception as e:
            logger.error(f"Error removing article from search: {e}")
    
    # Clear cache
    if cache:
        try:
            await cache.delete(f"article:{article_id}")
            if article.get("slug"):
                await cache.delete(f"article:{article['slug']}")
            await cache.delete("featured_article")
            await cache.delete("recent_articles")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

# New routes for deletion discussion system

@router.get("/{id}/deletion-discussion", response_class=HTMLResponse)
async def article_deletion_discussion_page(
    request: Request,
    id: str,
    db=Depends(get_db)
):
    """
    Render the deletion discussion page.
    """
    templates = request.app.state.templates
    
    try:
        # Get article and deletion request
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        deletion_request = await db["deletion_requests"].find_one({
            "articleId": ObjectId(id),
            "status": "pending"
        })
        
        if not deletion_request:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "message": "No active deletion discussion for this article"},
                status_code=404
            )
        
        # Get current user
        user_info = await get_user_or_anonymous(request, db)
        
        return templates.TemplateResponse(
            "article_deletion_discussion.html",
            {
                "request": request,
                "article": article,
                "deletion_request": deletion_request,
                "user_info": user_info
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading deletion discussion: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading deletion discussion: {str(e)}"},
            status_code=500
        )

@router.post("/{id}/deletion-discussion/comment")
async def add_deletion_discussion_comment(
    id: str,
    request: Request,
    comment_data: Dict[str, str] = Body(...),
    db=Depends(get_db)
):
    """
    Add a comment to the deletion discussion.
    """
    try:
        # Get user info
        user_info = await get_user_or_anonymous(request, db)
        
        if user_info["type"] == "anonymous":
            raise HTTPException(
                status_code=401,
                detail="You must be logged in to participate in discussions"
            )
        
        user = user_info["user"]
        comment_text = comment_data.get("comment", "").strip()
        
        if not comment_text:
            raise HTTPException(status_code=400, detail="Comment cannot be empty")
        
        # Get deletion request
        deletion_request = await db["deletion_requests"].find_one({
            "articleId": ObjectId(id),
            "status": "pending"
        })
        
        if not deletion_request:
            raise HTTPException(status_code=404, detail="No active deletion discussion found")
        
        # Add comment
        comment = {
            "userId": user["_id"],
            "username": user["username"],
            "comment": comment_text,
            "timestamp": datetime.now()
        }
        
        await db["deletion_requests"].update_one(
            {"_id": deletion_request["_id"]},
            {"$push": {"discussionComments": comment}}
        )
        
        return {"message": "Comment added to discussion", "comment": comment}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding discussion comment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add comment: {str(e)}"
        )

@router.post("/{id}/deletion-discussion/vote")
async def vote_on_deletion(
    id: str,
    request: Request,
    vote_data: Dict[str, str] = Body(...),
    db=Depends(get_db)
):
    """
    Vote on whether to delete or keep the article.
    """
    try:
        # Get user info
        user_info = await get_user_or_anonymous(request, db)
        
        if user_info["type"] == "anonymous":
            raise HTTPException(
                status_code=401,
                detail="You must be logged in to vote"
            )
        
        user = user_info["user"]
        vote = vote_data.get("vote")  # "delete" or "keep"
        
        if vote not in ["delete", "keep"]:
            raise HTTPException(status_code=400, detail="Vote must be 'delete' or 'keep'")
        
        # Get deletion request
        deletion_request = await db["deletion_requests"].find_one({
            "articleId": ObjectId(id),
            "status": "pending"
        })
        
        if not deletion_request:
            raise HTTPException(status_code=404, detail="No active deletion discussion found")
        
        user_id_str = str(user["_id"])
        
        # Remove user from both vote lists first
        await db["deletion_requests"].update_one(
            {"_id": deletion_request["_id"]},
            {
                "$pull": {
                    "votes.delete": user_id_str,
                    "votes.keep": user_id_str
                }
            }
        )
        
        # Add user to the appropriate vote list
        await db["deletion_requests"].update_one(
            {"_id": deletion_request["_id"]},
            {"$push": {f"votes.{vote}": user_id_str}}
        )
        
        return {"message": f"Voted to {vote} the article"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error voting on deletion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record vote: {str(e)}"
        )

@router.post("/{id}/deletion-discussion/resolve")
async def resolve_deletion_discussion(
    id: str,
    request: Request,
    resolution_data: Dict[str, str] = Body(...),
    db=Depends(get_db)
):
    """
    Resolve the deletion discussion (author or admin decision).
    """
    try:
        # Get user info
        user_info = await get_user_or_anonymous(request, db)
        
        if user_info["type"] == "anonymous":
            raise HTTPException(
                status_code=401,
                detail="You must be logged in to resolve discussions"
            )
        
        user = user_info["user"]
        decision = resolution_data.get("decision")  # "approve_deletion" or "reject_deletion"
        admin_comment = resolution_data.get("comment", "")
        
        if decision not in ["approve_deletion", "reject_deletion"]:
            raise HTTPException(
                status_code=400,
                detail="Decision must be 'approve_deletion' or 'reject_deletion'"
            )
        
        # Get article and deletion request
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        deletion_request = await db["deletion_requests"].find_one({
            "articleId": ObjectId(id),
            "status": "pending"
        })
        
        if not deletion_request:
            raise HTTPException(status_code=404, detail="No active deletion discussion found")
        
        # Check permissions
        is_author = str(article["createdBy"]) == str(user["_id"])
        is_admin = user["role"] == "admin"
        
        if not (is_author or is_admin):
            raise HTTPException(
                status_code=403,
                detail="Only the article author or an admin can resolve deletion discussions"
            )
        
        # Update deletion request
        resolution = {
            "resolvedBy": user["_id"],
            "resolvedByUsername": user["username"],
            "decision": decision,
            "comment": admin_comment,
            "resolvedAt": datetime.now()
        }
        
        await db["deletion_requests"].update_one(
            {"_id": deletion_request["_id"]},
            {
                "$set": {
                    "status": "resolved",
                    "resolution": resolution
                }
            }
        )
        
        # If approved, mark article for admin deletion
        if decision == "approve_deletion":
            await db["articles"].update_one(
                {"_id": ObjectId(id)},
                {"$set": {"pendingDeletion": True, "deletionApprovedAt": datetime.now()}}
            )
            
            # Create admin deletion task
            await db["admin_tasks"].insert_one({
                "type": "delete_article",
                "articleId": ObjectId(id),
                "articleTitle": article["title"],
                "requestedBy": deletion_request["requesterId"],
                "approvedBy": user["_id"],
                "createdAt": datetime.now(),
                "status": "pending"
            })
            
            message = "Deletion approved. Article marked for admin deletion."
        else:
            message = "Deletion request rejected. Article will remain published."
        
        return {"message": message, "decision": decision}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving deletion discussion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve discussion: {str(e)}"
        )
